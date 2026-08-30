import asyncio
from playwright.async_api import async_playwright
import time
import os


async def main():
    print("Ensure the Streamlit Dashboard is running on http://localhost:8501")
    print("Ensure the KMS is running on http://localhost:8000")
    print("Ensure Attacker Console is running")
    print("Waiting 5 seconds before capturing...")
    time.sleep(5)

    os.makedirs("screenshots", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        # 1. Dashboard - Secure State (L1/GREEN)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("http://localhost:8501")
        await page.wait_for_timeout(3000)  # wait for load
        await page.screenshot(path="screenshots/dashboard.jpg", type="jpeg", quality=90)
        print("✅ Saved screenshots/dashboard.jpg")

        # 2. Attack Triggered (RED)
        # Click "Eve ON" and "Trigger Attack"
        # We assume the buttons exist and we can click them
        try:
            await page.get_by_role("button", name="Eve ON").click()
            await page.wait_for_timeout(1000)
            await page.get_by_role("button", name="Trigger Attack").click()
            await page.wait_for_timeout(2000)
            await page.screenshot(
                path="screenshots/attack_active.jpg", type="jpeg", quality=90
            )
            print("✅ Saved screenshots/attack_active.jpg")
        except Exception as e:
            print(
                "Could not trigger attack automatically. Please do it manually next time:",
                e,
            )

        # 3. Attacker Console
        print(
            "Note: To screenshot the Attacker Console (CLI), please use your OS screenshot tool (e.g., Win+Shift+S) and save it as screenshots/attacker_cli.jpg"
        )

        # 4. QBER History Chart
        # Already visible in the dashboard screenshots, but you can scroll to it
        await page.evaluate("window.scrollTo(0, 500)")
        await page.wait_for_timeout(1000)
        await page.screenshot(
            path="screenshots/qber_chart.jpg", type="jpeg", quality=90
        )
        print("✅ Saved screenshots/qber_chart.jpg")

        # 5. Banking App Transfer Blocked
        page2 = await browser.new_page(viewport={"width": 1024, "height": 768})
        await page2.goto("http://localhost:8000/app")
        await page2.wait_for_timeout(2000)
        await page2.screenshot(
            path="screenshots/bank_transfer_blocked.jpg", type="jpeg", quality=90
        )
        print("✅ Saved screenshots/bank_transfer_blocked.jpg")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
