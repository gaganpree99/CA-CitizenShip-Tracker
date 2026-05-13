# 🇨🇦 Canadian Citizenship Status Tracker

A robust, automated tool to monitor your Canadian citizenship application progress. Never refresh the IRCC portal again—get notified the second your status changes.

## ✨ Why use this?

- **Real-time Alerts:** Get a Telegram message the moment a section (like Background Check or Physical Presence) is updated.
- **Hourly Monitoring:** Automatically checks your status 24 times a day using GitHub Actions.
- **Historical Tracking:** Keeps a log of your "Recent Activity" and captures status updates as they happen.
- **Clean Aesthetic:** Simple, easy-to-read notifications delivered straight to your phone.
- **Secure:** Designed to run in a private repository using GitHub Secrets to protect your UCI and Password.

---

## 🚀 Step-by-Step Setup Guide

### 1. Repository Setup
1.  **Create a New Private Repository:** Go to [GitHub](https://github.com/new) and create a new **Private** repository.
2.  **Upload the Code:** Upload `scraper.py`, `requirements.txt`, and the `.github/` folder to your new repository.

### 2. Configure Telegram Notifications
Get alerts on your phone by creating a simple Telegram bot:
1.  **Create the Bot:** Search for [@BotFather](https://t.me/botfather) on Telegram and send `/newbot`. Follow the steps to get your **API Token**.
2.  **Get your Chat ID:** Search for [@userinfobot](https://t.me/userinfobot) and send it any message to get your unique **ID**.
3.  **Start the Bot:** Open a chat with your new bot and click **Start**.

### 3. Add Your Credentials (GitHub Secrets)
To keep your data safe, we use GitHub Secrets instead of hardcoding your password:
1.  In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
2.  Add the following **Repository secrets**:
    - `UCI`: Your 8 or 10-digit Unique Client Identifier.
    - `PASSWORD`: Your IRCC Tracker password.
    - `TELEGRAM_TOKEN`: The API Token from BotFather.
    - `TELEGRAM_CHAT_ID`: The ID from userinfobot.

### 4. Enable the Automation
The tracker is set to run **every hour** automatically.
- To check if it's working, go to the **Actions** tab in your repository.
- You can manually trigger a run by selecting the "IRCC Status Check" workflow and clicking **Run workflow**.

---

## 🛠 Local Development
If you prefer to run the script on your own computer:

1.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```
2.  **Configure Environment:** Create a `.env` file in the project root:
    ```env
    UCI=your_uci
    PASSWORD=your_password
    TELEGRAM_TOKEN=your_bot_token
    TELEGRAM_CHAT_ID=your_chat_id
    ```
3.  **Run:** `python scraper.py`

---

## 📝 Important Notes & Troubleshooting
- **Maintenance Windows:** IRCC often performs maintenance on weekends (usually Saturday night/Sunday morning). The tracker may fail during these times; this is normal.
- **Bot Permissions:** If you aren't receiving messages, make sure you have clicked **"Start"** in your chat with the bot.
- **Security:** Always keep your repository **Private**. Your UCI and Password are sensitive information.

---

## 🤝 Disclaimer
This project is an independent tool and is not affiliated with Immigration, Refugees and Citizenship Canada (IRCC). Use responsibly and in accordance with government terms of service.
