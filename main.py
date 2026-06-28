from fastmcp import FastMCP
from datetime import datetime, date
from typing import Optional
from enum import Enum
import sqlite3
import os

mcp = FastMCP("expense-tracker")

DB_PATH = os.getenv("DB_PATH", "expenses.db")


class Category(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    ENTERTAINMENT = "Entertainment"
    BILLS = "Bills"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    OTHER = "Other"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


@mcp.tool
def add_expense(
    amount: float,
    category: str,
    description: str,
    expense_date: Optional[str] = None,
) -> dict:
    """Add a new expense."""
    if amount <= 0:
        raise ValueError("Amount must be positive.")

    try:
        Category(category)
    except ValueError:
        valid = [c.value for c in Category]
        raise ValueError(f"Invalid category. Valid: {', '.join(valid)}")

    if expense_date:
        try:
            datetime.strptime(expense_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")
    else:
        expense_date = date.today().isoformat()

    import uuid
    expense_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (id, amount, category, description, date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (expense_id, amount, category, description, expense_date, created_at),
    )
    conn.commit()
    conn.close()

    return {
        "id": expense_id,
        "amount": amount,
        "category": category,
        "description": description,
        "date": expense_date,
        "created_at": created_at,
    }


@mcp.tool
def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """List expenses with optional filters."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params: list = []

    if category:
        try:
            Category(category)
        except ValueError:
            valid = [c.value for c in Category]
            raise ValueError(f"Invalid category. Valid: {', '.join(valid)}")
        query += " AND category = ?"
        params.append(category)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(r) for r in rows]


@mcp.tool
def get_expense(expense_id: str) -> dict:
    """Get a single expense by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()

    if row is None:
        raise ValueError(f"Expense with ID '{expense_id}' not found.")
    return dict(row)


@mcp.tool
def update_expense(
    expense_id: str,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    expense_date: Optional[str] = None,
) -> dict:
    """Update an existing expense."""
    conn = get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Expense with ID '{expense_id}' not found.")

    updates: list[str] = []
    params: list = []

    if amount is not None:
        if amount <= 0:
            conn.close()
            raise ValueError("Amount must be positive.")
        updates.append("amount = ?")
        params.append(amount)

    if category is not None:
        try:
            Category(category)
        except ValueError:
            valid = [c.value for c in Category]
            conn.close()
            raise ValueError(f"Invalid category. Valid: {', '.join(valid)}")
        updates.append("category = ?")
        params.append(category)

    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if expense_date is not None:
        try:
            datetime.strptime(expense_date, "%Y-%m-%d")
        except ValueError:
            conn.close()
            raise ValueError("Date must be in YYYY-MM-DD format.")
        updates.append("date = ?")
        params.append(expense_date)

    if updates:
        params.append(expense_id)
        conn.execute(
            f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()

    updated = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    return dict(updated)


@mcp.tool
def delete_expense(expense_id: str) -> dict:
    """Delete an expense by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"Expense with ID '{expense_id}' not found.")

    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

    return {"deleted": True, "expense": dict(row)}


@mcp.tool
def get_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Get expense summary (total, count, average, breakdown by category)."""
    conn = get_db()

    date_filter = ""
    params: list = []
    if start_date:
        date_filter += " AND date >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND date <= ?"
        params.append(end_date)

    total_row = conn.execute(
        f"SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expenses WHERE 1=1{date_filter}",
        params,
    ).fetchone()

    count = total_row["count"]
    total = total_row["total"]

    if count == 0:
        conn.close()
        return {"total": 0, "count": 0, "average": 0, "by_category": {}}

    cat_rows = conn.execute(
        f"SELECT category, COUNT(*) as count, SUM(amount) as total FROM expenses WHERE 1=1{date_filter} GROUP BY category",
        params,
    ).fetchall()
    conn.close()

    by_category = {
        r["category"]: {"total": round(r["total"], 2), "count": r["count"]}
        for r in cat_rows
    }

    return {
        "total": round(total, 2),
        "count": count,
        "average": round(total / count, 2),
        "by_category": by_category,
    }


@mcp.tool
def get_expenses_by_category() -> dict:
    """Group all expenses by category."""
    conn = get_db()
    rows = conn.execute(
        "SELECT category, id, amount, description, date FROM expenses ORDER BY category, date DESC"
    ).fetchall()
    conn.close()

    grouped: dict[str, list[dict]] = {}
    for r in rows:
        cat = r["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "id": r["id"],
            "amount": r["amount"],
            "description": r["description"],
            "date": r["date"],
        })
    return grouped


@mcp.resource("expenses://summary")
def summary_resource() -> dict:
    """Overall expense summary resource."""
    return get_summary()


@mcp.resource("expenses://category/{category}")
def category_resource(category: str) -> dict:
    """Expenses for a specific category resource."""
    try:
        Category(category)
    except ValueError:
        valid = [c.value for c in Category]
        raise ValueError(f"Invalid category. Valid: {', '.join(valid)}")

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC",
        (category,),
    ).fetchall()
    total_row = conn.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM expenses WHERE category = ?",
        (category,),
    ).fetchone()
    conn.close()

    return {
        "category": category,
        "total": round(total_row["total"], 2),
        "count": total_row["count"],
        "expenses": [dict(r) for r in rows],
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    mcp.run(transport="http", host="0.0.0.0", port=port)
