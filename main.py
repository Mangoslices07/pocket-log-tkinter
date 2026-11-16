"""Pocket Log - a simple student expense tracker using Tkinter."""

import json
from datetime import date
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
budgets = {}
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
    sign = "-" if paise < 0 else ""
    paise = abs(paise)
    return f"{sign}\u20b9{paise // 100:,}.{paise % 100:02d}"


def parse_date(text):
    text = text.strip()
    try:
        entered = date.fromisoformat(text)
    except ValueError:
        raise ValueError("Enter a valid date in YYYY-MM-DD format.") from None
    if entered.isoformat() != text:
        raise ValueError("Use YYYY-MM-DD format, such as 2026-11-16.")
    return text


def load_data(path):
    if not path.exists():
        return [], {}
    with path.open(encoding="utf-8") as file:
        saved = json.load(file)
    # The original app saved just a list. Keep those old entries readable.
    if isinstance(saved, list):
        saved = {"expenses": saved, "budgets": {}}
    if (not isinstance(saved, dict) or not isinstance(saved.get("expenses"), list)
            or not isinstance(saved.get("budgets"), dict)):
        raise ValueError("The saved data has an invalid format.")
    for item in saved["expenses"]:
        if (not isinstance(item, dict) or not isinstance(item.get("name"), str)
                or not 1 <= len(item["name"].strip()) <= 40
                or item.get("category") not in CATEGORIES
                or type(item.get("amount_paise")) is not int
                or not 1 <= item["amount_paise"] <= 9999999999):
            raise ValueError("The saved file contains an invalid expense.")
        if item.get("date") is not None:
            if not isinstance(item["date"], str):
                raise ValueError("An expense date is invalid.")
            parse_date(item["date"])
    for month, amount in saved["budgets"].items():
        if not isinstance(month, str) or len(month) != 7:
            raise ValueError("A budget month is invalid.")
        parse_date(month + "-01")
        if type(amount) is not int or not 1 <= amount <= 9999999999:
            raise ValueError("A saved budget is invalid.")
    return saved["expenses"], saved["budgets"]


def save_data(path, entries, monthly_budgets):
    # Finish writing before replacing the old saved file.
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump({"expenses": entries, "budgets": monthly_budgets}, file, indent=2)
    temporary.replace(path)


def get_month_summary(entries, monthly_budgets, today):
    month = today.strftime("%Y-%m")
    spent = 0
    for item in entries:
        if (item.get("date") or "").startswith(month + "-"):
            spent += item["amount_paise"]
    budget = monthly_budgets.get(month)
    remaining = None if budget is None else budget - spent
    return spent, budget, remaining


def refresh_table():
    table.delete(*table.get_children())
    visible_total = 0
    shown = 0
    for index, item in enumerate(expenses):
        if filter_input.get() in ("All categories", item["category"]):
            table.insert("", "end", iid=str(index), values=(item.get("date") or "Not set",
                item["name"], item["category"], format_money(item["amount_paise"])))
            visible_total += item["amount_paise"]
            shown += 1
    total_text.set("All-time total: " + format_money(sum(item["amount_paise"] for item in expenses)))
    today = date.today()
    spent, budget, remaining = get_month_summary(expenses, budgets, today)
    month_text.set("MONTHLY BUDGET | " + today.strftime("%B %Y"))
    budget_text.set("Not set" if budget is None else format_money(budget))
    spent_text.set(format_money(spent))
    remaining_text.set("--" if remaining is None else format_money(remaining))
    if remaining is not None and remaining < 0:
        budget_notice.set("Over budget by " + format_money(-remaining))
    elif budget is None:
        budget_notice.set("Set a budget below. Monthly figures include all categories.")
    else:
        budget_notice.set("Within budget. Monthly figures include all categories.")
    status = f"Showing {shown} of {len(expenses)} expenses | Visible total: {format_money(visible_total)}"
    undated = sum(item.get("date") is None for item in expenses)
    if undated:
        status += f" | {undated} undated entry/entries excluded from monthly spending."
    status_text.set(status)


def save_changes(updated_expenses, updated_budgets=None):
    if not storage_ok:
        return False
    new_budgets = dict(budgets if updated_budgets is None else updated_budgets)
    try:
        save_data(DATA_FILE, updated_expenses, new_budgets)
    except OSError:
        messagebox.showerror("Save failed", "Could not save expenses. Your changes were not applied.")
        return False
    expenses[:] = updated_expenses
    budgets.clear()
    budgets.update(new_budgets)
    refresh_table()
    return True


def clear_fields():
    name_input.delete(0, tk.END)
    amount_input.delete(0, tk.END)
    category_input.set(CATEGORIES[0])
    date_input.delete(0, tk.END)
    date_input.insert(0, date.today().isoformat())
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
        expense_date = parse_date(date_input.get())
    except ValueError as error:
        messagebox.showwarning("Check expense", str(error))
        return
    new_expense = {"name": name, "category": category_input.get(),
                   "amount_paise": amount, "date": expense_date}
    if save_changes(expenses + [new_expense]):
        clear_fields()
        last_row = str(len(expenses) - 1)
        if table.exists(last_row):
            table.see(last_row)


