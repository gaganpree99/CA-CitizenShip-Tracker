# 🇨🇦 Canadian Citizenship Status Tracker

A robust, automated tool to monitor your Canadian citizenship application progress. Never refresh the IRCC portal again—get notified the second your status changes.

## ✨ Features

- **Automated Hourly Checks:** Runs in the background on your Mac every hour.
- **Firewall Proof:** Uses your local internet to bypass government-grade blocks (Data centers like GitHub are blocked by IRCC).
- **Real-time Alerts:** Get a Telegram message the moment a section (like Background Check or Physical Presence) is updated.
- **Clean Aesthetic:** Professional, easy-to-read notifications delivered straight to your phone.

---

## 🚀 Step-by-Step Setup Guide

### 1. Project Setup
1.  **Clone/Download** this project to your Mac.
2.  **Install Dependencies:**
    ```bash
    cd citizenship-tracker
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    playwright install firefox
    ```

### 2. Configure Telegram Notifications
1.  **Create a Bot:** Search for [@BotFather](https://t.me/botfather) on Telegram and send `/newbot`. Save the **API Token**.
2.  **Get your Chat ID:** Search for [@userinfobot](https://t.me/userinfobot) and send it a message to get your unique **ID**.
3.  **Start the Bot:** Open a chat with your new bot and click **Start**.

### 3. Configure Credentials
Create a `.env` file in the project root:
```env
UCI=your_10_digit_uci
PASSWORD=your_password
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🛠 How to Automate on macOS (Best Way)

Since IRCC blocks GitHub and other cloud servers, the best way to run this is directly on your Mac using a **LaunchAgent**. This will run the script every hour silently in the background.

1.  **Open Terminal** and navigate to your project folder.
2.  **Copy the automation file:**
    ```bash
    cp com.gaganpreet.citizenshiptracker.plist ~/Library/LaunchAgents/
    ```
3.  **Load the timer:**
    ```bash
    launchctl load ~/Library/LaunchAgents/com.gaganpreet.citizenshiptracker.plist
    ```

*To stop the automation later, use `launchctl unload` with the same path.*

---

## 📝 Troubleshooting
- **Maintenance Windows:** IRCC portals usually go down for maintenance on Saturday nights. If the tracker fails then, it's normal.
- **Sleep Mode:** The tracker runs whenever your Mac is awake. It will catch up on missed checks as soon as you wake your computer.
- **Logs:** Check `tracker_local.log` in the project folder to see the history of runs.

---

## 🤝 Disclaimer
This project is an independent tool and is not affiliated with IRCC. Use responsibly.
