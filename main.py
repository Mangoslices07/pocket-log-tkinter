"""Pocket Log - a simple student expense tracker using Tkinter."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

# Colours and the location of the saved expenses.
CREAM, PAPER, ORANGE, BLACK = "#FFF3DF", "#FFFAF2", "#F47735", "#191919"
MUTED, BORDER = "#6B5545", "#D5C4AC"
CATEGORIES = ["Food", "Travel", "Study", "Shopping", "Other"]
DATA_FILE = Path(__file__).resolve().parent / "expenses.json"
expenses = []
storage_ok = True


def parse_amount(text):
    # Store whole paise, so Rs. 12.50 becomes 1250.
    try:
        amount = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("Enter a valid amount, such as 120 or 49.50.") from None
    if not amount.is_finite() or not 0 < amount <= Decimal("99999999.99"):
        raise ValueError("Enter an amount from Rs. 0.01 to Rs. 99,999,999.99.")
    if amount * 100 != (amount * 100).to_integral_value():
        raise ValueError("Use no more than two decimal places.")
    return int(amount * 100)


def format_money(paise):
    return f"\u20b9{paise // 100:,}.{paise % 100:02d}"


def load_expenses(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file:
        saved = json.load(file)
    if not isinstance(saved, list):
        raise ValueError("The saved data is not a list.")
    for item in saved:
        if (not isinstance(item, dict) or not isinstance(item.get("name"), str)
                or not 1 <= len(item["name"].strip()) <= 40
                or item.get("category") not in CATEGORIES
                or type(item.get("amount_paise")) is not int
                or not 1 <= item["amount_paise"] <= 9999999999):
            raise ValueError("The saved file contains an invalid expense.")
    return saved


def save_expenses(path, entries):
    # Finish writing before replacing the old saved file.
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)
    temporary.replace(path)


def refresh_table():
    table.delete(*table.get_children())
    total = 0
    for index, item in enumerate(expenses):
        table.insert("", "end", iid=str(index), values=(
            item["name"], item["category"], format_money(item["amount_paise"])))
        total += item["amount_paise"]
    total_text.set(format_money(total))
    status_text.set(f"{len(expenses)} expense(s). Changes are saved automatically.")


def save_changes(updated_expenses):
    if not storage_ok:
        return False
    try:
        save_expenses(DATA_FILE, updated_expenses)
    except OSError:
        messagebox.showerror("Save failed", "Could not save expenses. Your changes were not applied.")
        return False
    expenses[:] = updated_expenses
    refresh_table()
    return True


def clear_fields():
    name_input.delete(0, tk.END)
    amount_input.delete(0, tk.END)
    category_input.set(CATEGORIES[0])
    name_input.focus_set()


def add_expense():
    if not storage_ok:
        return
    name = name_input.get().strip()
    if not 1 <= len(name) <= 40:
        messagebox.showwarning("Check name", "Enter a name with 1 to 40 characters.")
        return
    try:
        amount = parse_amount(amount_input.get())
    except ValueError as error:
        messagebox.showwarning("Check amount", str(error))
        return
    new_expense = {"name": name, "category": category_input.get(), "amount_paise": amount}
    if save_changes(expenses + [new_expense]):
        clear_fields()
        table.see(str(len(expenses) - 1))


def delete_expense():
    selection = table.selection()
    if not selection:
        messagebox.showinfo("Select a row", "Select an expense from the table first.")
        return
    index = int(selection[0])
    if messagebox.askyesno("Delete expense", "Delete the selected expense?"):
        save_changes(expenses[:index] + expenses[index + 1:])


if __name__ == "__main__":
    # Main window and theme.
    root = tk.Tk()
    root.title("Pocket Log | Student Expense Tracker")
    root.geometry("960x640")
    root.minsize(850, 590)
    root.configure(bg=CREAM)
    total_text = tk.StringVar(value=format_money(0))
    status_text = tk.StringVar()
    style = ttk.Style()
    style.theme_use("clam")  # Allows coloured buttons on macOS and Windows.
    style.configure("TEntry", fieldbackground=PAPER, foreground=BLACK, padding=8)
    style.configure("TCombobox", fieldbackground=PAPER, foreground=BLACK, padding=7)
    style.map("TCombobox", fieldbackground=[("readonly", PAPER)], foreground=[("readonly", BLACK)])
    style.configure("TButton", background=PAPER, foreground=BLACK, padding=9)
    style.configure("Orange.TButton", background=ORANGE, foreground=BLACK,
                    font=("Arial", 11, "bold"), padding=12)
    style.map("Orange.TButton", background=[("active", "#E96922")])
    style.configure("Treeview", background=PAPER, fieldbackground=PAPER,
                    foreground=BLACK, rowheight=35, font=("Arial", 11))
    style.configure("Treeview.Heading", background="#F9E7CB", foreground=BLACK,
                    font=("Arial", 10, "bold"), padding=9)
    style.map("Treeview", background=[("selected", ORANGE)], foreground=[("selected", BLACK)])

    # Heading.
    page = tk.Frame(root, bg=CREAM, padx=28, pady=25)
    page.pack(fill="both", expand=True)
    tk.Label(page, text="STUDENT EXPENSE TRACKER", bg=CREAM, fg=MUTED,
             font=("Arial", 10)).pack(anchor="w")
    tk.Label(page, text="Pocket Log.", bg=CREAM, fg=BLACK,
             font=("Arial", 30, "bold")).pack(anchor="w", pady=(5, 3))
    tk.Label(page, text="Keep track of the little things.", bg=CREAM, fg=MUTED).pack(anchor="w")
    content = tk.Frame(page, bg=CREAM)
    content.pack(fill="both", expand=True, pady=24)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=1)

    # Form on the left.
    form = tk.Frame(content, bg=PAPER, padx=20, pady=20,
                    highlightbackground=BORDER, highlightthickness=1)
    form.grid(row=0, column=0, sticky="nsew", padx=(0, 24))
    tk.Label(form, text="Add an expense", bg=PAPER, fg=BLACK,
             font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 20))
    tk.Label(form, text="Expense name", bg=PAPER, fg=BLACK).pack(anchor="w")
    name_input = ttk.Entry(form, width=24, font=("Arial", 11))
    name_input.pack(fill="x", pady=(5, 16))
    tk.Label(form, text="Amount (Rs.)", bg=PAPER, fg=BLACK).pack(anchor="w")
    amount_input = ttk.Entry(form, width=24, font=("Arial", 11))
    amount_input.pack(fill="x", pady=(5, 16))
    tk.Label(form, text="Category", bg=PAPER, fg=BLACK).pack(anchor="w")
    category_input = ttk.Combobox(form, values=CATEGORIES, state="readonly", width=22)
    category_input.set(CATEGORIES[0])
    category_input.pack(fill="x", pady=(5, 22))
    add_button = ttk.Button(form, text="Add expense", style="Orange.TButton", command=add_expense)
    add_button.pack(fill="x")
    ttk.Button(form, text="Clear fields", command=clear_fields).pack(fill="x", pady=(10, 0))

    # Total and table on the right.
    ledger = tk.Frame(content, bg=CREAM)
    ledger.grid(row=0, column=1, sticky="nsew")
    summary = tk.Frame(ledger, bg=BLACK, padx=20, pady=18)
    summary.pack(fill="x", pady=(0, 22))
    tk.Label(summary, text="Total spent", bg=BLACK, fg=CREAM).pack(anchor="w")
    tk.Label(summary, textvariable=total_text, bg=BLACK, fg=ORANGE,
             font=("Arial", 28, "bold")).pack(anchor="w", pady=(5, 0))
    tk.Label(ledger, text="Recent expenses", bg=CREAM, fg=BLACK,
             font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
    table_frame = tk.Frame(ledger, bg=PAPER)
    table_frame.pack(fill="both", expand=True)
    table = ttk.Treeview(table_frame, columns=("name", "category", "amount"),
                         show="headings", selectmode="browse", height=6)
    for column, title, width, anchor in [
        ("name", "Expense", 170, "w"), ("category", "Category", 100, "w"),
        ("amount", "Amount", 150, "e")
    ]:
        table.heading(column, text=title, anchor=anchor)
        table.column(column, width=width, minwidth=width, anchor=anchor)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    scrollbar.pack(side="right", fill="y")
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side="left", fill="both", expand=True)
    ttk.Button(ledger, text="Delete selected expense", command=delete_expense).pack(
        anchor="w", pady=(14, 0))
    tk.Label(page, textvariable=status_text, bg=CREAM, fg=MUTED,
             font=("Arial", 10), wraplength=760, justify="left").pack(anchor="w")

    # Reload saved data and start the event loop.
    try:
        expenses = load_expenses(DATA_FILE)
        refresh_table()
    except (OSError, ValueError, UnicodeError):
        storage_ok = False
        add_button.state(["disabled"])
        status_text.set("Could not read expenses.json. The saved file has not been changed.")
        messagebox.showerror("Saved data error", "Check or rename expenses.json, then restart the app.")
    name_input.focus_set()
    root.mainloop()
