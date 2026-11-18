"""Reproduce the offline asset and Chromium checks. Requires Pillow and Playwright."""
import hashlib
import json
import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
EVIDENCE = ROOT / "evidence"
manifest = json.loads((ASSETS / "manifest.json").read_text())
url = os.getenv("STUDIO_TEST_URL") or (ROOT / "index.html").as_uri()
from_disk = url.startswith("file:")


def verify_assets():
    expected = {"idle": (6, 960), "run": (8, 640), "jump": (11, 1360), "attack": (9, 1200)}
    for action, clip in manifest["clips"].items():
        count, milliseconds = expected[action]
        sheet = Image.open(ASSETS / clip["sheet"])
        assert sheet.size == (96 * count, 96) and sheet.mode == "RGBA"
        assert len(clip["frames"]) == count
        assert sum(frame["hold"] for frame in clip["frames"]) * manifest["tickMs"] == milliseconds
        digests = set()
        for index, frame in enumerate(clip["frames"]):
            x, y, w, h = frame["rect"]
            assert (x, y, w, h) == (96 * index, 0, 96, 96)
            png = Image.open(ASSETS / frame["file"])
            assert png.mode == "RGBA" and png.size == (96, 96)
            assert sheet.crop((x, y, x + w, y + h)).tobytes() == png.tobytes()
            assert set(png.getchannel("A").get_flattened_data()) == {0, 255}
            left, top, right, bottom = frame["bounds"]
            assert (left, top, right, bottom) == png.getbbox()
            assert 1 <= left < right < 95 and 1 <= top < bottom <= 78
            assert frame["anchor"] == {"x": 44, "y": 78}
            for contact in frame["contacts"]:
                assert contact["y"] == 78
                assert png.getpixel((contact["x"], 77))[3] == 255
            digests.add(hashlib.sha256(png.tobytes()).digest())
        assert len(digests) == count
    assert [f["contacts"] for f in manifest["clips"]["idle"]["frames"]].count(
        manifest["clips"]["idle"]["frames"][0]["contacts"]) == 6
    assert manifest["clips"]["jump"]["frames"][5]["bounds"][3] <= 57
    print("PASS assets: 34 distinct per-clip poses, four timings, alpha, dimensions, crops, bounds, anchors and contacts.")


