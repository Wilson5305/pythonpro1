"""
ui_helpers.py
-------------
Shared visual style constants and small reusable widget factory functions
so every screen in the application looks consistent and "modern/professional"
as required by the spec, without duplicating styling code everywhere.
"""

import tkinter as tk
from tkinter import ttk


# ---------------------------------------------------------------------------
# Color palette / fonts - centralized so the whole app is easy to re-theme.
# ---------------------------------------------------------------------------
COLORS = {
    "primary": "#1F4E8C",       # deep blue - headers, primary buttons
    "primary_dark": "#163A66",
    "secondary": "#2E9E6B",     # green - success / save actions
    "danger": "#D9534F",        # red - delete / destructive actions
    "warning": "#E8A33D",       # amber - pending status
    "bg": "#F4F6F9",            # app background
    "card_bg": "#FFFFFF",
    "sidebar_bg": "#16223B",
    "sidebar_hover": "#22335A",
    "text_dark": "#1E2A38",
    "text_light": "#FFFFFF",
    "muted": "#6B7785",
    "border": "#D7DCE3",
    "row_alt": "#F0F3F7",
}

FONTS = {
    "title": ("Segoe UI", 20, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "label": ("Segoe UI", 10),
    "label_bold": ("Segoe UI", 10, "bold"),
    "button": ("Segoe UI", 10, "bold"),
    "sidebar": ("Segoe UI", 11),
    "small": ("Segoe UI", 9),
}


def configure_styles(root):
    """
    Configures ttk styles globally. Called once from main.py after the
    root Tk window is created.
    """
    style = ttk.Style(root)
    # 'clam' theme allows background/foreground colors to actually apply
    # on most platforms (the default theme ignores many color overrides).
    style.theme_use("clam")

    style.configure("Treeview",
                     background=COLORS["card_bg"],
                     foreground=COLORS["text_dark"],
                     fieldbackground=COLORS["card_bg"],
                     rowheight=28,
                     font=FONTS["label"])
    style.configure("Treeview.Heading",
                     background=COLORS["primary"],
                     foreground=COLORS["text_light"],
                     font=FONTS["label_bold"],
                     relief="flat")
    style.map("Treeview.Heading", background=[("active", COLORS["primary_dark"])])
    style.map("Treeview", background=[("selected", COLORS["primary"])],
              foreground=[("selected", COLORS["text_light"])])

    style.configure("TCombobox", font=FONTS["label"])
    style.configure("Horizontal.TProgressbar", troughcolor=COLORS["bg"],
                     background=COLORS["secondary"])
    return style


def make_button(parent, text, command, bg=None, fg=None, width=16, height=1):
    """Factory for a consistently-styled flat button."""
    bg = bg or COLORS["primary"]
    fg = fg or COLORS["text_light"]
    btn = tk.Button(
        parent, text=text, command=command, bg=bg, fg=fg,
        font=FONTS["button"], relief="flat", bd=0, cursor="hand2",
        activebackground=_darken(bg), activeforeground=fg,
        width=width, height=height, padx=8, pady=6
    )
    # subtle hover effect
    btn.bind("<Enter>", lambda e: btn.config(bg=_darken(bg)))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def _darken(hex_color, factor=0.85):
    """Returns a slightly darker version of a hex color for hover states."""
    hex_color = hex_color.lstrip("#")
    try:
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return hex_color
    r, g, b = (max(0, int(c * factor)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def make_card(parent, padx=20, pady=20):
    """Returns a white 'card' frame with a subtle border, used for forms/panels."""
    outer = tk.Frame(parent, bg=COLORS["border"])
    inner = tk.Frame(outer, bg=COLORS["card_bg"])
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    card = tk.Frame(inner, bg=COLORS["card_bg"], padx=padx, pady=pady)
    card.pack(fill="both", expand=True)
    return outer, card


def make_label(parent, text, bold=False, size=None, color=None, bg=None):
    """Factory for a consistently-styled label."""
    font = FONTS["label_bold"] if bold else FONTS["label"]
    if size:
        font = (font[0], size, font[2] if len(font) > 2 else "normal")
    return tk.Label(
        parent, text=text, font=font,
        fg=color or COLORS["text_dark"], bg=bg or COLORS["card_bg"]
    )


def make_entry(parent, textvariable=None, width=30):
    """Factory for a consistently-styled entry field."""
    return tk.Entry(
        parent, textvariable=textvariable, font=FONTS["label"], width=width,
        relief="solid", bd=1, highlightthickness=1,
        highlightbackground=COLORS["border"], highlightcolor=COLORS["primary"]
    )


def show_status_badge(parent, status, bg_card=None):
    """Returns a small colored label representing payment status (Pending/Fully Paid)."""
    color = COLORS["secondary"] if status == "Fully Paid" else COLORS["warning"]
    lbl = tk.Label(
        parent, text=status, font=FONTS["small"], fg="white", bg=color,
        padx=8, pady=2
    )
    return lbl
