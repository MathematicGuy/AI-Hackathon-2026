import json
from pathlib import Path

import httpx
import pytest

from backend.app.catalog_images.representative import GroupSource
from backend.app.catalog_images.sources import source_for_group
from scripts.collect_representative_images import _parser, main, run_collection


LISTING_HTML = """
<ul class="listproduct">
  <li class="item" data-id="10">
    <a data-brand="Samsung"><div class="item-img">
      <img data-src="https://cdn.tgdd.vn/Products/Images/1/10/a.jpg">
    </div></a>
  </li>
</ul>
"""


def ready_mapping(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "mapping_version": 1,
                "generated_at": "2026-07-19T00:00:00+00:00",
                "groups": {
                    "38:2": {
                        "category_code": "38",
                        "brand_id": "2",
                        "brand": "Samsung",
                        "image_type": "representative",
                        "images": [
                            "https://cdn.tgdd.vn/Products/Images/1/seed.jpg"
                        ],
                        "source_url": "https://www.dienmayxanh.com/tu-lanh-samsung",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_cli_requires_one_explicit_mode():
    with pytest.raises(SystemExit):
        _parser().parse_args([])
    with pytest.raises(SystemExit):
        _parser().parse_args(["--pilot", "--all-groups"])


def test_source_urls_follow_current_first_party_category_patterns():
    assert source_for_group("72", None, "Apple").source_url == (
        "https://www.dienmayxanh.com/may-tinh-nguyen-bo-apple"
    )
    assert source_for_group("137", "233", "Boya").source_url == (
        "https://www.dienmayxanh.com/micro-thu-am-boya"
    )
    assert source_for_group("139", "447", "Zenbos").source_url == (
        "https://www.dienmayxanh.com/micro-zenbos"
    )


def test_pilot_rejects_unsafe_rate_limit(tmp_path):
    with pytest.raises(SystemExit):
        main(
            [
                "--pilot",
                "--output-dir",
                str(tmp_path),
                "--rate-limit-seconds",
                "0.5",
            ]
        )


def test_collection_preserves_ready_groups_and_resume_uses_checkpoint(tmp_path):
    mapping_path = tmp_path / "runtime.json"
    output_dir = tmp_path / "operation"
    ready_mapping(mapping_path)
    sources = (
        GroupSource(
            "38", "2", "Samsung", "https://www.dienmayxanh.com/tu-lanh-samsung"
        ),
        GroupSource(
            "36", "2", "Samsung", "https://www.dienmayxanh.com/may-lanh-samsung"
        ),
    )
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        return httpx.Response(200, text=LISTING_HTML, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = run_collection(
            sources=sources,
            mode="all-groups",
            output_dir=output_dir,
            production_mapping_path=mapping_path,
            mapping_version=1,
            resume=False,
            force=False,
            timeout_seconds=1,
            rate_limit_seconds=1,
            client=client,
            sleep=lambda _: None,
        )
    assert result == 0
    assert requests == ["https://www.dienmayxanh.com/may-lanh-samsung"]
    deployed = json.loads(mapping_path.read_text(encoding="utf-8"))
    assert set(deployed["groups"]) == {"38:2", "36:2"}
    assert deployed["groups"]["38:2"]["images"] == [
        "https://cdn.tgdd.vn/Products/Images/1/seed.jpg"
    ]

    def unexpected(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"resume fetched ready group: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(unexpected)) as client:
        assert (
            run_collection(
                sources=sources,
                mode="all-groups",
                output_dir=output_dir,
                production_mapping_path=mapping_path,
                mapping_version=1,
                resume=True,
                force=False,
                timeout_seconds=1,
                rate_limit_seconds=1,
                client=client,
                sleep=lambda _: None,
            )
            == 0
        )


def test_existing_checkpoint_requires_resume_or_force(tmp_path):
    output_dir = tmp_path / "operation"
    output_dir.mkdir()
    (output_dir / "checkpoint.json").write_text(
        '{"groups": {}}', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="--resume or --force"):
        run_collection(
            sources=(),
            mode="all-groups",
            output_dir=output_dir,
            production_mapping_path=None,
            mapping_version=1,
            resume=False,
            force=False,
            timeout_seconds=1,
            rate_limit_seconds=1,
        )


def test_interruption_keeps_production_mapping_unchanged(tmp_path):
    mapping_path = tmp_path / "runtime.json"
    output_dir = tmp_path / "operation"
    ready_mapping(mapping_path)
    original = mapping_path.read_bytes()
    sources = (
        GroupSource(
            "36", "2", "Samsung", "https://www.dienmayxanh.com/may-lanh-samsung"
        ),
        GroupSource(
            "73", "2", "Samsung", "https://www.dienmayxanh.com/man-hinh-samsung"
        ),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if "man-hinh" in request.url.path:
            raise KeyboardInterrupt
        return httpx.Response(200, text=LISTING_HTML, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(KeyboardInterrupt):
            run_collection(
                sources=sources,
                mode="all-groups",
                output_dir=output_dir,
                production_mapping_path=mapping_path,
                mapping_version=1,
                resume=False,
                force=False,
                timeout_seconds=1,
                rate_limit_seconds=1,
                client=client,
                sleep=lambda _: None,
            )
    assert mapping_path.read_bytes() == original
    checkpoint = json.loads((output_dir / "checkpoint.json").read_text())
    assert checkpoint["groups"]["36:2"]["status"] == "ready"
