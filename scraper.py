import os
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tracker.log"),
        logging.StreamHandler()
    ]
)

load_dotenv()

UCI = os.getenv("UCI")
APP_NUMBER = os.getenv("APP_NUMBER")
PASSWORD = os.getenv("PASSWORD")
STATUS_FILE = "status.json"

async def get_current_status():
    async with async_playwright() as p:
        # Try Firefox to see if it bypasses the IP-based block better than Chromium
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            logging.info("Navigating to IRCC tracker login page...")
            await page.goto("https://tracker-suivi.apps.cic.gc.ca/en/login", wait_until="networkidle", timeout=60000)

            # Debug: Capture state before entering credentials
            await page.screenshot(path="before_login.png")
            titles = await page.locator("h1, h2").all_inner_texts()
            logging.info(f"Page titles: {titles}")

            # Wait for the app to bootstrap
            logging.info("Waiting for app to bootstrap...")
            # UCI input might have different labels or IDs depending on state
            uci_selector = 'input[name="uci"]'
            await page.wait_for_selector(uci_selector, state="visible", timeout=60000)
            
            logging.info("Entering credentials...")
            # Use fill but with small sleeps between to ensure SPA stability
            await page.locator('input[name="uci"]').first.fill(UCI)
            await asyncio.sleep(1)
            
            # Application number is often required.
            app_num_selector = 'input[name="applicationNumber"]'
            if await page.locator(app_num_selector).count() > 0:
                if APP_NUMBER:
                    await page.locator(app_num_selector).fill(APP_NUMBER)
                    await asyncio.sleep(1)
                    logging.info("Filled Application Number.")
                else:
                    logging.warning("Application Number field found but no APP_NUMBER provided!")

            # Password field
            await page.locator('input[name="password"]').first.fill(PASSWORD)
            await asyncio.sleep(1)

            logging.info("Clicking Sign In...")
            # Target the actual submit button specifically
            sign_in_button = page.locator('button[type="submit"], .btn-primary, button:has-text("Sign in")').first
            await sign_in_button.wait_for(state="visible", timeout=30000)
            await sign_in_button.click()

            # Wait for the dashboard to load or an error to appear
            logging.info("Waiting for dashboard to load (this can take up to 90s)...")
            
            try:
                # 1. Wait for URL change or error
                for _ in range(18): # 90 seconds total (5s chunks)
                    if "dashboard" in page.url:
                        logging.info(f"URL changed to: {page.url}")
                        break
                    
                    # Check for visible error messages
                    errors = await page.locator(".alert-danger, .error-message, .invalid-feedback").all_inner_texts()
                    if any(e.strip() for e in errors):
                        logging.error(f"Login failed with error on page: {[e.strip() for e in errors if e.strip()]}")
                        await page.screenshot(path="login_error_on_page.png")
                        return None
                        
                    await asyncio.sleep(5)
                
                if "dashboard" not in page.url:
                    raise Exception(f"Timed out waiting for dashboard. Current URL: {page.url}")
                
                # 2. Wait for a key element to appear in the DOM (even if not perfectly visible)
                # We'll use a loop to check for several possible indicators
                found = False
                for _ in range(12): # 60 seconds total
                    if await page.get_by_text("Your citizenship application status", exact=False).count() > 0:
                        found = True
                        break
                    
                    # Check for errors using valid selectors
                    has_alert = await page.locator(".alert-danger").count() > 0
                    has_invalid = await page.get_by_text("Invalid", exact=False).count() > 0
                    has_error = await page.get_by_text("error", exact=False).count() > 0
                    
                    if has_alert or has_invalid or has_error:
                        logging.error("Login failed or error detected on dashboard.")
                        await page.screenshot(path="login_error.png")
                        return None
                    await asyncio.sleep(5)
                
                if not found:
                    raise Exception("Dashboard elements not found after URL change.")

                # Debug: Save HTML for inspection
                with open("dashboard_debug.html", "w") as f:
                    f.write(await page.content())
                
                logging.info("Dashboard detected successfully.")
                # Scroll to bottom to ensure all elements (activity log, etc.) are loaded
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2) # Wait for any lazy loading
            except Exception as e:
                logging.error(f"Timed out or failed waiting for dashboard. Current URL: {page.url}")
                await page.screenshot(path="timeout_state.png")
                raise

            # Extract Status
            data = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "",
                "sections": {},
                "activity": []
            }

            # Overall Status - usually near "Your citizenship application status: "
            try:
                status_text = await page.locator("text=/Your citizenship application status:/i").inner_text()
                data["overall_status"] = status_text.replace("Your citizenship application status:", "").strip()
            except:
                data["overall_status"] = "Unknown"

            # Last updated - near "Updated:"
            try:
                last_updated = await page.locator("text=/Updated:/i").locator("xpath=following-sibling::*").first.inner_text()
                data["last_updated"] = last_updated.strip()
            except:
                # Fallback to general search
                try:
                    last_updated = await page.locator(".date-text, .updated-date").first.inner_text()
                    data["last_updated"] = last_updated.strip()
                except:
                    data["last_updated"] = "Unknown"

            # Section statuses
            section_names = [
                "Background verification", 
                "Citizenship test", 
                "Physical presence", 
                "Language skills", 
                "Prohibitions", 
                "Citizenship ceremony"
            ]
            for name in section_names:
                try:
                    # Target the h3 title exactly
                    section_title = page.locator(f"h3:has-text('{name}')")
                    if await section_title.count() > 0:
                        # Find the summary container
                        summary = section_title.locator("xpath=ancestor::summary").first
                        if await summary.count() > 0:
                            # Look for the chip text specifically
                            chip_text_el = summary.locator(".chip-text")
                            if await chip_text_el.count() > 0:
                                status = await chip_text_el.first.inner_text()
                                data["sections"][name] = status.strip()
                            else:
                                # Fallback to chip classes
                                if await summary.locator(".completed-chip").count() > 0:
                                    data["sections"][name] = "Completed"
                                elif await summary.locator(".notStarted-chip").count() > 0:
                                    data["sections"][name] = "Not started"
                                elif await summary.locator(".inProgress-chip").count() > 0:
                                    data["sections"][name] = "In progress"
                except:
                    continue

            # Activity log - targeting .activity class found in HTML
            try:
                activity_items = await page.locator(".activity").all()
                for item in activity_items:
                    date_el = item.locator(".date")
                    title_el = item.locator(".activity-title")
                    text_el = item.locator(".activity-text")
                    
                    date = await date_el.inner_text() if await date_el.count() > 0 else ""
                    title = await title_el.inner_text() if await title_el.count() > 0 else ""
                    text = await text_el.inner_text() if await text_el.count() > 0 else ""
                    
                    if title or text:
                        entry = f"[{date.strip()}] {title.strip()}: {text.strip()}".replace("\n", " ")
                        data["activity"].append(entry)
            except:
                pass

            return data

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            # Take a screenshot for debugging if it fails
            await page.screenshot(path="error_screenshot.png")
            return None
        finally:
            await browser.close()

