"""Deterministic browser and cross-stack proof for US-125.

The proof starts the shipped E02 FastAPI router with an in-memory catalog,
starts ``frontend/`` in Next development mode with its real ``/api`` rewrite,
and drives the chatbot in Chromium.  It intentionally does not use the M1
advisor rig or ``frontend-mvp/``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
AGENT_PATH = "/api/v1/agent/respond"
MAX_PAYLOAD_BYTES = 256 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _fixture_products() -> list[Any]:
    """Build grounded records without touching a database or workbook."""

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from backend.app.agent.catalog.dataset_adapter import GenericProduct
    from backend.app.agent.catalog.promotions import PromotionInfo

    return [
        GenericProduct(
            productidweb="us125-web-alpha",
            category_code="38",
            category_name="Tủ Lạnh",
            brand="LG",
            brand_id="us125-brand-lg",
            model_code="US125-ALPHA",
            sku="SKU-US125-ALPHA",
            attributes={
                "productidweb": "us125-web-alpha",
                "category_code": "38",
                "brand": "LG",
                "Dung tích sử dụng": "300 lít",
                "Kiểu tủ": "Ngăn đá trên",
                "Công nghệ Inverter": "Có",
            },
            promotion=PromotionInfo(
                list_price=12_000_000,
                sale_price=8_000_000,
                gift="Tặng phiếu mua hàng US-125",
            ),
        ),
        GenericProduct(
            productidweb="us125-web-beta",
            category_code="38",
            category_name="Tủ Lạnh",
            brand="Samsung",
            brand_id="us125-brand-samsung",
            model_code="US125-BETA",
            sku="SKU-US125-BETA",
            attributes={
                "productidweb": "us125-web-beta",
                "category_code": "38",
                "brand": "Samsung",
                "Dung tích sử dụng": "500 lít",
                "Kiểu tủ": "Side by side",
            },
            promotion=PromotionInfo(
                list_price=10_000_000,
                sale_price=None,
                gift=None,
            ),
        ),
        GenericProduct(
            productidweb="us125-web-gamma",
            category_code="38",
            category_name="Tủ Lạnh",
            brand="Aqua",
            brand_id="us125-brand-aqua",
            model_code="US125-GAMMA",
            sku="SKU-US125-GAMMA",
            attributes={
                "productidweb": "us125-web-gamma",
                "category_code": "38",
                "brand": "Aqua",
                "Dung tích sử dụng": None,
                "Kiểu tủ": "Ngăn đá dưới",
            },
            promotion=PromotionInfo(
                list_price=11_000_000,
                sale_price=None,
                gift=None,
            ),
        ),
    ]


def _serve_backend(port: int) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import uvicorn

    from backend.app.agent.api import create_agent_app
    from backend.app.agent.graph import AgentDependencies

    app = create_agent_app(AgentDependencies(products=_fixture_products()))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _wait_for_http(
    url: str,
    process: subprocess.Popen[bytes],
    *,
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = "not ready"
    while time.monotonic() < deadline:
        return_code = process.poll()
        if return_code is not None:
            raise RuntimeError(f"process exited before {url} was ready ({return_code})")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if 200 <= response.status < 500:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = str(error)
        time.sleep(0.2)
    raise TimeoutError(f"timed out waiting for {url}: {last_error}")


def _stop_process_tree(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)


def _process_flags() -> tuple[int, bool]:
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        flags |= subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        return flags, False
    return 0, True


@dataclass
class ApiRecorder:
    agent_payloads: list[dict[str, Any]] = field(default_factory=list)
    api_paths: list[str] = field(default_factory=list)
    response_sizes: list[int] = field(default_factory=list)
    turn_durations_ms: list[int] = field(default_factory=list)

    def reset(self) -> None:
        self.agent_payloads.clear()
        self.api_paths.clear()
        self.response_sizes.clear()
        self.turn_durations_ms.clear()

    def observe_request(self, request: Any) -> None:
        path = urlsplit(request.url).path
        if not path.startswith("/api/"):
            return
        self.api_paths.append(path)
        if path != AGENT_PATH or request.method != "POST":
            return
        try:
            payload = request.post_data_json
        except (json.JSONDecodeError, TypeError):
            payload = None
        _require(isinstance(payload, dict), "agent request did not contain JSON")
        self.agent_payloads.append(payload)


def _send_turn(page: Any, recorder: ApiRecorder, message: str) -> dict[str, Any]:
    composer = page.locator('textarea[aria-label="Tin nhắn"]')
    before = len(recorder.agent_payloads)
    composer.fill(message)
    started = time.monotonic()
    with page.expect_response(
        lambda response: (
            urlsplit(response.url).path == AGENT_PATH
            and response.request.method == "POST"
        ),
        timeout=20_000,
    ) as response_info:
        composer.press("Enter")
    response = response_info.value
    elapsed_ms = int((time.monotonic() - started) * 1000)
    response_bytes = response.body()
    body = response.json()
    page.wait_for_timeout(50)

    _require(response.status == 200, f"agent returned HTTP {response.status}")
    _require(isinstance(body, dict), "agent response was not a JSON object")
    _require(
        len(recorder.agent_payloads) == before + 1,
        "a normal chatbot turn must issue exactly one agent request",
    )
    _require(
        len(response_bytes) <= MAX_PAYLOAD_BYTES,
        f"agent payload exceeded {MAX_PAYLOAD_BYTES} bytes",
    )
    recorder.response_sizes.append(len(response_bytes))
    recorder.turn_durations_ms.append(elapsed_ms)
    return body


def _open_chat(page: Any, *, mobile: bool) -> Any:
    from playwright.sync_api import expect

    launcher = page.locator('button[aria-label^="Mở Trợ lý AI"]')
    expect(launcher).to_be_visible(timeout=15_000)
    launcher.click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    _require(
        dialog.get_attribute("aria-modal") == ("true" if mobile else "false"),
        "chatbot modal semantics do not match the viewport",
    )
    expected_focus = "Đóng chatbot" if mobile else "Tin nhắn"
    page.wait_for_function(
        "label => document.activeElement?.getAttribute('aria-label') === label",
        expected_focus,
    )
    body_overflow = page.evaluate("document.body.style.overflow")
    _require(
        (body_overflow == "hidden") if mobile else (body_overflow != "hidden"),
        "chatbot body scroll locking does not match modal semantics",
    )
    box = dialog.bounding_box()
    _require(box is not None, "chatbot dialog has no layout box")
    viewport_width = page.evaluate("window.innerWidth")
    _require(
        box["x"] >= -1 and box["x"] + box["width"] <= viewport_width + 1,
        "chatbot dialog overflows the viewport horizontally",
    )
    if not mobile:
        _require(box["width"] < viewport_width, "desktop chatbot blocks the storefront")
        _require(
            page.locator("main").first.get_attribute("inert") is None,
            "desktop storefront was made inert",
        )
    return dialog


def _verify_recommendation(page: Any, body: dict[str, Any]) -> None:
    from playwright.sync_api import expect

    presentation = body.get("presentation")
    _require(isinstance(presentation, dict), "recommendation omitted presentation")
    _require(presentation.get("type") == "recommendation", "wrong discriminator")
    products = presentation.get("products")
    _require(isinstance(products, list) and len(products) == 3, "fixture products missing")
    _require(
        len({product["sku"] for product in products}) == len(products),
        "recommendation SKUs are not unique",
    )

    result = page.get_by_test_id("chat-recommendation-result")
    expect(result).to_be_visible(timeout=10_000)
    for product in products:
        card = result.get_by_test_id(f"chat-presentation-product-{product['sku']}")
        expect(card).to_have_count(1)
        expect(card.get_by_text(product["name"], exact=True)).to_be_visible()
        for badge in product["badges"]:
            expect(card.get_by_text(badge["label"], exact=True)).to_be_visible()

    alpha = next(product for product in products if product["sku"] == "SKU-US125-ALPHA")
    _require(len(alpha["badges"]) == 2, "server did not supply both alpha badges")
    _require(
        result.get_by_test_id("chat-presentation-product-SKU-US125-ALPHA").count()
        == 1,
        "a multi-badge product rendered more than once",
    )
    result_text = result.inner_text()
    for unavailable in (
        "Chưa có hình ảnh",
        "Chưa có liên kết sản phẩm",
        "Chưa có dữ liệu",
    ):
        _require(unavailable in result_text, f"missing-data label not visible: {unavailable}")


def _verify_comparison(page: Any, body: dict[str, Any]) -> Any:
    from playwright.sync_api import expect

    presentation = body.get("presentation")
    _require(isinstance(presentation, dict), "comparison omitted presentation")
    _require(presentation.get("type") == "comparison", "wrong comparison discriminator")
    products = presentation.get("products")
    rows = presentation.get("comparison_rows")
    _require(isinstance(products, list) and len(products) == 2, "comparison needs two products")
    _require(isinstance(rows, list) and rows, "comparison rows are missing")

    result = page.get_by_test_id("chat-comparison-result")
    expect(result).to_be_visible(timeout=10_000)
    for product in products:
        header = result.get_by_test_id(f"chat-presentation-product-{product['sku']}")
        expect(header).to_have_count(1)
        expect(header.get_by_text(product["name"], exact=True)).to_be_visible()

    rendered = result.inner_text()
    saw_explicit_null = False
    for row in rows:
        _require(row["label"] in rendered, f"comparison row missing: {row['label']}")
        for cell in row["values"]:
            if cell["value"] is None:
                saw_explicit_null = True
            else:
                _require(
                    cell["value"] in rendered,
                    f"server comparison value not visible for {cell['sku']}",
                )
    _require(saw_explicit_null, "fixture did not prove an honest null comparison cell")
    _require("Chưa có dữ liệu" in rendered, "null comparison cell was not disclosed")
    return result.get_by_test_id("chat-comparison-table-scroll")


def _assert_no_hydration_waterfall(recorder: ApiRecorder) -> None:
    unexpected = [path for path in recorder.api_paths if path != AGENT_PATH]
    _require(not unexpected, f"unexpected browser API hydration calls: {unexpected}")


def _save_screenshot(page: Any, artifacts: Path | None, name: str) -> None:
    if artifacts is None:
        return
    artifacts.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(artifacts / name), animations="disabled")


def _run_desktop(browser: Any, base_url: str, artifacts: Path | None) -> ApiRecorder:
    from playwright.sync_api import expect

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    recorder = ApiRecorder()
    page.on("request", recorder.observe_request)
    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=30_000)
        _open_chat(page, mobile=False)
        recorder.reset()

        clarification = _send_turn(page, recorder, "so sánh hai mẫu tủ lạnh")
        _require(
            clarification.get("presentation", {}).get("type") == "text",
            "first-turn comparison must stay text-only",
        )
        expect(page.get_by_test_id("chat-comparison-result")).to_have_count(0)
        expect(page.get_by_test_id("chat-recommendation-result")).to_have_count(0)

        page.get_by_role("button", name="Làm mới hội thoại").click()
        expect(page.get_by_test_id("chat-comparison-result")).to_have_count(0)
        recommendation = _send_turn(page, recorder, "mua tủ lạnh tầm 15 triệu")
        _verify_recommendation(page, recommendation)
        comparison = _send_turn(page, recorder, "so sánh hai mẫu")
        table_scroll = _verify_comparison(page, comparison)

        first_session = recommendation.get("session_id")
        _require(isinstance(first_session, str) and first_session, "session ID missing")
        _require(comparison.get("session_id") == first_session, "session did not round-trip")
        _require(recorder.agent_payloads[0].get("session_id") is None, "clarification leaked a session")
        _require(recorder.agent_payloads[1].get("session_id") is None, "reset did not start a new session")
        _require(
            recorder.agent_payloads[2].get("session_id") == first_session,
            "comparison request did not carry the recommendation session",
        )
        _require(len(recorder.agent_payloads) == 3, "desktop flow issued extra agent requests")
        _assert_no_hydration_waterfall(recorder)
        _save_screenshot(page, artifacts, "us125-desktop-comparison.png")

        table_scroll.focus()
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.wait_for_function(
            "() => document.activeElement?.getAttribute('aria-label')?.startsWith('Mở Trợ lý AI')",
        )
    finally:
        context.close()
    return recorder


def _run_mobile(
    browser: Any,
    base_url: str,
    artifacts: Path | None,
    *,
    width: int,
) -> ApiRecorder:
    from playwright.sync_api import expect

    context = browser.new_context(viewport={"width": width, "height": 760})
    page = context.new_page()
    recorder = ApiRecorder()
    page.on("request", recorder.observe_request)
    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=30_000)
        _open_chat(page, mobile=True)
        recorder.reset()

        recommendation = _send_turn(page, recorder, "mua tủ lạnh tầm 15 triệu")
        _verify_recommendation(page, recommendation)
        comparison = _send_turn(page, recorder, "so sánh hai mẫu")
        table_scroll = _verify_comparison(page, comparison)
        _require(
            comparison.get("session_id") == recommendation.get("session_id"),
            f"session did not round-trip at {width}px",
        )
        _require(
            recorder.agent_payloads[1].get("session_id") == recommendation.get("session_id"),
            f"comparison request omitted session at {width}px",
        )
        _require(len(recorder.agent_payloads) == 2, f"extra agent request at {width}px")
        _assert_no_hydration_waterfall(recorder)

        overflow = table_scroll.evaluate("node => node.scrollWidth > node.clientWidth")
        _require(overflow, f"comparison table is not horizontally scrollable at {width}px")
        viewport_overflow = page.evaluate(
            "document.documentElement.scrollWidth > window.innerWidth + 1",
        )
        _require(not viewport_overflow, f"page overflows horizontally at {width}px")
        _save_screenshot(page, artifacts, f"us125-mobile-{width}-comparison.png")

        table_scroll.focus()
        page.keyboard.press("Escape")
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.wait_for_function(
            "() => document.activeElement?.getAttribute('aria-label')?.startsWith('Mở Trợ lý AI')",
        )
        _require(
            page.evaluate("document.body.style.overflow") != "hidden",
            f"body scroll lock was not restored at {width}px",
        )
    finally:
        context.close()
    return recorder


def _tail(path: Path, lines: int = 30) -> str:
    if not path.exists():
        return "<no log>"
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])


def _run_browser_proof(artifacts: Path | None) -> None:
    from playwright.sync_api import sync_playwright

    backend_port = _free_port()
    frontend_port = _free_port()
    flags, start_new_session = _process_flags()
    backend_process: subprocess.Popen[bytes] | None = None
    frontend_process: subprocess.Popen[bytes] | None = None

    with tempfile.TemporaryDirectory(prefix="us125-ui-proof-") as temp:
        temp_path = Path(temp)
        backend_log = temp_path / "backend.log"
        frontend_log = temp_path / "frontend.log"
        backend_handle = backend_log.open("wb")
        frontend_handle = frontend_log.open("wb")
        try:
            backend_process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--serve-backend",
                    "--port",
                    str(backend_port),
                ],
                cwd=ROOT,
                stdout=backend_handle,
                stderr=subprocess.STDOUT,
                creationflags=flags,
                start_new_session=start_new_session,
            )
            _wait_for_http(
                f"http://127.0.0.1:{backend_port}/health",
                backend_process,
                timeout_seconds=30,
            )

            npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
            _require(npm is not None, "npm executable was not found")
            environment = os.environ.copy()
            environment.update(
                {
                    "BACKEND_ORIGIN": f"http://127.0.0.1:{backend_port}",
                    "NEXT_TELEMETRY_DISABLED": "1",
                }
            )
            frontend_process = subprocess.Popen(
                [
                    npm,
                    "run",
                    "dev",
                    "--",
                    "--hostname",
                    "127.0.0.1",
                    "--port",
                    str(frontend_port),
                ],
                cwd=FRONTEND,
                env=environment,
                stdout=frontend_handle,
                stderr=subprocess.STDOUT,
                creationflags=flags,
                start_new_session=start_new_session,
            )
            base_url = f"http://127.0.0.1:{frontend_port}/"
            _wait_for_http(base_url, frontend_process, timeout_seconds=90)

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    recorders = [
                        _run_desktop(browser, base_url, artifacts),
                        _run_mobile(browser, base_url, artifacts, width=320),
                        _run_mobile(browser, base_url, artifacts, width=400),
                    ]
                finally:
                    browser.close()

            sizes = [size for recorder in recorders for size in recorder.response_sizes]
            durations = [
                duration
                for recorder in recorders
                for duration in recorder.turn_durations_ms
            ]
            print(
                "US-125 browser proof PASS: "
                f"7 turns, max payload={max(sizes)} bytes, "
                f"max local response={max(durations)} ms, "
                "desktop + mobile 320/400, no hydration waterfall"
            )
        except Exception:
            _stop_process_tree(frontend_process)
            _stop_process_tree(backend_process)
            backend_handle.close()
            frontend_handle.close()
            print("--- backend log ---", file=sys.stderr)
            print(_tail(backend_log), file=sys.stderr)
            print("--- frontend log ---", file=sys.stderr)
            print(_tail(frontend_log), file=sys.stderr)
            raise
        finally:
            _stop_process_tree(frontend_process)
            _stop_process_tree(backend_process)
            if not backend_handle.closed:
                backend_handle.close()
            if not frontend_handle.closed:
                frontend_handle.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve-backend", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, help=argparse.SUPPRESS)
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        help="Optional directory for desktop and mobile screenshots.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.serve_backend:
        _require(args.port is not None, "--serve-backend requires --port")
        _serve_backend(args.port)
        return 0
    artifacts = args.artifacts_dir.resolve() if args.artifacts_dir else None
    _run_browser_proof(artifacts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
