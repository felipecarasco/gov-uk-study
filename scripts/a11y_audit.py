"""Accessibility audit of every page and error state of the running service.

Runs axe-core (WCAG 2.2 AA and best practices) on each page, checks that a
keyboard user can skip to the content, and fails on any browser console error,
which includes Content Security Policy violations and missing assets.

Needs the whole service running (make dev) and axe-core installed (make assets).
Run with: make a11y
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Point it elsewhere with A11Y_BASE_URL, for example when WEB_PORT is changed.
BASE = os.environ.get("A11Y_BASE_URL", "http://localhost:5000")
AXE = (Path(__file__).resolve().parent.parent / "web/node_modules/axe-core/axe.min.js").read_text()
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]

problems = []


def accepted(violation):
    # GOV.UK places the Back link before <main>, on purpose, so axe's
    # best-practice "region" rule flags it. That one case is accepted.
    return violation["id"] == "region" and all(
        ".govuk-back-link" in node["target"][0] for node in violation["nodes"]
    )


def audit(page, name):
    # Loaded through the automation channel, not as a <script> tag: the
    # service's Content Security Policy rightly blocks inline scripts without its
    # nonce, and switching the policy off would stop this audit from catching the
    # site's own violations.
    page.evaluate(AXE)
    result = page.evaluate("tags => axe.run({runOnly: {type: 'tag', values: tags}})", TAGS)
    for violation in result["violations"]:
        if not accepted(violation):
            targets = [node["target"][0] for node in violation["nodes"]][:3]
            problems.append(f"{name}: {violation['id']} ({violation['impact']}) {targets}")
    print(f"checked {name}")


def check_keyboard(page):
    page.goto(BASE)
    page.keyboard.press("Tab")
    if not page.evaluate("document.activeElement.classList.contains('govuk-skip-link')"):
        problems.append("keyboard: the first Tab does not reach the skip link")
    page.keyboard.press("Enter")
    if page.evaluate("document.activeElement.id") != "main-content":
        problems.append("keyboard: the skip link does not move focus to the main content")
    print("checked keyboard access")


def launch(p):
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()


with sync_playwright() as p:
    browser = launch(p)
    page = browser.new_page()
    # A resource that fails (a font, an image, a script) is a problem. The page
    # itself is not: some pages answer 404 on purpose.
    page.on(
        "response",
        lambda r: r.request.resource_type != "document"
        and r.status >= 400
        and problems.append(f"missing resource on {page.url}: {r.status} {r.url}"),
    )
    # Other console errors, including Content Security Policy violations. The
    # generic "Failed to load resource" message only repeats what the response
    # listener above already reports, so it is left out.
    page.on(
        "console",
        lambda msg: msg.type == "error"
        and not msg.text.startswith("Failed to load resource")
        and problems.append(f"console on {page.url}: {msg.text}"),
    )

    page.goto(BASE)
    audit(page, "start")
    page.goto(f"{BASE}/search")
    audit(page, "search choice")
    page.get_by_role("button", name="Continue").click()
    audit(page, "search choice (error)")
    page.goto(f"{BASE}/search/title-number")
    page.get_by_role("button", name="Continue").click()
    audit(page, "title number (error)")
    page.goto(f"{BASE}/search/postcode")
    page.get_by_role("button", name="Search").click()
    audit(page, "postcode (error)")
    page.get_by_label("Postcode").fill("SE1 7PB")
    page.get_by_role("button", name="Search").click()
    audit(page, "results")
    page.locator(".govuk-pagination__next a").click()
    audit(page, "results, last page")
    page.goto(f"{BASE}/search/results?postcode=ZZ99ZZ")
    audit(page, "no results")
    page.goto(f"{BASE}/search/titles/ZZ000000")
    audit(page, "title not found")
    page.goto(f"{BASE}/does-not-exist")
    audit(page, "page not found")
    for path, name in [("/accessibility", "accessibility"), ("/cookies", "cookies"), ("/privacy", "privacy")]:
        page.goto(BASE + path)
        audit(page, name)

    page.goto(f"{BASE}/search/titles/SGL123457")
    audit(page, "title detail")
    page.get_by_role("button", name="Order a copy").click()
    page.get_by_role("button", name="Continue").click()
    audit(page, "document type (error)")
    page.get_by_label("Title register").check()
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("button", name="Continue").click()
    audit(page, "your details (error)")
    page.get_by_label("Full name").fill("Audit Test")
    page.get_by_label("Email address").fill("audit@example.com")
    page.get_by_label("Address", exact=True).fill("1 Audit Street")
    page.get_by_role("button", name="Continue").click()
    audit(page, "check answers")
    page.get_by_role("button", name="Accept and continue to payment").click()
    audit(page, "payment")
    page.get_by_role("button", name="Pay £3.00").click()
    audit(page, "confirmation")

    check_keyboard(page)
    browser.close()

if problems:
    print("\n".join(["", "Accessibility problems:"] + problems))
    sys.exit(1)
print("\nNo accessibility problems found.")