def load_previous_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return None
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            logging.warning(f"Failed to load status.json: {e}")
            return None
    return None

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def compare_statuses(old, new):
    if not old:
        logging.info("No previous status found. This is the first run.")
        return True

    changes = []
    
    if old.get("overall_status") != new.get("overall_status"):
        changes.append(f"Overall status changed: {old.get('overall_status')} -> {new.get('overall_status')}")

    old_sections = old.get("sections", {})
    new_sections = new.get("sections", {})

    for section, status in new_sections.items():
        if section not in old_sections:
            changes.append(f"New section added: {section} ({status})")
        elif old_sections[section] != status:
            changes.append(f"Section '{section}' updated: {old_sections[section]} -> {status}")

    if len(new.get("activity", [])) > len(old.get("activity", [])):
        changes.append(f"New activity detected! Total items: {len(new.get('activity'))}")

    if changes:
        logging.info("CHANGES DETECTED:")
        for change in changes:
            logging.info(f" - {change}")
        return True
    else:
        logging.info("No changes detected.")
        return False

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_notification(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            import httpx
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            # Ensure message is not empty and has valid format
            if not message:
                message = "Status check completed (no changes)."
                
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"<b>🇨🇦 IRCC Tracker Update:</b>\n\n{message}",
                "parse_mode": "HTML"
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logging.error(f"Telegram API error: {response.status_code} - {response.text}")
                else:
                    logging.info("Notification sent via Telegram.")
        except Exception as e:
            logging.error(f"Failed to send Telegram notification: {e}")
    else:
        logging.info(f"Notification (print-only): {message}")

async def main():
    VERSION = "2.0"
    logging.info(f"--- IRCC Tracker {VERSION} starting ---")
    # Log environment variable presence (not values) for debugging
    logging.info(f"Environment check: UCI={bool(UCI)} ({len(UCI) if UCI else 0} chars), "
                 f"PASSWORD={bool(PASSWORD)} ({len(PASSWORD) if PASSWORD else 0} chars), "
                 f"APP_NUMBER={bool(APP_NUMBER)}, "
                 f"TG_TOKEN={bool(TELEGRAM_TOKEN)}, TG_CHAT={bool(TELEGRAM_CHAT_ID)}")

    if not UCI or not PASSWORD:
        logging.error("UCI and PASSWORD must be set in .env file or GitHub Secrets.")
        return

    new_status = await get_current_status()
    if new_status:
        old_status = load_previous_status()
        
        # Determine changes for notification
        changes = []
        if old_status:
            if old_status.get("overall_status") != new_status.get("overall_status"):
                changes.append(f"<b>Overall Status:</b> {old_status.get('overall_status')} ➡️ {new_status.get('overall_status')}")
            
            old_sections = old_status.get("sections", {})
            new_sections = new_status.get("sections", {})
            for section, status in new_sections.items():
                if old_sections.get(section) != status:
                    changes.append(f"<b>{section}:</b> {old_sections.get(section, 'N/A')} ➡️ {status}")
        # Map statuses to emojis
        status_icons = {
            "Completed": "✅",
            "In progress": "⏳",
            "Not started": "📋",
            "Unknown": "❓"
        }

        if old_status:
            changes.append("<b>STATUS UPDATE DETECTED</b>\n")
            if old_status.get("overall_status") != new_status.get("overall_status"):
                changes.append(f"<b>Overall:</b> {old_status.get('overall_status')} ➡️ <b>{new_status.get('overall_status')}</b>")
            
            old_sections = old_status.get("sections", {})
            new_sections = new_status.get("sections", {})
            section_changes = []
            for section, status in new_sections.items():
                if old_sections.get(section) != status:
                    section_changes.append(f"• <b>{section}:</b> {old_sections.get(section, 'N/A')} ➡️ <b>{status}</b>")
            
            if section_changes:
                changes.append("\n".join(section_changes))
            
            changes.append(f"\n<b>Last Updated:</b> {new_status.get('last_updated')}")
        else:
            # Initial capture - simplified
            changes.append("🇨🇦 <b>CITIZENSHIP TRACKER</b>\n")
            changes.append(f"<b>Overall Status:</b> {new_status.get('overall_status')}")
            changes.append(f"<b>Last Updated:</b> {new_status.get('last_updated')}\n")
            
            changes.append("<b>Current Progress:</b>")
            for section, status in new_status.get("sections", {}).items():
                changes.append(f"• {section}: <b>{status}</b>")
            
            if new_status.get("activity"):
                changes.append(f"\n<b>Recent History:</b>")
                # Show top 3 most recent activities
                for activity in new_status.get("activity", [])[:3]:
                    parts = activity.split("]", 1)
                    if len(parts) > 1:
                        date_part = parts[0].replace("[", "").strip()
                        desc_part = parts[1].split(":", 1)
                        title = desc_part[0].strip() if len(desc_part) > 1 else "Update"
                        changes.append(f"• {date_part}: <b>{title}</b>")
                    else:
                        changes.append(f"• {activity[:50]}...")

        if compare_statuses(old_status, new_status):
            save_status(new_status)
            # Use a slightly different header for the actual notification
            final_message = "\n".join(changes)
            await send_notification(final_message)
            logging.info("Status updated and saved.")
    else:
        logging.error("Failed to retrieve current status.")

if __name__ == "__main__":
    asyncio.run(main())
