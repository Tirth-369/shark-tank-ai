"""
Shark Tank AI — Tkinter desktop application
Place this file beside data(2).csv (or data.csv), pitch_extractor.py and models/.
Train models first using run_train_tkinter.bat if models/ is missing.
"""
from __future__ import annotations

import os, json, math, traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
try:
    from PIL import Image, ImageTk, ImageOps, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
import numpy as np
import pandas as pd
import joblib

from pitch_extractor import extract_pitch

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
DATA_PATH = ROOT / "data.csv"
if not DATA_PATH.exists():
    DATA_PATH = ROOT / "data(2).csv"

# ---------- Theme ----------
BG = "#080d17"
SIDEBAR = "#091321"
PANEL = "#101d2d"
PANEL2 = "#142338"
BORDER = "#24374f"
TEXT = "#edf7ff"
MUTED = "#9bb0c8"
CYAN = "#3de4ff"
CYAN_DARK = "#00a9c7"
GREEN = "#56e0c0"
AMBER = "#ffc978"
RED = "#ff7585"
FONT = ("Segoe UI", 10)
TITLE_FONT = ("Segoe UI", 25, "bold")

SHARKS = ["Namita", "Vineeta", "Anupam", "Aman", "Peyush"]
SHARK_PROFILES = [
    ("Aman Gupta", "boAt", "aman"), ("Anupam Mittal", "Shaadi.com", "anupam"),
    ("Ashneer Grover", "BharatPe", "ashneer"), ("Ghazal Alagh", "Mamaearth", "ghazal"),
    ("Namita Thapar", "Emcure", "namita"), ("Peyush Bansal", "Lenskart", "peyush"),
    ("Vineeta Singh", "SUGAR Cosmetics", "vineeta")
]
SAMPLE = """We are building a D2C healthy snack brand in Maharashtra for young professionals.
We have been operating since 2023 and generate ₹50 lakh annual revenue with around
4,000 customers. We are asking for ₹50 lakh in exchange for 5% equity at a requested
valuation of ₹1000 lakh. Our products are sold through our website and Amazon, and
we plan to expand into retail stores. We have strong gross margins and a differentiated product."""

def fmt_money(x):
    try: return f"₹{float(x):,.1f} lakh"
    except (TypeError, ValueError): return "—"
def fmt_pct(x):
    try: return f"{float(x)*100:.1f}%"
    except (TypeError, ValueError): return "—"
def age_text(x):
    return {0: "Young", 1: "Middle", 2: "Old"}.get(int(x), "Middle")

class SharkTankApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shark Tank AI | Pitch Intelligence Platform")
        self.geometry("1440x900")
        self.minsize(1120, 720)
        self.configure(bg=BG)
        self.df = self.load_data()
        self.models, self.meta = self.load_models()
        self.industries = sorted(self.df["Industry"].dropna().astype(str).unique()) if "Industry" in self.df else []
        self.states = sorted(self.df["Pitchers State"].dropna().astype(str).str.split(",").str[0].unique()) if "Pitchers State" in self.df else []
        self.current_page = "Home"
        self.last_pitch = ""
        self.last_result = None
        self.last_extraction = None
        self.last_inputs = None
        self.selected_sharks = SHARKS.copy()
        self._configure_styles()
        self._build_shell()
        self.show_page("Home")

    def load_data(self):
        if not DATA_PATH.exists():
            messagebox.showerror("Dataset not found", "Place data.csv or data(2).csv beside tkinter_app.py.")
            raise FileNotFoundError("Dataset missing")
        return pd.read_csv(DATA_PATH)

    def load_models(self):
        """Load every model and retain a useful diagnostic if anything is missing."""
        required = [
            "deal_model", "offer_model", "valuation_model",
            "deal_amount_model", "equity_model", "num_sharks_model",
            *[f"shark_{s.lower()}" for s in SHARKS],
        ]
        self.model_load_error = None
        if not MODEL_DIR.exists():
            self.model_load_error = f"Models folder not found: {MODEL_DIR}"
            return {}, {}

        missing = [name for name in required if not (MODEL_DIR / f"{name}.pkl").is_file()]
        if not (MODEL_DIR / "metadata.pkl").is_file():
            missing.append("metadata.pkl")
        if missing:
            self.model_load_error = (
                "Missing model files in the models folder: " + ", ".join(missing)
                + ". Run the training script successfully before predicting."
            )
            return {}, {}

        try:
            models = {name: joblib.load(MODEL_DIR / f"{name}.pkl") for name in required}
            meta = joblib.load(MODEL_DIR / "metadata.pkl")
            # Verify the expected model interface before enabling predictions.
            for name in ("deal_model", "offer_model", *[f"shark_{s.lower()}" for s in SHARKS]):
                if not hasattr(models[name], "predict_proba"):
                    raise TypeError(f"{name}.pkl does not support predict_proba")
            for name in ("valuation_model", "deal_amount_model", "equity_model", "num_sharks_model"):
                if not hasattr(models[name], "predict"):
                    raise TypeError(f"{name}.pkl does not support predict")
            self.model_load_error = None
            return models, meta
        except Exception as exc:
            self.model_load_error = f"Could not load trained models: {type(exc).__name__}: {exc}"
            traceback.print_exc()
            return {}, {}

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=FONT)
        style.configure("Treeview", background=PANEL, foreground=TEXT, fieldbackground=PANEL,
                        rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL2, foreground=CYAN,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#17465a")], foreground=[("selected", TEXT)])
        style.configure("TCombobox", fieldbackground="#0b1422", background=PANEL2, foreground=TEXT)
        style.configure("Vertical.TScrollbar", background=PANEL2, troughcolor=BG, arrowcolor=CYAN)

    def _build_shell(self):
        header = tk.Frame(self, bg=BG, height=68)
        header.pack(fill="x", padx=24, pady=(14, 8))
        tk.Label(header, text="🦈  SHARK TANK", bg=BG, fg=TEXT,
                 font=("Segoe UI", 19, "bold")).pack(side="left")
        tk.Label(header, text="AI", bg=BG, fg=CYAN, font=("Segoe UI", 19, "bold")).pack(side="left", padx=(0, 20))
        tk.Label(header, text="PITCH INTELLIGENCE PLATFORM", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left", pady=(8, 0))
        tk.Label(header, text="INDIA EDITION   ●", bg=BG, fg=CYAN,
                 font=("Segoe UI", 9, "bold")).pack(side="right", pady=(8, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(body, bg=SIDEBAR, width=225, highlightbackground=BORDER, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="WORKSPACE", bg=SIDEBAR, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(22, 12))
        self.nav_buttons = {}
        nav = [("⌂", "Home"), ("▦", "Companies"), ("▥", "Analytics"), ("✧", "Pitch Analyzer"),
               ("♟", "Compare Sharks"), ("◈", "Scenario Simulator"), ("▤", "Dataset Insights"), ("◎", "Model Card")]
        for icon, name in nav:
            b = tk.Button(self.sidebar, text=f"  {icon}    {name}", anchor="w",
                          command=lambda n=name: self.show_page(n), bg=SIDEBAR, fg=TEXT,
                          activebackground="#13283c", activeforeground=CYAN, relief="flat",
                          bd=0, padx=16, pady=13, font=("Segoe UI", 10, "bold"), cursor="hand2")
            b.pack(fill="x", padx=9, pady=2)
            self.nav_buttons[name] = b
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=20)
        tk.Label(self.sidebar, text="Historical data\nModel-assisted insights", bg=SIDEBAR,
                 fg=MUTED, justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=18)
        # Scrollable main workspace: every page can extend below the window.
        self.content_outer = tk.Frame(body, bg=BG)
        self.content_outer.pack(side="left", fill="both", expand=True)

        self.content_canvas = tk.Canvas(
            self.content_outer, bg=BG, highlightthickness=0, bd=0
        )
        self.content_scrollbar = ttk.Scrollbar(
            self.content_outer, orient="vertical", command=self.content_canvas.yview
        )
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)

        self.content_scrollbar.pack(side="right", fill="y")
        self.content_canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.content_canvas, bg=BG)
        self.content_window = self.content_canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )

        self.content.bind("<Configure>", self._update_content_scrollregion)
        self.content_canvas.bind("<Configure>", self._resize_content_window)
        self.content_canvas.bind("<Enter>", self._bind_mousewheel)
        self.content_canvas.bind("<Leave>", self._unbind_mousewheel)
        self.content.bind("<Enter>", self._bind_mousewheel)
        self.content.bind("<Leave>", self._unbind_mousewheel)
        self.content.pack_propagate(True)

        # Keep the same comfortable page padding as the previous layout.
        self.content.configure(padx=26, pady=22)

    def _update_content_scrollregion(self, event=None):
        self.content_canvas.configure(
            scrollregion=self.content_canvas.bbox("all")
        )

    def _resize_content_window(self, event):
        # Make page content use the full available width, while allowing vertical scrolling.
        self.content_canvas.itemconfigure(self.content_window, width=event.width)

    def _bind_mousewheel(self, event=None):
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, event=None):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.delta:
            self.content_canvas.yview_scroll(
                int(-event.delta / 120), "units"
            )

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.content_canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.content_canvas.yview_scroll(3, "units")

    def clear_content(self):
        for w in self.content.winfo_children(): w.destroy()

    def show_page(self, page):
        self.current_page = page
        for name, b in self.nav_buttons.items():
            b.configure(bg="#123044" if name == page else SIDEBAR,
                        fg=CYAN if name == page else TEXT)
        self.clear_content()
        getattr(self, "page_" + page.lower().replace(" ", "_"))()
        self.content_canvas.yview_moveto(0)
        self.after_idle(self._update_content_scrollregion)

    def page_title(self, heading, subtitle=None):
        tk.Label(self.content, text=heading, bg=BG, fg=TEXT, font=TITLE_FONT).pack(anchor="w", pady=(0, 4))
        if subtitle:
            tk.Label(self.content, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 18))

    def panel(self, parent=None, padx=18, pady=16):
        box = tk.Frame(parent or self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        box.pack_propagate(True)
        return box

    def section_label(self, parent, text):
        tk.Label(parent, text=text, bg=PANEL, fg=CYAN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(14, 8))

    def metric_card(self, parent, label, value, note=""):
        card = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(card, text=label.upper(), bg=PANEL, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=15, pady=(13, 5))
        tk.Label(card, text=str(value), bg=PANEL, fg=TEXT, font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=15)
        if note: tk.Label(card, text=note, bg=PANEL, fg=CYAN, font=("Segoe UI", 8)).pack(anchor="w", padx=15, pady=(2, 12))
        else: tk.Frame(card, bg=PANEL, height=12).pack()
        return card

    def make_table(self, parent, frame, columns, rows, height=12):
        wrap = tk.Frame(parent, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=14, pady=12)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", height=height)
        for c in columns:
            tree.heading(c, text=c)
            tree.column(c, width=max(110, int(760/max(1,len(columns)))), anchor="w")
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        hs = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1); wrap.columnconfigure(0, weight=1)
        for row in rows: tree.insert("", "end", values=[self.safe(v) for v in row])
        return tree

    @staticmethod
    def safe(v):
        if pd.isna(v): return "—"
        if isinstance(v, (float, np.floating)): return f"{v:,.2f}".rstrip("0").rstrip(".")
        return str(v)

    def load_shark_photo(self, slug, size=(100, 100)):
        """Load a local shark portrait; return None when unavailable."""
        if not PIL_AVAILABLE:
            return None
        candidates = [
            ROOT / "assets" / "sharks" / f"{slug}.jpg",
            ROOT / "assets" / "sharks" / f"{slug}.png",
            ROOT / "assets" / f"{slug}.jpg",
            ROOT / "assets" / f"{slug}.png",
        ]
        photo_path = next((p for p in candidates if p.exists()), None)
        if photo_path is None:
            return None
        try:
            image = Image.open(photo_path).convert("RGBA")
            image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
            mask = Image.new("L", size, 0)
            ImageDraw.Draw(mask).ellipse((1, 1, size[0]-1, size[1]-1), fill=255)
            image.putalpha(mask)
            return ImageTk.PhotoImage(image)
        except Exception as exc:
            print(f"Could not load shark photo {photo_path}: {exc}")
            return None

    def show_shark_details(self, name, company, slug):
        """Open an interactive investor profile with dataset-derived stats."""
        popup = tk.Toplevel(self)
        popup.title(f"{name} | Shark Profile")
        popup.geometry("440x560")
        popup.configure(bg=BG)
        popup.transient(self)

        photo = self.load_shark_photo(slug, (150, 150))
        if photo:
            image_label = tk.Label(popup, image=photo, bg=BG)
            image_label.image = photo
            image_label.pack(pady=(24, 10))
        else:
            tk.Label(popup, text="🦈", bg=BG, fg=CYAN,
                     font=("Segoe UI Emoji", 54)).pack(pady=(24, 10))

        tk.Label(popup, text=name, bg=BG, fg=TEXT,
                 font=("Segoe UI", 20, "bold")).pack()
        tk.Label(popup, text=company, bg=BG, fg=CYAN,
                 font=("Segoe UI", 11)).pack(pady=(3, 16))

        # Match the shark to the investment columns available in this dataset.
        first = name.split()[0]
        amount_col = f"{first} Investment Amount"
        amounts = (pd.to_numeric(self.df[amount_col], errors="coerce").fillna(0)
                   if amount_col in self.df.columns else pd.Series(0, index=self.df.index))
        invested = amounts[amounts > 0]
        stats = [
            ("Recorded investments", f"{len(invested):,}"),
            ("Total investment", fmt_money(invested.sum()) if len(invested) else "—"),
            ("Average investment", fmt_money(invested.mean()) if len(invested) else "—"),
        ]
        for label, value in stats:
            card = tk.Frame(popup, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", padx=28, pady=6)
            tk.Label(card, text=label.upper(), bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(10, 2))
            tk.Label(card, text=value, bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=14, pady=(0, 10))

        tk.Button(popup, text="CLOSE PROFILE", command=popup.destroy,
                  bg=CYAN_DARK, fg="#03121b", relief="flat", padx=22,
                  pady=9, cursor="hand2").pack(pady=18)

    def page_home(self):
        self.page_title(
            "Every pitch. Every shark. Every outcome.",
            "Explore Indian Shark Tank pitches, compare investors, and test your startup against historical deal data."
        )

        total = len(self.df)
        offers_col = self.df.get("Received Offer", pd.Series(0, index=self.df.index))
        offers = int(pd.to_numeric(offers_col, errors="coerce").fillna(0).sum())
        amount_col = self.df.get("Total Deal Amount", pd.Series(0, index=self.df.index))
        total_amount = pd.to_numeric(amount_col, errors="coerce").fillna(0).sum()
        industry_count = self.df["Industry"].nunique() if "Industry" in self.df.columns else "—"

        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x", pady=(4, 20))
        metrics = [
            ("Pitches in dataset", f"{total:,}"),
            ("Pitches with offers", f"{offers:,}"),
            ("Total deal amount", fmt_money(total_amount)),
            ("Industries", industry_count),
        ]
        for label, value in metrics:
            card = self.metric_card(row, label, value)
            card.pack(side="left", fill="x", expand=True, padx=5)

        self.page_title("Meet the Sharks", "Select an investor to explore their recorded investment activity.")
        sharkrow = tk.Frame(self.content, bg=BG)
        sharkrow.pack(fill="x", pady=(0, 18))
        self.shark_images = []  # Keep image references alive for Tkinter.

        for name, company, slug in SHARK_PROFILES:
            card = tk.Frame(sharkrow, bg=PANEL, highlightbackground=BORDER,
                            highlightthickness=1, cursor="hand2")
            card.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            photo = self.load_shark_photo(slug, (78, 78))
            if photo:
                self.shark_images.append(photo)
                avatar = tk.Label(card, image=photo, bg=PANEL, cursor="hand2")
            else:
                initials = "".join(part[0] for part in name.split())
                avatar = tk.Label(card, text=initials, bg="#123044", fg=CYAN,
                                  font=("Segoe UI", 17, "bold"), width=5, height=2,
                                  cursor="hand2")
            avatar.pack(pady=(12, 7))
            name_label = tk.Label(card, text=name, bg=PANEL, fg=TEXT,
                                  font=("Segoe UI", 8, "bold"), cursor="hand2")
            name_label.pack()
            company_label = tk.Label(card, text=company, bg=PANEL, fg=MUTED,
                                     font=("Segoe UI", 8), cursor="hand2")
            company_label.pack(pady=(3, 5))
            action_label = tk.Label(card, text="VIEW PROFILE  →", bg=PANEL, fg=CYAN,
                                    font=("Segoe UI", 7, "bold"), cursor="hand2")
            action_label.pack(pady=(2, 11))

            def open_profile(event, n=name, c=company, sl=slug):
                self.show_shark_details(n, c, sl)
            for widget in (card, avatar, name_label, company_label, action_label):
                widget.bind("<Button-1>", open_profile)

            def enter(event, target=card):
                target.configure(highlightbackground=CYAN, bg=PANEL2)
            def leave(event, target=card):
                target.configure(highlightbackground=BORDER, bg=PANEL)
            card.bind("<Enter>", enter)
            card.bind("<Leave>", leave)

        self.page_title("Popular Companies", "Search and open company records from the historical dataset.")
        search_var = tk.StringVar()
        search_entry = tk.Entry(self.content, textvariable=search_var, bg="#0b1422", fg=TEXT,
                                insertbackground=TEXT, relief="flat", font=FONT)
        search_entry.pack(fill="x", ipady=9, pady=(0, 8))
        search_entry.insert(0, "Search startup or industry…")

        cols = [c for c in ["Startup Name", "Industry", "Received Offer", "Total Deal Amount"]
                if c in self.df.columns]
        holder = tk.Frame(self.content, bg=PANEL)
        holder.pack(fill="both", expand=True)
        tree = self.make_table(holder, None, cols, [], height=7)

        def refresh(*_):
            for item in tree.get_children():
                tree.delete(item)
            query = search_var.get().strip()
            view = self.df
            if query and query != "Search startup or industry…":
                mask = view.astype(str).apply(
                    lambda col: col.str.contains(query, case=False, na=False, regex=False)
                ).any(axis=1)
                view = view[mask]
            if "Startup Name" in view.columns:
                view = view.drop_duplicates("Startup Name")
            for values in view[cols].head(100).itertuples(index=False, name=None):
                tree.insert("", "end", values=[self.safe(v) for v in values])
            count_label.configure(text=f"{len(view):,} matching companies (showing up to 100)")

        count_label = tk.Label(self.content, text="", bg=BG, fg=MUTED)
        count_label.pack(anchor="w", pady=(5, 2))
        search_var.trace_add("write", refresh)
        refresh()

        def open_company(event):
            selection = tree.selection()
            if not selection:
                return
            values = tree.item(selection[0], "values")
            details = "\n".join(f"{cols[i]}: {values[i]}" for i in range(len(values)))
            messagebox.showinfo("Company details", details)
        tree.bind("<Double-1>", open_company)

        tk.Button(self.content, text="🧠  OPEN PITCH ANALYZER  →",
                  command=lambda: self.show_page("Pitch Analyzer"), bg=CYAN_DARK,
                  fg="#03121b", activebackground=CYAN, relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=20, pady=11,
                  cursor="hand2").pack(anchor="w", pady=14)

    def page_companies(self):
        self.page_title("Companies", "Search the historical pitch database by startup, industry, or business description.")
        bar = tk.Frame(self.content, bg=BG); bar.pack(fill="x", pady=(0, 12))
        query = tk.StringVar()
        ent = tk.Entry(bar, textvariable=query, bg="#0b1422", fg=TEXT, insertbackground=TEXT,
                       relief="flat", font=FONT); ent.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        ent.insert(0, "Search companies…")
        holder = tk.Frame(self.content, bg=PANEL); holder.pack(fill="both", expand=True)
        cols = [c for c in ["Startup Name", "Industry", "Season Number", "Received Offer", "Accepted Offer",
                            "Total Deal Amount", "Total Deal Equity", "Business Description"] if c in self.df]
        tree = self.make_table(holder, None, cols, [], height=20)
        def refresh(*_):
            for item in tree.get_children(): tree.delete(item)
            q = query.get().strip()
            view = self.df
            if q and q != "Search companies…":
                mask = view.astype(str).apply(lambda s: s.str.contains(q, case=False, na=False, regex=False)).any(axis=1)
                view = view[mask]
            if "Startup Name" in view: view = view.drop_duplicates("Startup Name")
            for r in view[cols].head(500).itertuples(index=False, name=None):
                tree.insert("", "end", values=[self.safe(v) for v in r])
            count.configure(text=f"{len(view):,} matching records (showing up to 500)")
        query.trace_add("write", refresh)
        count = tk.Label(self.content, text="", bg=BG, fg=MUTED); count.pack(anchor="w", pady=6)
        refresh()

    def draw_bars(self, parent, series, title, max_items=12, suffix=""):
        box = tk.Frame(parent, bg=PANEL); box.pack(fill="x", padx=14, pady=10)
        tk.Label(box, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=10)
        vals = series.head(max_items)
        maximum = max(float(vals.max()) if len(vals) else 1, 1)
        for label, value in vals.items():
            line = tk.Frame(box, bg=PANEL); line.pack(fill="x", padx=14, pady=4)
            tk.Label(line, text=str(label)[:28], width=27, anchor="w", bg=PANEL, fg=MUTED).pack(side="left")
            track = tk.Frame(line, bg="#24374f", height=13); track.pack(side="left", fill="x", expand=True, padx=8)
            fill = tk.Frame(track, bg=CYAN, height=13, width=max(2, int(400*float(value)/maximum)))
            fill.pack(side="left")
            tk.Label(line, text=f"{value:,.1f}{suffix}" if isinstance(value, (float, np.floating)) else f"{value:,}{suffix}",
                     width=12, anchor="e", bg=PANEL, fg=TEXT).pack(side="right")

    def page_analytics(self):
        self.page_title("Analytics", "Historical patterns across industries, offers and seasons.")
        self.draw_bars(self.content, self.df["Industry"].value_counts(), "Pitches by industry")
        if "Received Offer" in self.df:
            rates = self.df.groupby("Industry")["Received Offer"].mean().mul(100).sort_values(ascending=False)
            self.draw_bars(self.content, rates, "Offer rate by industry", suffix="%")
        if "Season Number" in self.df:
            counts = self.df.groupby("Season Number").size().sort_index()
            self.draw_bars(self.content, counts, "Pitch volume by season")

    def page_pitch_analyzer(self):
        self.page_title("Would you get a deal?", "Describe your startup. The extractor identifies facts, then the ML models estimate historical outcomes.")
        tk.Label(self.content, text="YOUR STARTUP PITCH", bg=BG, fg=CYAN, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.pitch_text = tk.Text(self.content, height=7, wrap="word", bg="#0b1422", fg=TEXT,
                                  insertbackground=TEXT, relief="flat", font=("Segoe UI", 10),
                                  padx=12, pady=10, highlightbackground=BORDER, highlightthickness=1)
        self.pitch_text.pack(fill="x", pady=(7, 8))
        btns = tk.Frame(self.content, bg=BG); btns.pack(fill="x")
        tk.Button(btns, text="LOAD SAMPLE PITCH", command=self.load_sample, bg=PANEL2, fg=CYAN,
                  relief="flat", padx=12, pady=8).pack(side="left")
        tk.Button(btns, text="EXTRACT & VERIFY", command=self.extract_and_verify, bg=CYAN_DARK,
                  fg="#03121b", relief="flat", padx=16, pady=8, font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
        self.pitch_verify = tk.Frame(self.content, bg=BG)
        self.pitch_verify.pack(fill="both", expand=True, pady=12)
        if not self.models:
            tk.Label(
                self.pitch_verify,
                text="Prediction models are not loaded: " + (self.model_load_error or "unknown loading error"),
                bg=BG, fg=AMBER, wraplength=1050, justify="left"
            ).pack(anchor="w", pady=6)

    def load_sample(self):
        self.pitch_text.delete("1.0", "end"); self.pitch_text.insert("1.0", SAMPLE)
        self.extract_and_verify()

    def add_field(self, parent, label, value, key, row, col, width=22):
        cell = tk.Frame(parent, bg=PANEL); cell.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
        tk.Label(cell, text=label, bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        var = tk.StringVar(value=str(value))
        ent = tk.Entry(cell, textvariable=var, bg="#0b1422", fg=TEXT, insertbackground=TEXT,
                       relief="flat", width=width, font=FONT)
        ent.pack(fill="x", ipady=7, pady=(4, 0))
        self.pitch_vars[key] = var

    def extract_and_verify(self):
        pitch = self.pitch_text.get("1.0", "end").strip()
        if not pitch:
            messagebox.showwarning("Pitch required", "Enter your startup pitch first."); return
        try:
            ex = extract_pitch(pitch)
        except Exception as exc:
            messagebox.showerror("Pitch extraction failed", f"{type(exc).__name__}: {exc}")
            traceback.print_exc()
            return
        self.last_pitch, self.last_extraction = pitch, ex
        # Keep fallback values dataset-derived, matching the Streamlit version.
        d = self.df
        numeric_defaults = {
            "ask": float(d["Original Ask Amount"].median()), "equity": float(d["Original Offered Equity"].median()),
            "valuation": float(d["Valuation Requested"].median()), "revenue": float(d["Yearly Revenue"].median()),
            "monthly_sales": float(d["Monthly Sales"].median()), "gross_margin": float(d["Gross Margin"].median()),
            "net_margin": float(d["Net Margin"].median()), "ebitda": float(d["EBITDA"].median()),
            "skus": int(d["SKUs"].median()), "started_in": int(d["Started in"].median()),
            "presenters": int(d["Number of Presenters"].median()), "age": 1
        }
        cat_defaults = {"industry": d["Industry"].mode().iloc[0],
                        "state": d["Pitchers State"].dropna().astype(str).str.split(",").str[0].mode().iloc[0]}
        p = {k: (ex[k] if ex.get(k) is not None else v) for k, v in numeric_defaults.items()}
        p.update({k: (ex[k] if ex.get(k) is not None else v) for k, v in cat_defaults.items()})
        estimated = [k for k in numeric_defaults if ex.get(k) is None] + [k for k in cat_defaults if ex.get(k) is None]
        p["bootstrapped"] = 0 if ex.get("bootstrapped") is None else ex["bootstrapped"]
        p["patents"] = 0 if ex.get("patents") is None else ex["patents"]
        p["cash_burn"] = 0 if ex.get("cash_burn") is None else ex["cash_burn"]
        p["estimated_fields"] = estimated
        if ex.get("valuation") is None and ex.get("ask") is not None and ex.get("equity", 0) > 0:
            p["valuation"] = ex["ask"]*100/ex["equity"]; estimated.append("valuation (derived)")
        if ex.get("monthly_sales") is None and ex.get("revenue") is not None:
            p["monthly_sales"] = ex["revenue"]/12; estimated.append("monthly sales (derived)")
        self.last_inputs = p
        for w in self.pitch_verify.winfo_children(): w.destroy()
        detected = [f"{k}: {ex[k]}" for k in ["industry","state","ask","equity","valuation","revenue","customers","started_in"] if ex.get(k) is not None]
        tk.Label(self.pitch_verify, text="WHAT WE UNDERSTOOD", bg=BG, fg=CYAN,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(self.pitch_verify, text="   •   ".join(detected) if detected else "No structured fields detected yet.",
                 bg=BG, fg=GREEN, wraplength=1000, justify="left").pack(anchor="w", pady=6)
        cov = ex.get("extraction_coverage", 0)*100
        tk.Label(self.pitch_verify, text=f"Information captured: {cov:.0f}%    |    Amber values are estimated from dataset statistics.",
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 10))
        box = tk.Frame(self.pitch_verify, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        box.pack(fill="x", pady=5)
        self.pitch_vars = {}
        fields = [
            ("Industry", "industry", p["industry"]), ("Founder state", "state", p["state"]),
            ("Ask amount (₹ lakh)", "ask", p["ask"]), ("Equity offered (%)", "equity", p["equity"]),
            ("Requested valuation (₹ lakh)", "valuation", p["valuation"]), ("Annual revenue (₹ lakh)", "revenue", p["revenue"]),
            ("Monthly sales (₹ lakh)", "monthly_sales", p["monthly_sales"]), ("Gross margin (%)", "gross_margin", p["gross_margin"]),
            ("Net margin (%)", "net_margin", p["net_margin"]), ("EBITDA (₹ lakh)", "ebitda", p["ebitda"]),
            ("Started in", "started_in", p["started_in"]), ("Presenters", "presenters", p["presenters"]),
            ("SKUs / products", "skus", p["skus"]), ("Age group (0 Young, 1 Middle, 2 Old)", "age", p["age"])
        ]
        for i, (label, key, value) in enumerate(fields):
            self.add_field(box, label, value, key, i//3, i%3)
        self.pitch_flags = {}
        flags = tk.Frame(box, bg=PANEL); flags.grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=10)
        for label, key in [("Bootstrapped","bootstrapped"),("Patent / IP","patents"),("Cash burn","cash_burn")]:
            var = tk.BooleanVar(value=bool(p[key])); self.pitch_flags[key] = var
            tk.Checkbutton(flags, text=label, variable=var, bg=PANEL, fg=TEXT, selectcolor="#0b1422",
                           activebackground=PANEL, activeforeground=CYAN).pack(side="left", padx=10)
        tk.Label(box, text="SHARKS TO EVALUATE", bg=PANEL, fg=CYAN,
                 font=("Segoe UI", 9, "bold")).grid(row=6, column=0, sticky="w", padx=14, pady=(5, 0))
        self.shark_vars = {}
        srow = tk.Frame(box, bg=PANEL); srow.grid(row=7, column=0, columnspan=3, sticky="w", padx=8, pady=6)
        for shark in SHARKS:
            v = tk.BooleanVar(value=True); self.shark_vars[shark] = v
            tk.Checkbutton(srow, text=shark, variable=v, bg=PANEL, fg=TEXT, selectcolor="#0b1422",
                           activebackground=PANEL, activeforeground=CYAN).pack(side="left", padx=7)
        tk.Button(self.pitch_verify, text="🧠  ANALYZE MY PITCH", command=self.run_prediction,
                  bg=CYAN_DARK, fg="#03121b", relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=18, pady=11).pack(anchor="w", pady=12)
        if estimated:
            tk.Label(self.pitch_verify, text="Estimated / derived: " + ", ".join(estimated),
                     bg=BG, fg=AMBER, wraplength=1000).pack(anchor="w")

    def collect_inputs(self):
        p = dict(self.last_inputs)
        numeric = ["ask","equity","valuation","revenue","monthly_sales","gross_margin","net_margin",
                   "ebitda","started_in","presenters","skus","age"]
        try:
            for k in numeric: p[k] = float(self.pitch_vars[k].get())
            for k in ["started_in","presenters","skus","age"]: p[k] = int(p[k])
        except ValueError:
            raise ValueError("Please enter valid numeric values in all pitch fields.")
        p["industry"] = self.pitch_vars["industry"].get()
        p["state"] = self.pitch_vars["state"].get()
        for k, v in self.pitch_flags.items(): p[k] = int(v.get())
        sharks = [s for s, v in self.shark_vars.items() if v.get()]
        if not sharks: raise ValueError("Select at least one shark.")
        return p, sharks

    def build_row(self, p, sharks):
        row = {
            "Season Number":5,"Episode Number":10,"Pitch Number":3,
            "Started in":p["started_in"],"Number of Presenters":p["presenters"],
            "Male Presenters":p["presenters"],"Female Presenters":0,"Transgender Presenters":0,"Couple Presenters":0,
            "Pitchers Average Age":p["age"],"Yearly Revenue":p["revenue"],"Monthly Sales":p["monthly_sales"],
            "Gross Margin":p["gross_margin"],"Net Margin":p["net_margin"],"EBITDA":p["ebitda"],
            "Cash Burn":p["cash_burn"],"SKUs":p["skus"],"Has Patents":p["patents"],"Part of Match off":0,
            "Original Ask Amount":p["ask"],"Original Offered Equity":p["equity"],"Valuation Requested":p["valuation"],
            "Namita Present":int("Namita" in sharks),"Vineeta Present":int("Vineeta" in sharks),
            "Anupam Present":int("Anupam" in sharks),"Aman Present":int("Aman" in sharks),
            "Peyush Present":int("Peyush" in sharks),"Ritesh Present":0,"Amit Present":0,"Guest Present":0,
            "Industry":p["industry"],"Pitchers State":p["state"],
            # The training data stores this categorical feature as 'yes' or 'funded'.
            "Bootstrapped":"yes" if int(p["bootstrapped"]) == 1 else "funded",
            "days_into_season":30,"ask_log":np.log1p(max(0,p["ask"])),
            "valuation_requested_log":np.log1p(max(0,p["valuation"])),
            "ask_equity_ratio":p["equity"]/(p["ask"]+1),
            "valuation_ask_ratio":p["valuation"]/(p["ask"]+1),"sharks_present_count":len(sharks)
        }
        return pd.DataFrame([row])

    @staticmethod
    def positive_probability(model, X):
        """Return probability for class 1, independent of class-column ordering."""
        probabilities = model.predict_proba(X)
        classes = list(getattr(model, "classes_", []))
        if not classes and hasattr(model, "named_steps"):
            final_model = model.named_steps.get("model")
            classes = list(getattr(final_model, "classes_", []))
        if 1 in classes:
            return float(probabilities[0, classes.index(1)])
        if len(classes) == 2:
            return float(probabilities[0, 1])
        return 0.0

    def predict(self, p, sharks):
        if not self.models:
            detail = getattr(self, "model_load_error", None)
            raise RuntimeError(detail or "Trained models are unavailable. Run the training script and check the models folder.")

        X = self.build_row(p, sharks)
        # Use the exact feature order saved during training. This prevents
        # missing/extra columns or a different column order at prediction time.
        trained_features = self.meta.get("features", []) if isinstance(self.meta, dict) else []
        if trained_features:
            missing = [col for col in trained_features if col not in X.columns]
            if missing:
                raise ValueError("Prediction input is missing trained features: " + ", ".join(missing))
            X = X.loc[:, trained_features]

        return {
            "deal": self.positive_probability(self.models["deal_model"], X),
            "offer": self.positive_probability(self.models["offer_model"], X),
            "valuation": max(0.0, float(np.expm1(self.models["valuation_model"].predict(X)[0]))),
            "amount": max(0.0, float(np.expm1(self.models["deal_amount_model"].predict(X)[0]))),
            "equity": max(0.0, float(np.expm1(self.models["equity_model"].predict(X)[0]))),
            "num_sharks": float(np.clip(self.models["num_sharks_model"].predict(X)[0], 0, 5)),
            "sharks": {
                shark: self.positive_probability(self.models[f"shark_{shark.lower()}"], X)
                for shark in sharks
            },
        }

    def attractiveness(self, pred, p):
        traction=min(1,(p["revenue"]/(max(p["ask"],1)*2.0)))
        margin=np.clip((p["gross_margin"]+max(p["net_margin"],-20))/100,0,1)
        pressure=1-np.clip(p["valuation"]/(max(p["revenue"]*10,1)),0,1)
        return float(np.clip(100*(.50*pred["deal"]+.18*traction+.17*margin+.15*pressure),0,100))

    def run_prediction(self):
        try:
            p, sharks = self.collect_inputs()
            pred = self.predict(p, sharks)
            self.last_result = {"p":p,"sharks":sharks,"pred":pred}
            self.last_inputs = p
            self.render_prediction(pred, p, self.last_extraction)
        except Exception as e:
            messagebox.showerror("Prediction unavailable", str(e))

    def render_prediction(self, pred, p, ex):
        for w in self.pitch_verify.winfo_children():
            if getattr(w, "_prediction_result", False): w.destroy()
        box = tk.Frame(self.pitch_verify, bg=PANEL, highlightbackground=CYAN, highlightthickness=1)
        box._prediction_result = True
        box.pack(fill="x", pady=10)
        headline = "Strong deal signal" if pred["deal"] >= .70 else ("Positive deal signal" if pred["deal"] >= .50 else "High no-deal risk")
        tk.Label(box, text=headline, bg=PANEL, fg=CYAN, font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(box, text="Based on verified pitch inputs and historical training data.", bg=PANEL, fg=MUTED).pack(anchor="w", padx=16)
        metrics = tk.Frame(box, bg=PANEL); metrics.pack(fill="x", padx=10, pady=12)
        for label, value in [("Deal probability",fmt_pct(pred["deal"])),("Offer probability",fmt_pct(pred["offer"])),
                             ("Expected valuation",fmt_money(pred["valuation"])),("Expected deal amount",fmt_money(pred["amount"]))]:
            c = self.metric_card(metrics, label, value); c.pack(side="left", fill="x", expand=True, padx=5)
        score = self.attractiveness(pred,p)
        tk.Label(box, text=f"Pitch health score: {score:.0f}/100  ·  Dashboard heuristic, not a trained target.",
                 bg=PANEL, fg=GREEN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        tk.Label(box, text=f"Predicted deal structure: valuation {fmt_money(pred['valuation'])}  |  deal {fmt_money(pred['amount'])}  |  equity {pred['equity']:.1f}%  |  expected sharks {pred['num_sharks']:.1f}",
                 bg=PANEL, fg=TEXT, wraplength=1000).pack(anchor="w", padx=16, pady=5)
        if pred["sharks"]:
            best = max(pred["sharks"], key=pred["sharks"].get)
            self.draw_bars(box, (pd.Series(pred["sharks"])*100).sort_values(ascending=False), "Potential shark match", suffix="%")
            tk.Label(box, text=f"Top predicted match: {best} — {pred['sharks'][best]*100:.1f}%",
                     bg=PANEL, fg=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=8)
        tk.Label(box, text="Historical patterns are informative, not guarantees of future investment decisions.",
                 bg=PANEL, fg=AMBER, wraplength=1000).pack(anchor="w", padx=16, pady=(4, 14))

    def page_compare_sharks(self):
        self.page_title("Compare Sharks", "Compare recorded investment activity for the five sharks with trained prediction models.")
        rows=[]
        for shark in SHARKS:
            col=f"{shark} Investment Amount"
            values=pd.to_numeric(self.df[col],errors="coerce").fillna(0) if col in self.df else pd.Series(0,index=self.df.index)
            rows.append((shark,int((values>0).sum()),float(values.sum()),float(values[values>0].mean()) if (values>0).any() else 0))
        box=tk.Frame(self.content,bg=PANEL); box.pack(fill="both",expand=True)
        self.make_table(box,None,["Shark","Recorded investments","Total invested (₹ lakh)","Average investment (₹ lakh)"],rows,8)
        self.draw_bars(self.content,pd.Series({r[0]:r[1] for r in rows}).sort_values(ascending=False),"Recorded investments by shark")

    def page_scenario_simulator(self):
        self.page_title("Scenario Simulator", "Change the terms of the same startup and see how the trained model responds.")
        if not self.last_result:
            tk.Label(self.content, text="Analyze a pitch first, then return here to simulate alternative terms.",
                     bg=BG, fg=MUTED, font=FONT).pack(anchor="w", pady=20); return
        base=self.last_result["p"].copy(); sharks=self.last_result["sharks"]
        vars={}
        for label,key in [("Ask amount (₹ lakh)","ask"),("Equity offered (%)","equity"),("Requested valuation (₹ lakh)","valuation")]:
            row=tk.Frame(self.content,bg=PANEL); row.pack(fill="x",pady=8)
            tk.Label(row,text=label,bg=PANEL,fg=TEXT,width=28,anchor="w").pack(side="left",padx=15,pady=14)
            v=tk.DoubleVar(value=float(base[key])); vars[key]=v
            scale=tk.Scale(row,from_=0,to=max(1000,float(base[key])*3+100),resolution=1 if key!="equity" else .5,
                           orient="horizontal",variable=v,bg=PANEL,fg=CYAN,highlightthickness=0,
                           troughcolor="#263b50",length=600); scale.pack(side="left",fill="x",expand=True,padx=10)
            value=tk.Label(row,textvariable=v,bg=PANEL,fg=CYAN,width=12); value.pack(side="right",padx=15)
        result=tk.Frame(self.content,bg=BG); result.pack(fill="x",pady=18)
        def update(*_):
            for w in result.winfo_children(): w.destroy()
            p=base.copy(); p.update({k:float(v.get()) for k,v in vars.items()})
            try: pred=self.predict(p,sharks)
            except Exception as e:
                tk.Label(result,text=str(e),bg=BG,fg=AMBER).pack(anchor="w"); return
            for label,value in [("Deal probability",fmt_pct(pred["deal"])),("Offer probability",fmt_pct(pred["offer"])),
                                ("Expected valuation",fmt_money(pred["valuation"]))]:
                c=self.metric_card(result,label,value); c.pack(side="left",fill="x",expand=True,padx=6)
            eq=max(p["equity"],0.0001)
            tk.Label(result,text=f"Ask/equity implied valuation: {fmt_money(p['ask']*100/eq)}",
                     bg=BG,fg=MUTED).pack(anchor="w",pady=12)
        for v in vars.values(): v.trace_add("write",update)
        update()

    def page_dataset_insights(self):
        self.page_title("Dataset Insights", "A quick overview of the historical Shark Tank dataset.")
        metrics=[("Historical pitches",f"{len(self.df):,}"),("Industries",self.df["Industry"].nunique()),
                 ("Median ask",fmt_money(self.df["Original Ask Amount"].median())),
                 ("Median equity",f"{self.df['Original Offered Equity'].median():.1f}%")]
        row=tk.Frame(self.content,bg=BG); row.pack(fill="x",pady=10)
        for l,v in metrics:
            c=self.metric_card(row,l,v); c.pack(side="left",fill="x",expand=True,padx=5)
        self.draw_bars(self.content,self.df["Industry"].value_counts(),"Most represented industries")

    def page_model_card(self):
        self.page_title("Model Card", "Evaluation metrics stored with the trained project models.")
        if not self.meta:
            try:
                with open(ROOT/"model_metrics.json",encoding="utf-8") as f: results=json.load(f)
            except Exception: results={}
        else: results=self.meta.get("results",{})
        rows=[]
        for key, item in results.items():
            if key=="sharks": continue
            m=item.get("metrics",{})
            rows.append((key.replace("_"," ").title(), f"{m.get('accuracy','—')}",
                         f"{m.get('precision','—')}",f"{m.get('recall','—')}",
                         f"{m.get('f1','—')}",f"{m.get('roc_auc','—')}",f"{m.get('r2','—')}"))
        box=tk.Frame(self.content,bg=PANEL); box.pack(fill="both",expand=True)
        self.make_table(box,None,["Task","Accuracy","Precision","Recall","F1","ROC-AUC","R²"],rows,10)
        tk.Label(self.content,text="Individual shark predictions are ranking signals, not certain investment decisions. "
                 "Regression metrics are not directly comparable to classification metrics.",
                 bg=BG,fg=AMBER,wraplength=1000,justify="left").pack(anchor="w",pady=12)

if __name__ == "__main__":
    try:
        app = SharkTankApp()
        app.mainloop()
    except Exception:
        traceback.print_exc()
