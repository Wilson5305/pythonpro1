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


class LiveStudentSearch:
    """Reusable autocomplete search field for student lookup screens."""

    def __init__(self, parent, student_model, on_select, width=32):
        self.parent = parent
        self.student_model = student_model
        self.on_select = on_select
        self.placeholder = "Search students..."
        self.var = tk.StringVar()
        self.frame = tk.Frame(parent, bg=parent.cget("bg") or COLORS["bg"])

        self.entry = make_entry(self.frame, self.var, width=width)
        self.entry.pack(fill="x")
        self.entry.configure(exportselection=False)
        self._set_placeholder()

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Down>", lambda e: self._move_highlight(1))
        self.entry.bind("<Up>", lambda e: self._move_highlight(-1))
        self.entry.bind("<Return>", lambda e: self._select_highlighted())
        self.entry.bind("<Escape>", lambda e: self._close_dropdown())

        self.results = []
        self.highlight_index = -1
        self.dropdown_frame = tk.Frame(parent, bg=COLORS["card_bg"], bd=1, relief="solid")
        self.listbox = tk.Listbox(
            self.dropdown_frame, height=8, activestyle="none",
            bg=COLORS["card_bg"], fg=COLORS["text_dark"],
            font=FONTS["label"], bd=0, highlightthickness=0,
            exportselection=False
        )
        self.listbox.pack(fill="both")
        self.listbox.bind("<ButtonRelease-1>", self._on_listbox_click)
        self.listbox.bind("<Motion>", self._on_listbox_motion)

        self._close_dropdown()
        root = parent.winfo_toplevel()
        root.bind("<Button-1>", self._handle_global_click, add="+")

    def _set_placeholder(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.placeholder)
        self.entry.configure(fg=COLORS["muted"])

    def _on_focus_in(self, _event=None):
        value = self.var.get().strip()
        if value == self.placeholder or value == "":
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=COLORS["text_dark"])

    def _on_focus_out(self, _event=None):
        value = self.var.get().strip()
        if value == "":
            self._set_placeholder()
            self._close_dropdown()

    def _current_query(self):
        value = self.var.get().strip()
        if value == self.placeholder:
            return ""
        return value

    def _handle_global_click(self, event):
        if not self.dropdown_frame.winfo_ismapped():
            return
        if self.entry.winfo_containing(event.x_root, event.y_root) or self.listbox.winfo_containing(event.x_root, event.y_root):
            return
        self._close_dropdown()

    def _close_dropdown(self):
        self.listbox.delete(0, tk.END)
        self.highlight_index = -1
        if self.dropdown_frame.winfo_ismapped():
            self.dropdown_frame.pack_forget()

    def _on_key_release(self, _event=None):
        query = self._current_query()
        if not query:
            self._close_dropdown()
            return
        self._update_suggestions(query)

    def _update_suggestions(self, query):
        results = self.student_model.search_students(query)[:10]
        self.results = results
        self.listbox.delete(0, tk.END)
        if not results:
            self.listbox.insert(tk.END, "No students found")
            self.listbox.config(state="disabled")
            self.dropdown_frame.pack(fill="x", pady=(4, 0))
            self.highlight_index = -1
            return

        self.listbox.config(state="normal")
        for student in results:
            text = f"{student['student_name']}\n{student['register_id']} • {student['course_name']}"
            self.listbox.insert(tk.END, text)
        self.dropdown_frame.pack(fill="x", pady=(4, 0))

    def _move_highlight(self, direction):
        if not self.results:
            return
        total = len(self.results)
        if self.highlight_index == -1:
            self.highlight_index = 0 if direction > 0 else total - 1
        else:
            self.highlight_index = (self.highlight_index + direction) % total
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.highlight_index)
        self.listbox.see(self.highlight_index)

    def _on_listbox_motion(self, event):
        if not self.results:
            return
        index = self.listbox.nearest(event.y)
        if index is not None and index >= 0:
            self.highlight_index = index
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)

    def _select_highlighted(self):
        if not self.results:
            return
        if self.highlight_index < 0:
            self.highlight_index = 0
        if self.highlight_index >= len(self.results):
            self.highlight_index = len(self.results) - 1
        self._choose_student(self.results[self.highlight_index])

    def _on_listbox_click(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        self._choose_student(self.results[selection[0]])

    def _choose_student(self, student):
        self.var.set(student["student_name"])
        self.entry.configure(fg=COLORS["text_dark"])
        self._close_dropdown()
        self.on_select(student)


def show_status_badge(parent, status, bg_card=None):
    """Returns a small colored label representing payment status (Pending/Fully Paid)."""
    color = COLORS["secondary"] if status == "Fully Paid" else COLORS["warning"]
    lbl = tk.Label(
        parent, text=status, font=FONTS["small"], fg="white", bg=color,
        padx=8, pady=2
    )
    return lbl
