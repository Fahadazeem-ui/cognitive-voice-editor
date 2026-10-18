#!/usr/bin/env python3
"""Cognitive Voice Editor – Desktop UI"""
from __future__ import annotations
import os, queue, sys, threading, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "Cognitive Voice Editor"
APP_SIZE = "720x560"

class PipelineWorker(threading.Thread):
    def __init__(self, input_path, output_path, language, api_key, model_size, log_queue, done_callback):
        super().__init__(daemon=True)
        self.input_path = input_path
        self.output_path = output_path
        self.language = language or None
        self.api_key = api_key or None
        self.model_size = model_size
        self.log_queue = log_queue
        self.done_callback = done_callback

    def log(self, msg):
        self.log_queue.put(msg)

    def run(self):
        try:
            self.log("Starting full pipeline…")
            self.log(f"Input : {self.input_path}")
            self.log(f"Output: {self.output_path}")
            work = Path("pipeline_work")
            work.mkdir(parents=True, exist_ok=True)
            m01, m02, m03, m04 = work/"01_manifest.json", work/"02_pruned.json", work/"03_paced.json", work/"04_welded.json"
            dry_run = not bool(self.api_key)
            if dry_run:
                self.log("WARNING: No API key → retakes will NOT be removed.")
            self.log("Module 01: Ingestion + VAD + alignment…")
            from src.config import AudioConfig
            from src.pipeline import SessionOnePipeline
            cfg = AudioConfig(whisper_model_size=self.model_size, device="cpu", compute_type="int8", language=self.language)
            SessionOnePipeline(cfg).run(self.input_path, m01)
            self.log("Module 01 done")
            self.log("Module 02: Cognitive pruning…")
            from src.prune_pipeline import CognitivePruningPipeline
            CognitivePruningPipeline(api_key=self.api_key, dry_run=dry_run, model_name="gemini-2.5-flash").run(m01, m02)
            self.log("Module 02 done")
            self.log("Module 03: Dynamic pacing…")
            from src.pacing_pipeline import PacingPipeline
            PacingPipeline().run(m02, m03)
            self.log("Module 03 done")
            self.log("Module 04: Acoustic welding…")
            from src.welding_pipeline import WeldingPipeline
            WeldingPipeline().run(raw_audio_path=self.input_path, paced_manifest_path=m03, output_wav=self.output_path, output_manifest=m04)
            self.log("Module 04 done")
            self.log(f"DONE → {self.output_path}")
            self.done_callback(True, str(self.output_path))
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            self.done_callback(False, str(exc))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.minsize(640, 480)
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.lang_var = tk.StringVar(value="ur")
        self.key_var = tk.StringVar(value=os.environ.get("GEMINI_API_KEY", ""))
        self.model_var = tk.StringVar(value="base")
        self.status_var = tk.StringVar(value="Ready")
        self.log_queue = queue.Queue()
        self._build_ui()
        self.after(200, self._poll_log)

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self, padding=16)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Cognitive Voice Editor", font=("Segoe UI", 16, "bold")).pack(anchor=tk.W, **pad)
        ttk.Label(frm, text="Raw recording → clean natural track", font=("Segoe UI", 9)).pack(anchor=tk.W, padx=12, pady=(0, 10))
        row1 = ttk.Frame(frm); row1.pack(fill=tk.X, **pad)
        ttk.Label(row1, text="Audio file:", width=12).pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.input_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row1, text="Browse…", command=self._browse_input).pack(side=tk.LEFT)
        row2 = ttk.Frame(frm); row2.pack(fill=tk.X, **pad)
        ttk.Label(row2, text="Save as:", width=12).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row2, text="Browse…", command=self._browse_output).pack(side=tk.LEFT)
        row3 = ttk.Frame(frm); row3.pack(fill=tk.X, **pad)
        ttk.Label(row3, text="Language:", width=12).pack(side=tk.LEFT)
        ttk.Combobox(row3, textvariable=self.lang_var, values=["ur", "en", "hi", "ar", "auto"], width=10, state="readonly").pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(row3, text="Model:").pack(side=tk.LEFT)
        ttk.Combobox(row3, textvariable=self.model_var, values=["tiny", "base", "small", "medium"], width=10, state="readonly").pack(side=tk.LEFT, padx=(8, 0))
        row4 = ttk.Frame(frm); row4.pack(fill=tk.X, **pad)
        ttk.Label(row4, text="Gemini API key:", width=12).pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=self.key_var, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(frm, text="Free key: https://aistudio.google.com/apikey", font=("Segoe UI", 8), foreground="#666").pack(anchor=tk.W, padx=12)
        row5 = ttk.Frame(frm); row5.pack(fill=tk.X, **pad)
        self.start_btn = ttk.Button(row5, text="Start Cleaning", command=self._start)
        self.start_btn.pack(side=tk.LEFT)
        ttk.Button(row5, text="Open output folder", command=self._open_out_folder).pack(side=tk.LEFT, padx=8)
        ttk.Label(frm, text="Log:").pack(anchor=tk.W, padx=12, pady=(10, 0))
        self.log_text = tk.Text(frm, height=14, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        ttk.Label(frm, textvariable=self.status_var, font=("Segoe UI", 9)).pack(anchor=tk.W, padx=12)

    def _browse_input(self):
        path = filedialog.askopenfilename(title="Select raw audio", filetypes=[("Audio", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All", "*.*")])
        if path:
            self.input_var.set(path)
            p = Path(path)
            if not self.output_var.get():
                self.output_var.set(str(p.with_name(p.stem + "_clean.wav")))

    def _browse_output(self):
        path = filedialog.asksaveasfilename(title="Save clean audio", defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if path:
            self.output_var.set(path)

    def _append_log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _poll_log(self):
        try:
            while True:
                self._append_log(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        self.after(200, self._poll_log)

    def _start(self):
        inp = self.input_var.get().strip()
        out = self.output_var.get().strip()
        if not inp or not Path(inp).is_file():
            messagebox.showerror("Missing file", "Please choose a valid audio file.")
            return
        if not out:
            p = Path(inp)
            out = str(p.with_name(p.stem + "_clean.wav"))
            self.output_var.set(out)
        lang = self.lang_var.get()
        if lang == "auto":
            lang = None
        self.start_btn.configure(state=tk.DISABLED)
        self.status_var.set("Processing… please wait")
        def on_done(ok, info):
            self.after(0, lambda: self._finish(ok, info))
        PipelineWorker(Path(inp), Path(out), lang, self.key_var.get().strip() or None, self.model_var.get(), self.log_queue, on_done).start()

    def _finish(self, ok, info):
        self.start_btn.configure(state=tk.NORMAL)
        if ok:
            self.status_var.set("Done")
            messagebox.showinfo("Done", f"Clean audio saved:\n{info}")
        else:
            self.status_var.set("Failed")
            messagebox.showerror("Error", info)

    def _open_out_folder(self):
        out = self.output_var.get().strip()
        folder = str(Path(out).parent) if out else os.getcwd()
        if sys.platform == "win32":
            os.startfile(folder)

def main():
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    App().mainloop()

if __name__ == "__main__":
    main()