def verify_browser():
    with sync_playwright() as p:
        if from_disk:
            browser = p.firefox.launch()
        else:
            assert url.startswith("http://127.0.0.1:")
            browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        print(f"{browser.browser_type.name} {browser.version} ({'offline file' if from_disk else 'loopback preview'})")

        def new_context(**options):
            context = browser.new_context(offline=from_disk, **options)
            if not from_disk:
                context.route("**/*", lambda route: route.continue_() if route.request.url == url else route.abort())
            return context

        context = new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        errors, network, failures = [], [], []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("request", lambda request: network.append(request.url) if request.url.startswith(("http:", "https:")) and request.url != url else None)
        page.on("requestfailed", lambda request: failures.append(request.url))
        page.clock.install()
        page.goto(url)
        page.wait_for_function("document.querySelector('#primary-meta').textContent !== ''")
        assert page.locator('[data-action=idle]').get_attribute("aria-pressed") == "true"
        assert page.locator("#primary").evaluate("c => c.width === 192 && !c.getContext('2d').imageSmoothingEnabled")
        page.clock.run_for(300)
        assert float(page.locator("#seek").input_value()) > 250
        page.locator("#play").click()
        stopped = page.locator("#seek").input_value()
        page.clock.run_for(200)
        assert page.locator("#seek").input_value() == stopped
        page.locator('[data-action=idle]').click()
        if from_disk:
            page.screenshot(path=EVIDENCE / "desktop.png")
        print("PASS standalone viewer launch, visible Idle, autoplay, pause, integer canvas and smoothing.")

        def seek_to(ms):
            page.locator("#seek").evaluate("(node, ms) => { node.value = ms; node.dispatchEvent(new Event('input')); }", ms)

        def bitmap(canvas="#primary"):
            return page.locator(canvas).evaluate("c => c.toDataURL()")

        bitmaps = []
        for action, ms, frame in [("idle", 480, 3), ("run", 160, 3), ("jump", 560, 6), ("attack", 480, 5)]:
            button = page.locator(f"[data-action={action}]")
            button.click()
            assert button.get_attribute("aria-pressed") == "true"
            assert page.locator("#primary-name").text_content() == action.title()
            seek_to(ms)
            assert page.locator("#frame").text_content().startswith(f"FRAME {frame:02}")
            assert page.locator("#loop").is_checked() == manifest["clips"][action]["loop"]
            bitmaps.append(bitmap())
        assert len(set(bitmaps)) == 4
        page.keyboard.press("ArrowRight")
        assert page.locator("#frame").text_content().startswith("FRAME 06")
        page.keyboard.press("ArrowLeft")
        assert page.locator("#frame").text_content().startswith("FRAME 05")
        page.locator("#prev").click()
        assert page.locator("#frame").text_content().startswith("FRAME 04")
        page.locator("#next").click()
        assert page.locator("#frame").text_content().startswith("FRAME 05")
        page.keyboard.press("ArrowRight")
        assert page.locator("#frame").text_content().startswith("FRAME 06")
        page.locator("#seek").focus()
        page.keyboard.press("ArrowLeft")
        assert page.locator("#frame").text_content().startswith("FRAME 05")
        page.locator("h1").click()
        page.keyboard.press("Space")
        assert page.locator("#play").text_content() == "Pause"
        page.keyboard.press("Space")
        assert page.locator("#play").text_content() == "Play"
        print("PASS four distinct Canvas renders, action labels, seek, frame count, buttons and keyboard shortcuts.")

        for rate in [".25", ".5", "1", "1.5", "2"]:
            seek_to(0)
            page.locator("#speed").select_option(rate)
            page.locator("#play").click()
            page.clock.run_for(208)
            elapsed = float(page.locator("#seek").input_value())
            assert abs(elapsed - 208 * float(rate)) <= 38, (rate, elapsed)
            page.locator("#play").click()
        page.locator("#speed").select_option("1")
        seek_to(1180)
        page.locator("#play").click()
        page.clock.run_for(95)
        assert page.locator("#play").text_content() == "Play"
        assert page.locator("#seek").input_value() == "1200"
        page.locator("#loop").check()
        seek_to(1180)
        page.locator("#play").click()
        page.clock.run_for(95)
        assert 35 <= float(page.locator("#seek").input_value()) <= 125
        page.locator("#play").click()
        print("PASS all five speed rates, one-shot end and explicit loop wrap.")

        for scale in (1, 2, 4):
            page.locator("#zoom").select_option(str(scale))
            assert page.locator("#primary").evaluate("c => c.width") == scale * 96
        page.locator("#zoom").select_option("2")
        for backdrop in ["light", "checker", "dark"]:
            page.locator("#background").select_option(backdrop)
            assert page.locator(".stage").first.get_attribute("data-bg") == backdrop
        before = bitmap()
        page.locator("#guide").check()
        assert bitmap() != before
        page.locator("#compare").check()
        page.locator("#secondary-action").select_option("run")
        seek_to(480)
        assert page.locator("#secondary-meta").text_content() == "07 / 8"
        if from_disk:
            page.screenshot(path=EVIDENCE / "desktop-comparison.png")
        seek_to(650)
        shorter = bitmap("#secondary")
        seek_to(980)
        assert bitmap("#secondary") == shorter
        assert page.locator("#secondary-meta").text_content() == "08 / 8 · Hold"
        assert page.locator("#primary-meta").text_content() == "09 / 9"
        assert page.locator("#seek").get_attribute("max") == "1200"
        page.locator("#compare").uncheck()
        assert page.locator("#secondary-pane").is_hidden()
        assert not page.locator("#loop").is_checked()
        assert not errors and not failures and not network, (errors, failures, network)
        print("PASS zoom, all backdrops, ground, shared time, shorter clip final-pose hold and compare exit. Zero errors, failed requests or HTTP(S) requests.")

        mobile = new_context(viewport={"width": 360, "height": 800},
                                     has_touch=True, reduced_motion="reduce")
        narrow = mobile.new_page()
        narrow.goto(url)
        narrow.wait_for_function("document.querySelector('#primary-meta').textContent !== ''")
        assert narrow.locator("#play").text_content() == "Play"
        narrow.keyboard.press("Tab")
        assert narrow.locator(":focus-visible").count() == 1
        if from_disk:
            narrow.screenshot(path=EVIDENCE / "mobile.png", full_page=True)
        narrow.locator("#compare").check()
        narrow.locator("#zoom").select_option("4")
        assert narrow.evaluate("document.documentElement.scrollWidth === innerWidth")
        assert narrow.locator("#secondary").evaluate("c => c.width") == 384
        for stage in narrow.locator(".stage").all():
            assert stage.evaluate("s => s.scrollWidth >= 384 && s.clientWidth < 384")
            stage.focus()
            stage.evaluate("s => s.scrollLeft = 0")
            narrow.keyboard.press("ArrowRight")
            narrow.wait_for_function("document.activeElement.scrollLeft > 0")
            assert narrow.locator("#frame").text_content().startswith("FRAME 01")
        assert page.evaluate("document.documentElement.scrollWidth === innerWidth")
        print("PASS reduced motion, visible keyboard focus, narrow comparison and keyboard scrolling of both 4× canvases without page overflow.")

        if not from_disk:
            browser.close()
            return

        # Record the actual viewer and its action changes in the browser.
        recording = new_context(viewport={"width": 1040, "height": 790},
                                        record_video_dir=EVIDENCE / "video-temp")
        recorded = recording.new_page()
        recorded.goto(url)
        recorded.wait_for_function("document.querySelector('#primary-meta').textContent !== ''")
        recorded.wait_for_timeout(1000)
        for action in ("run", "jump", "attack"):
            recorded.locator(f"[data-action={action}]").click()
            recorded.wait_for_timeout(1500)
            if action == "jump":
                recorded.locator("#play").click()
        video = recorded.video
        recording.close()
        video.save_as(EVIDENCE / "viewer-walkthrough.webm")
        video.delete()
        (EVIDENCE / "video-temp").rmdir()
        browser.close()
        print("PASS browser walkthrough recorded from the actual offline viewer.")


if __name__ == "__main__":
    verify_assets()
    verify_browser()
