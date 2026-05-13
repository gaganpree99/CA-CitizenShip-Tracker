# 🇨🇦 IRCC Citizenship Status Tracker

An automated tool to monitor changes in your Canadian citizenship application status and get notified immediately via Telegram.

## ✨ Features

- **Automated Hourly Checks:** Uses GitHub Actions to check your status every hour, 24/7.
- **Deep Status Tracking:** Monitors overall status, individual section progress (Background, Test, Presence, etc.), and "Last Updated" dates.
- **Activity History:** Automatically captures and tracks new entries in your application history.
- **Instant Notifications:** Get notified on your phone via Telegram as soon as a change is detected.
- **Privacy First:** Designed to run in a private repository using GitHub Secrets to keep your credentials safe.

## 🚀 Setup Instructions

### 1. Prerequisites
- A **private** GitHub repository to host the code.
- Your IRCC Tracker credentials (UCI and Password).

### 2. Telegram Configuration (Optional but Recommended)
To receive mobile notifications:
1.  **Create a Bot:** Message [@BotFather](https://t.me/botfather) on Telegram, send `/newbot`, and save the **API Token**.
2.  **Get your Chat ID:** Message [@userinfobot](https://t.me/userinfobot) to get your unique **ID**.
3.  **Start the Bot:** Open a chat with your new bot and click **Start**.

### 3. GitHub Actions Setup
1.  Push this project to your **private** GitHub repository.
2.  In your repository, go to **Settings > Secrets and variables > Actions**.
3.  Add the following **Repository secrets**:
    - `UCI`: Your 8 or 10-digit UCI.
    - `PASSWORD`: Your IRCC tracker password.
    - `APP_NUMBER`: (Optional) Your application number.
    - `TELEGRAM_TOKEN`: (Optional) Your Telegram bot token.
    - `TELEGRAM_CHAT_ID`: (Optional) Your Telegram chat ID.

### 4. Local Development (Optional)
If you want to run the tracker on your own machine:
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```
2.  Create a `.env` file with your credentials (see `.env.example`).
3.  Run the scraper:
    ```bash
    python scraper.py
    ```

## 📊 How it Works
1.  The GitHub Action wakes up every hour.
2.  It logs into the IRCC portal using Playwright Stealth.
3.  It compares the current dashboard data with the previous state stored in `status.json`.
4.  If a change is found (e.g., a section moves from "In progress" to "Completed"), it sends a Telegram message.
5.  It commits the updated `status.json` back to your repository.

## ⚠️ Disclaimer
This tool is for personal use only. Ensure you comply with IRCC's Terms of Use. Frequent automated access to government portals may result in temporary IP blocks or account restrictions. Use at your own risk.
