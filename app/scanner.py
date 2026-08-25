import asyncio
from pathlib import Path

import httpx

# grabbing axe-core from cdnjs, caching locally so we don't hit the CDN every run
AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
_AXE_CACHE = Path(__file__).parent.parent / "static" / "axe.min.js"


def _fetch_axe_js() -> str:
    if _AXE_CACHE.exists():
        return _AXE_CACHE.read_text()
    _AXE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    r = httpx.get(AXE_CDN, timeout=30)
    r.raise_for_status()
    _AXE_CACHE.write_text(r.text)
    return r.text


async def _run(url: str, timeout_secs: int) -> dict:
    from playwright.async_api import async_playwright

    axe_js = _fetch_axe_js()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = await browser.new_page()
        try:
            # using "load" not "networkidle" — networkidle times out on sites
            # with polling/websockets (learned this the hard way)
            await page.goto(url, wait_until="load", timeout=timeout_secs * 1000)
            await page.wait_for_timeout(1500)
        except Exception as e:
            await browser.close()
            raise ValueError(f"Could not load page: {e}")

        await page.add_script_tag(content=axe_js)

        raw = await page.evaluate(
            """() => new Promise((resolve, reject) => {
                axe.run(document, { reporter: 'v2' }, (err, res) => {
                    if (err) reject(err.message);
                    else resolve(res);
                });
            })"""
        )
        await browser.close()

    violations = []
    for v in raw.get("violations", []):
        for node in v.get("nodes", []):
            violations.append({
                "rule_id": v["id"],
                "impact": v.get("impact", "minor"),
                "description": v["description"],
                "help_url": v.get("helpUrl", ""),
                "target": ", ".join(str(t) for t in node.get("target", [])),
                "html": node.get("html", ""),
                "wcag_tags": [t for t in v.get("tags", []) if t.startswith("wcag")],
            })

    return {
        "violations": violations,
        "passes_count": len(raw.get("passes", [])),
        "inapplicable_count": len(raw.get("inapplicable", [])),
    }


def scan_url(url: str, timeout_secs: int = 45) -> dict:
    return asyncio.run(_run(url, timeout_secs))
