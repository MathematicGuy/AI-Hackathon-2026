#!/usr/bin/env python
"""Collect representative category-brand images with explicit safety gates."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import pathlib
import sys
import time
from collections.abc import Callable, Iterable
from contextlib import nullcontext
from dataclasses import replace
from datetime import datetime, timezone

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from backend.app.agent.catalog.dataset_adapter import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    ExcelDatasetAdapter,
)
from backend.app.catalog_images import (  # noqa: E402
    PILOT_GROUPS,
    GroupSource,
    RepresentativeImageMapping,
    catalog_group_sources,
    collect_group,
)
from backend.app.catalog_images.mapping import DEFAULT_MAPPING_PATH  # noqa: E402

logger = logging.getLogger(__name__)

PILOT_OUTPUT_DIR = pathlib.Path("data/processed/representative-images/pilot-5")
ALL_GROUPS_OUTPUT_DIR = pathlib.Path(
    "data/processed/representative-images/all-groups-v1"
)


def _atomic_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _image_url(image: str | dict) -> str:
    return image if isinstance(image, str) else image["url"]


def _write_review_csv(path: pathlib.Path, groups: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "group_key",
                "category_code",
                "brand_id",
                "brand",
                "image_type",
                "status",
                "image_count",
                "image_position",
                "image_url",
                "source_url",
                "attempted_source_urls",
                "failure_reason",
            ),
        )
        writer.writeheader()
        for group in groups:
            images = group["images"] or [None]
            for position, image in enumerate(images):
                writer.writerow(
                    {
                        "group_key": group["group_key"],
                        "category_code": group["category_code"],
                        "brand_id": group["brand_id"],
                        "brand": group["brand"],
                        "image_type": group["image_type"],
                        "status": group["status"],
                        "image_count": len(group["images"]),
                        "image_position": (
                            image.get("position", position)
                            if isinstance(image, dict)
                            else position if image else ""
                        ),
                        "image_url": _image_url(image) if image else "",
                        "source_url": group.get("source_url") or "",
                        "attempted_source_urls": " | ".join(
                            group.get("attempted_source_urls") or []
                        ),
                        "failure_reason": group.get("failure_reason") or "",
                    }
                )
    temporary.replace(path)


def _load_checkpoint(path: pathlib.Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_groups = payload.get("groups", {})
    if isinstance(raw_groups, list):
        return {group["group_key"]: group for group in raw_groups}
    if isinstance(raw_groups, dict):
        return dict(raw_groups)
    raise ValueError(f"invalid checkpoint groups in {path}")


def _ready_result_from_mapping(key: str, group: dict, version: int) -> dict:
    return {
        "group_key": key,
        "category_code": group["category_code"],
        "brand_id": group["brand_id"],
        "brand": group["brand"],
        "image_type": "representative",
        "source_url": group["source_url"],
        "status": "ready",
        "failure_reason": None,
        "images": list(group["images"]),
        "mapping_version": version,
    }


def _load_production_ready(
    path: pathlib.Path, *, mapping_version: int, force: bool
) -> dict[str, dict]:
    if not path.exists() or force:
        return {}
    mapping = RepresentativeImageMapping.load(path)
    if mapping.mapping_version != mapping_version:
        raise ValueError(
            "existing production mapping has a different version; "
            "use the matching --mapping-version or explicit --force"
        )
    return {
        key: _ready_result_from_mapping(key, group, mapping.mapping_version)
        for key, group in mapping.groups.items()
    }


def _checkpoint_payload(
    *, mode: str, mapping_version: int, generated_at: str, groups: list[dict]
) -> dict:
    return {
        "checkpoint_version": 1,
        "mode": mode,
        "mapping_version": mapping_version,
        "generated_at": generated_at,
        "groups": {group["group_key"]: group for group in groups},
    }


def _production_payload(
    groups: Iterable[dict], *, mapping_version: int, generated_at: str
) -> dict:
    ready: dict[str, dict] = {}
    for result in groups:
        if result.get("status") != "ready":
            continue
        ready[result["group_key"]] = {
            "category_code": result["category_code"],
            "brand_id": result["brand_id"],
            "brand": result["brand"],
            "image_type": "representative",
            "images": [_image_url(image) for image in result["images"][:3]],
            "source_url": result["source_url"],
        }
    return {
        "mapping_version": mapping_version,
        "generated_at": generated_at,
        "groups": ready,
    }


def _ordered_results(
    sources: tuple[GroupSource, ...], results: dict[str, dict]
) -> list[dict]:
    ordered = [results[source.key] for source in sources if source.key in results]
    source_keys = {source.key for source in sources}
    ordered.extend(results[key] for key in sorted(results) if key not in source_keys)
    return ordered


def _summary(groups: list[dict], *, mapping_path: pathlib.Path | None) -> dict:
    return {
        "total_groups": len(groups),
        "ready": sum(group["status"] == "ready" for group in groups),
        "not_found": sum(group["status"] == "not_found" for group in groups),
        "skipped": sum(group["status"] == "skipped" for group in groups),
        "error": sum(group["status"] == "error" for group in groups),
        "total_images": sum(len(group["images"]) for group in groups),
        "mapping_path": str(mapping_path) if mapping_path else None,
    }


def run_collection(
    *,
    sources: tuple[GroupSource, ...],
    mode: str,
    output_dir: pathlib.Path,
    production_mapping_path: pathlib.Path | None,
    mapping_version: int,
    resume: bool,
    force: bool,
    timeout_seconds: float,
    rate_limit_seconds: float,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    checkpoint_path = output_dir / (
        "mapping.json" if mode == "pilot" else "checkpoint.json"
    )
    review_path = output_dir / "review.csv"
    summary_path = output_dir / "summary.json"
    if checkpoint_path.exists() and not resume and not force:
        raise ValueError(
            f"checkpoint already exists at {checkpoint_path}; use --resume or --force"
        )

    results = (
        _load_production_ready(
            production_mapping_path,
            mapping_version=mapping_version,
            force=force,
        )
        if production_mapping_path
        else {}
    )
    if resume and not force:
        for key, result in _load_checkpoint(checkpoint_path).items():
            if results.get(key, {}).get("status") != "ready":
                results[key] = result
    if force:
        results = {}

    generated_at = datetime.now(timezone.utc).isoformat()
    headers = {
        "User-Agent": (
            "XanhProduct-representative-images/1.0 "
            "(+rate-limited first-party category-brand mapping)"
        )
    }
    timeout = httpx.Timeout(timeout_seconds, connect=min(10.0, timeout_seconds))
    context = (
        nullcontext(client)
        if client is not None
        else httpx.Client(headers=headers, timeout=timeout, follow_redirects=True)
    )
    with context as active_client:
        assert active_client is not None
        for index, source in enumerate(sources):
            existing = results.get(source.key)
            fetched = False
            if existing is not None and existing.get("status") == "ready" and not force:
                result = existing
                logger.info(
                    "group=%s status=cache_hit images=%d",
                    source.key,
                    len(result["images"]),
                )
            else:
                collection_source = source
                if resume and existing is not None and source.fallback_url:
                    collection_source = replace(
                        source,
                        source_url=source.fallback_url,
                        fallback_url=None,
                    )
                result = collect_group(collection_source, active_client)
                fetched = collection_source.source_url is not None
                logger.info(
                    "group=%s status=%s images=%d",
                    source.key,
                    result["status"],
                    len(result["images"]),
                )
            result["mapping_version"] = mapping_version
            results[source.key] = result
            groups = _ordered_results(sources, results)
            _atomic_json(
                checkpoint_path,
                _checkpoint_payload(
                    mode=mode,
                    mapping_version=mapping_version,
                    generated_at=generated_at,
                    groups=groups,
                ),
            )
            _write_review_csv(review_path, groups)
            if fetched and index + 1 < len(sources):
                sleep(rate_limit_seconds)

    groups = _ordered_results(sources, results)
    if production_mapping_path is not None:
        payload = _production_payload(
            groups,
            mapping_version=mapping_version,
            generated_at=generated_at,
        )
        # Checkpoints retain partial progress; deploy only a completed pass.
        RepresentativeImageMapping.from_payload(payload)
        _atomic_json(production_mapping_path, payload)
    summary = _summary(groups, mapping_path=production_mapping_path or checkpoint_path)
    summary["checkpoint_path"] = str(checkpoint_path)
    summary["review_path"] = str(review_path)
    _atomic_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if summary["error"] else 0


def run_pilot(
    *,
    limit_groups: int,
    output_dir: pathlib.Path,
    resume: bool,
    force: bool = False,
    timeout_seconds: float,
    rate_limit_seconds: float,
) -> int:
    if not 1 <= limit_groups <= 5:
        raise ValueError("pilot limit_groups must be between 1 and 5")
    return run_collection(
        sources=PILOT_GROUPS[:limit_groups],
        mode="pilot",
        output_dir=output_dir,
        production_mapping_path=None,
        mapping_version=1,
        resume=resume,
        force=force,
        timeout_seconds=timeout_seconds,
        rate_limit_seconds=rate_limit_seconds,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect representative images by category-brand group."
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--pilot", action="store_true", help="run at most five groups")
    modes.add_argument(
        "--all-groups",
        action="store_true",
        help="explicitly process every category-brand group",
    )
    parser.add_argument("--limit-groups", type=int)
    parser.add_argument("--output-dir", type=pathlib.Path)
    parser.add_argument("--catalog-path", type=pathlib.Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--mapping-path", type=pathlib.Path, default=DEFAULT_MAPPING_PATH
    )
    parser.add_argument("--mapping-version", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=25.0)
    parser.add_argument("--rate-limit-seconds", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.mapping_version < 1:
        parser.error("--mapping-version must be positive")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.pilot:
        limit = args.limit_groups or 5
        if not 1 <= limit <= 5:
            parser.error("--pilot requires --limit-groups between 1 and 5")
        rate_limit = (
            args.rate_limit_seconds if args.rate_limit_seconds is not None else 1.0
        )
        if rate_limit < 1.0:
            parser.error("--pilot requires --rate-limit-seconds >= 1.0")
        return run_pilot(
            limit_groups=limit,
            output_dir=args.output_dir or PILOT_OUTPUT_DIR,
            resume=args.resume,
            force=args.force,
            timeout_seconds=args.timeout_seconds,
            rate_limit_seconds=rate_limit,
        )

    if args.limit_groups is not None:
        parser.error("--limit-groups is only valid with --pilot")
    rate_limit = (
        args.rate_limit_seconds if args.rate_limit_seconds is not None else 1.5
    )
    if rate_limit < 1.0:
        parser.error("--all-groups requires --rate-limit-seconds >= 1.0")
    products = ExcelDatasetAdapter(args.catalog_path).load()
    sources = catalog_group_sources(products)
    return run_collection(
        sources=sources,
        mode="all-groups",
        output_dir=args.output_dir or ALL_GROUPS_OUTPUT_DIR,
        production_mapping_path=args.mapping_path,
        mapping_version=args.mapping_version,
        resume=args.resume,
        force=args.force,
        timeout_seconds=args.timeout_seconds,
        rate_limit_seconds=rate_limit,
    )


if __name__ == "__main__":
    raise SystemExit(main())