def set_budget():
    if not storage_ok:
        return
    updated = dict(budgets)
    month = date.today().strftime("%Y-%m")
    text = budget_input.get().strip()
    try:
        if text:
            updated[month] = parse_amount(text)
        else:
            updated.pop(month, None)
    except ValueError as error:
        messagebox.showwarning("Check budget", str(error))
        return
    save_changes(list(expenses), updated)


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
    root.geometry("1080x790")
    root.minsize(1000, 750)
    root.configure(bg=CREAM)
    total_text = tk.StringVar(value=format_money(0))
    status_text = tk.StringVar()
    month_text = tk.StringVar()
    budget_text, spent_text, remaining_text = tk.StringVar(), tk.StringVar(), tk.StringVar()
    budget_notice = tk.StringVar()
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
    tk.Label(form, text="Date (YYYY-MM-DD)", bg=PAPER, fg=BLACK).pack(anchor="w")
    date_input = ttk.Entry(form, width=24, font=("Arial", 11))
    date_input.insert(0, date.today().isoformat())
    date_input.pack(fill="x", pady=(5, 16))
    tk.Label(form, text="Category", bg=PAPER, fg=BLACK).pack(anchor="w")
    category_input = ttk.Combobox(form, values=CATEGORIES, state="readonly", width=22)
    category_input.set(CATEGORIES[0])
    category_input.pack(fill="x", pady=(5, 22))
    add_button = ttk.Button(form, text="Add expense", style="Orange.TButton", command=add_expense)
    add_button.pack(fill="x")
    ttk.Button(form, text="Clear fields", command=clear_fields).pack(fill="x", pady=(10, 0))

    # Current month's budget, followed by the expense table.
    ledger = tk.Frame(content, bg=CREAM)
    ledger.grid(row=0, column=1, sticky="nsew")
    summary = tk.Frame(ledger, bg=BLACK, padx=20, pady=18)
    summary.pack(fill="x", pady=(0, 22))
    tk.Label(summary, textvariable=month_text, bg=BLACK, fg=CREAM,
             font=("Arial", 10)).pack(anchor="w")
    numbers = tk.Frame(summary, bg=BLACK)
    numbers.pack(fill="x", pady=(12, 0))
    for column, label, variable in [(0, "Budget", budget_text),
                                    (1, "Spent", spent_text), (2, "Remaining", remaining_text)]:
        numbers.columnconfigure(column, weight=1, uniform="money")
        tk.Label(numbers, text=label, bg=BLACK, fg=CREAM).grid(row=0, column=column, sticky="w")
        tk.Label(numbers, textvariable=variable, bg=BLACK, fg=ORANGE,
                 font=("Arial", 17, "bold")).grid(row=1, column=column, sticky="w", pady=(4, 0))
    tk.Label(ledger, textvariable=budget_notice, bg=CREAM, fg=BLACK,
             wraplength=650, justify="left").pack(anchor="w", pady=(0, 10))
    budget_form = tk.Frame(ledger, bg=CREAM)
    budget_form.pack(fill="x", pady=(0, 4))
    tk.Label(budget_form, text="Monthly budget (Rs.)", bg=CREAM, fg=BLACK).pack(side="left")
    budget_input = ttk.Entry(budget_form, width=14)
    budget_input.pack(side="left", padx=10)
    budget_button = ttk.Button(budget_form, text="Save budget", command=set_budget)
    budget_button.pack(side="left")
    tk.Label(ledger, text="Leave the budget field empty and save to remove this month's budget.",
             bg=CREAM, fg=MUTED, font=("Arial", 9)).pack(anchor="w", pady=(0, 16))
    toolbar = tk.Frame(ledger, bg=CREAM)
    toolbar.pack(fill="x", pady=(0, 10))
    tk.Label(toolbar, text="Expenses", bg=CREAM, fg=BLACK,
             font=("Arial", 12, "bold")).pack(side="left")
    filter_input = ttk.Combobox(toolbar, values=["All categories"] + CATEGORIES,
                               state="readonly", width=18)
    filter_input.set("All categories")
    filter_input.pack(side="right")
    filter_input.bind("<<ComboboxSelected>>", lambda event: refresh_table())
    table_frame = tk.Frame(ledger, bg=PAPER)
    table_frame.pack(fill="both", expand=True)
    table = ttk.Treeview(table_frame, columns=("date", "name", "category", "amount"),
                         show="headings", selectmode="browse", height=6)
    for column, title, width, anchor in [
        ("date", "Date", 105, "w"), ("name", "Expense", 145, "w"),
        ("category", "Category", 95, "w"), ("amount", "Amount", 130, "e")
    ]:
        table.heading(column, text=title, anchor=anchor)
        table.column(column, width=width, minwidth=width, anchor=anchor)
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    scrollbar.pack(side="right", fill="y")
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side="left", fill="both", expand=True)
    ttk.Button(ledger, text="Delete selected expense", command=delete_expense).pack(
        anchor="w", pady=(14, 0))
    tk.Label(ledger, textvariable=total_text, bg=CREAM, fg=BLACK,
             font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
    tk.Label(page, textvariable=status_text, bg=CREAM, fg=MUTED,
             font=("Arial", 10), wraplength=1000, justify="left").pack(anchor="w")

    # Reload saved data and start the event loop.
    try:
        expenses, budgets = load_data(DATA_FILE)
        refresh_table()
        current_budget = budgets.get(date.today().strftime("%Y-%m"))
        if current_budget is not None:
            budget_input.insert(0, f"{Decimal(current_budget) / 100:.2f}")
    except (OSError, ValueError, UnicodeError):
        storage_ok = False
        add_button.state(["disabled"])
        budget_button.state(["disabled"])
        status_text.set("Could not read expenses.json. The saved file has not been changed.")
        messagebox.showerror("Saved data error", "Check or rename expenses.json, then restart the app.")
    name_input.focus_set()
    root.mainloop()
