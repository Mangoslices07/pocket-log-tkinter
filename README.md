# Pocket Log

A simple student expense tracker built with **Python and Tkinter**. The design uses a cream background, orange accents, and a black Pocket Log heading.

## Run

Open this folder in VS Code, select a Python 3 interpreter, and run:

```bash
python3 main.py
```

On Windows, use `python main.py` if `python3` is unavailable. The application uses only the Python standard library; there is no `pip install` step. The Python installation must include Tkinter. Check it with `python3 -m tkinter` if the window does not open.

## Features

- Add an expense name, date, rupee amount, and category.
- Use today's date or enter another valid date as `YYYY-MM-DD`.
- Filter the table by category and see the total for the displayed rows.
- Set a budget for the current calendar month and see spending and the remaining amount.
- See a warning when monthly spending exceeds the budget.
- View expenses in a scrollable table and see the running total.
- Select and delete an expense after confirmation.
- Clear the form without deleting saved expenses.
- Save expenses and monthly budgets automatically in `expenses.json` beside `main.py`.
- Reload saved entries when the app is opened again.
- Validate empty names, calendar dates, invalid numbers, nonpositive amounts, and fractions smaller than one paise.

No internet connection, login, database server, or external Python package is required to run the app. It is a local desktop GUI project.

## Files

- `main.py`: interface, event handlers, validation, and JSON saving.
- `expenses.json`: personal entries, created when an expense is first saved. It is excluded from Git.

The local submission folder also contains `report.html` (the editable report source) and `RA2511026010635.pdf` (the two-page report). These submission documents are not included in the public source repository. To update the report, edit the HTML in a text editor, open it in a browser, and print to PDF using A4 paper, 100% scale, and browser headers/footers disabled.

## Saved data

The app starts empty. Example entries for a demonstration are Lunch / Food / 120, Bus fare / Travel / 40, and Notebooks / Study / 90; the total is Rs. 250.00.

The budget summary always refers to the current calendar month on your computer. It includes all categories even while the table is filtered. Older or future dated expenses still count toward the all-time total, but only entries dated in the current month count toward its spending. Budgets are saved separately for each month. Set a new budget when a new month starts. To remove the current month's budget, leave its field empty and click Save budget.

Older `expenses.json` files from the first version remain readable. Their entries appear with the date `Not set`; they count toward the all-time and visible totals but not monthly spending. The app never invents dates for older expenses. Saving a change upgrades the file to store both expenses and budgets. Keep your existing data file in the same folder when replacing the Python source.

If a saved file is damaged, the app displays a warning and will not overwrite it. Close the app, check or rename `expenses.json`, then restart. Keep a copy of that file if you want to back up your expenses. Use one app window at a time.
