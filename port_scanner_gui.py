#!/usr/bin/env python3
"""
Network Port Scanner - GUI
----------------------------
A simple desktop GUI (built with tkinter, included with Python) for the
port scanner. Scans run in a background thread so the window doesn't freeze.

⚠️ IMPORTANT / LEGAL NOTE:
Only scan devices and networks you own or have explicit permission to test.
Scanning networks/devices without authorization is illegal in most countries
(including under India's IT Act, 2000). Use this only on your home network,
personal devices, or lab environments you control.

Run with:
    python3 port_scanner_gui.py

Requires scanner_core.py to be in the same folder.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os

import scanner_core as core


class PortScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Port Scanner")
        self.root.geometry("650x550")
        self.root.resizable(True, True)

        self.last_result = None  # holds scan result dict for export
        self.scanning = False

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        # --- Input frame ---
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", **pad)

        ttk.Label(frame, text="Target (IP or subnet):").grid(row=0, column=0, sticky="w")
        self.target_entry = ttk.Entry(frame, width=30)
        self.target_entry.insert(0, "192.168.1.1")
        self.target_entry.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(frame, text="Ports (blank = common):").grid(row=1, column=0, sticky="w")
        self.ports_entry = ttk.Entry(frame, width=30)
        self.ports_entry.grid(row=1, column=1, sticky="w", padx=5)

        self.banner_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Grab banners", variable=self.banner_var).grid(
            row=2, column=0, sticky="w", pady=4
        )

        ttk.Label(frame, text="Timeout (s):").grid(row=2, column=1, sticky="w")
        self.timeout_entry = ttk.Entry(frame, width=6)
        self.timeout_entry.insert(0, "0.5")
        self.timeout_entry.grid(row=2, column=1, sticky="e")

        # --- Buttons ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", **pad)

        self.scan_btn = ttk.Button(btn_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side="left", padx=5)

        self.export_json_btn = ttk.Button(
            btn_frame, text="Export JSON", command=lambda: self.export("json"), state="disabled"
        )
        self.export_json_btn.pack(side="left", padx=5)

        self.export_csv_btn = ttk.Button(
            btn_frame, text="Export CSV", command=lambda: self.export("csv"), state="disabled"
        )
        self.export_csv_btn.pack(side="left", padx=5)

        # --- Progress bar ---
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill="x", padx=8, pady=(0, 6))

        self.status_label = ttk.Label(self.root, text="Ready.")
        self.status_label.pack(fill="x", padx=8)

        # --- Output text area ---
        text_frame = ttk.Frame(self.root)
        text_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self.output = tk.Text(text_frame, wrap="word", state="disabled", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def log(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_log(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def update_progress(self, done, total):
        # Called from the background thread; schedule the UI update on the main thread
        pct = int((done / total) * 100) if total else 0
        self.root.after(0, lambda: self.progress.configure(value=pct))

    def start_scan(self):
        if self.scanning:
            return

        target = self.target_entry.get().strip()
        ports = self.ports_entry.get().strip() or None
        grab_banners = self.banner_var.get()

        try:
            timeout = float(self.timeout_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid input", "Timeout must be a number.")
            return

        if not target:
            messagebox.showerror("Invalid input", "Please enter a target IP or subnet.")
            return

        self.scanning = True
        self.scan_btn.configure(state="disabled")
        self.export_json_btn.configure(state="disabled")
        self.export_csv_btn.configure(state="disabled")
        self.progress.configure(value=0)
        self.clear_log()
        self.status_label.configure(text=f"Scanning {target} ...")
        self.log(f"Starting scan of {target} ...\n")

        thread = threading.Thread(
            target=self._run_scan, args=(target, ports, timeout, grab_banners), daemon=True
        )
        thread.start()

    def _run_scan(self, target, ports, timeout, grab_banners):
        try:
            result = core.scan_targets(
                target,
                port_str=ports,
                timeout=timeout,
                grab_banners=grab_banners,
                progress_callback=self.update_progress,
            )
        except ValueError:
            self.root.after(0, lambda: messagebox.showerror("Invalid target", f"'{target}' is not a valid IP or subnet."))
            self.root.after(0, self._scan_finished, None)
            return

        self.root.after(0, self._scan_finished, result)

    def _scan_finished(self, result):
        self.scanning = False
        self.scan_btn.configure(state="normal")
        self.progress.configure(value=100 if result else 0)

        if result is None:
            self.status_label.configure(text="Scan failed.")
            return

        self.last_result = result
        self.export_json_btn.configure(state="normal")
        self.export_csv_btn.configure(state="normal")
        self.status_label.configure(text=f"Scan complete — {result['scanned_at']}")

        for host in result["hosts"]:
            self.log(f"[+] Host: {host['ip']}")
            if host["open_ports"]:
                for entry in host["open_ports"]:
                    line = f"    {entry['port']}/tcp  OPEN  {entry['service']}"
                    if entry["banner"]:
                        line += f"  | {entry['banner']}"
                    self.log(line)
            else:
                self.log("    No open ports found.")
            self.log("")

    def export(self, fmt):
        if not self.last_result:
            return

        ext = f".{fmt}"
        filepath = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(fmt.upper(), f"*{ext}")],
            initialfile=f"scan_results{ext}",
        )
        if not filepath:
            return

        try:
            if fmt == "json":
                core.export_json(self.last_result, filepath)
            else:
                core.export_csv(self.last_result, filepath)
            messagebox.showinfo("Exported", f"Results saved to:\n{filepath}")
        except OSError as e:
            messagebox.showerror("Export failed", str(e))


def main():
    root = tk.Tk()
    app = PortScannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
