import sqlite3
import os
from datetime import date, datetime
from fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")

mcp = FastMCP("expenses-tracker")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL CHECK(amount > 0),
            category_id INTEGER NOT NULL,
            description TEXT DEFAULT '',
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        );

        INSERT OR IGNORE INTO categories (name, type) VALUES ('Food & Drink', 'expense');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Transport', 'expense');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Shopping', 'expense');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Entertainment', 'expense');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Bills & Utilities', 'expense');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Salary', 'income');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Freelance', 'income');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Investment', 'income');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Other Income', 'income');
        INSERT OR IGNORE INTO categories (name, type) VALUES ('Other Expense', 'expense');
    """)
    conn.commit()
    conn.close()


init_db()


# ─── Category Tools ───────────────────────────────────────────────────────────


@mcp.tool
def add_category(name: str, type: str) -> str:
    """Add a new expense or income category."""
    if type not in ("expense", "income"):
        return "Error: type must be 'expense' or 'income'"
    conn = get_db()
    try:
        conn.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type))
        conn.commit()
        return f"Category '{name}' added"
    except sqlite3.IntegrityError:
        return f"Error: category '{name}' already exists"
    finally:
        conn.close()


@mcp.tool
def list_categories(type: str = "") -> list[dict]:
    """List all categories. Optionally filter by type ('expense' or 'income')."""
    conn = get_db()
    if type:
        rows = conn.execute(
            "SELECT id, name, type FROM categories WHERE type = ? ORDER BY name",
            (type,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, type FROM categories ORDER BY type, name"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@mcp.tool
def update_category(id: int, name: str | None = None, type: str | None = None) -> str:
    """Update a category's name and/or type."""
    conn = get_db()
    fields = []
    params = []
    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if type is not None:
        if type not in ("expense", "income"):
            conn.close()
            return "Error: type must be 'expense' or 'income'"
        fields.append("type = ?")
        params.append(type)
    if not fields:
        conn.close()
        return "Error: nothing to update"
    params.append(id)
    try:
        conn.execute(f"UPDATE categories SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
        if conn.total_changes == 0:
            conn.close()
            return "Error: category not found"
        conn.close()
        return f"Category #{id} updated"
    except sqlite3.IntegrityError:
        conn.close()
        return f"Error: category name '{name}' already exists"
    except Exception as e:
        conn.close()
        return f"Error: {e}"


@mcp.tool
def delete_category(id: int) -> str:
    """Delete a category. Fails if transactions reference it."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM categories WHERE id = ?", (id,))
        conn.commit()
        if conn.total_changes == 0:
            conn.close()
            return "Error: category not found"
        conn.close()
        return f"Category #{id} deleted"
    except sqlite3.IntegrityError:
        conn.close()
        return "Error: cannot delete category with existing transactions"
    except Exception as e:
        conn.close()
        return f"Error: {e}"


# ─── Transaction Tools ────────────────────────────────────────────────────────


@mcp.tool
def add_transaction(
    amount: float, category_id: int, description: str = "", date: str = "", type: str = "expense"
) -> str:
    """Add an expense or income transaction. Date format: YYYY-MM-DD (defaults to today)."""
    if amount <= 0:
        return "Error: amount must be positive"
    if type not in ("expense", "income"):
        return "Error: type must be 'expense' or 'income'"
    if not date:
        date = datetime.today().strftime("%Y-%m-%d")
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO transactions (amount, category_id, description, date, type) VALUES (?, ?, ?, ?, ?)",
            (amount, category_id, description, date, type),
        )
        conn.commit()
        tx_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return f"Transaction #{tx_id} added: {type} of {amount} on {date}"
    except sqlite3.IntegrityError:
        conn.close()
        return "Error: invalid category_id"
    except Exception as e:
        conn.close()
        return f"Error: {e}"


@mcp.tool
def list_transactions(
    start_date: str = "",
    end_date: str = "",
    category_id: int = 0,
    type: str = "",
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List transactions with optional filters. Date format: YYYY-MM-DD."""
    query = """
        SELECT t.id, t.amount, t.description, t.date, t.type,
               c.id AS category_id, c.name AS category_name
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND t.date <= ?"
        params.append(end_date)
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if type:
        query += " AND t.type = ?"
        params.append(type)
    query += " ORDER BY t.date DESC, t.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@mcp.tool
def update_transaction(
    id: int,
    amount: float | None = None,
    category_id: int | None = None,
    description: str | None = None,
    date: str | None = None,
    type: str | None = None,
) -> str:
    """Update a transaction. Only provided fields are changed."""
    if amount is not None and amount <= 0:
        return "Error: amount must be positive"
    if type is not None and type not in ("expense", "income"):
        return "Error: type must be 'expense' or 'income'"
    conn = get_db()
    fields = []
    params = []
    if amount is not None:
        fields.append("amount = ?")
        params.append(amount)
    if category_id is not None:
        fields.append("category_id = ?")
        params.append(category_id)
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if date is not None:
        fields.append("date = ?")
        params.append(date)
    if type is not None:
        fields.append("type = ?")
        params.append(type)
    if not fields:
        conn.close()
        return "Error: nothing to update"
    params.append(id)
    conn.execute(f"UPDATE transactions SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    if conn.total_changes == 0:
        conn.close()
        return "Error: transaction not found"
    conn.close()
    return f"Transaction #{id} updated"


@mcp.tool
def delete_transaction(id: int) -> str:
    """Delete a transaction by ID."""
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id = ?", (id,))
    conn.commit()
    if conn.total_changes == 0:
        conn.close()
        return "Error: transaction not found"
    conn.close()
    return f"Transaction #{id} deleted"


# ─── Summary / Report Tools ────────────────────────────────────────────────────


@mcp.tool
def get_summary(start_date: str = "", end_date: str = "") -> dict:
    """Get income/expense summary. Date format: YYYY-MM-DD. Defaults to current month."""
    if not start_date and not end_date:
        today = date.today()
        start_date = today.replace(day=1).isoformat()
        end_date = today.isoformat()
    conn = get_db()
    totals = conn.execute(
        """SELECT type, COALESCE(SUM(amount), 0) AS total
           FROM transactions
           WHERE date >= ? AND date <= ?
           GROUP BY type""",
        (start_date, end_date),
    ).fetchall()
    by_category = conn.execute(
        """SELECT t.type, c.name AS category, COALESCE(SUM(t.amount), 0) AS total
           FROM transactions t
           JOIN categories c ON t.category_id = c.id
           WHERE t.date >= ? AND t.date <= ?
           GROUP BY t.type, c.name
           ORDER BY t.type, total DESC""",
        (start_date, end_date),
    ).fetchall()
    transaction_count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE date >= ? AND date <= ?",
        (start_date, end_date),
    ).fetchone()[0]
    conn.close()
    totals_dict = {r["type"]: r["total"] for r in totals}
    total_expenses = totals_dict.get("expense", 0.0)
    total_income = totals_dict.get("income", 0.0)
    return {
        "period": f"{start_date} to {end_date}",
        "total_expenses": total_expenses,
        "total_income": total_income,
        "net": total_income - total_expenses,
        "transaction_count": transaction_count,
        "by_category": [dict(r) for r in by_category],
    }


@mcp.tool
def get_monthly_report(year: int, month: int) -> dict:
    """Get a detailed report for a specific month (e.g. 2026, 6)."""
    start_date = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1:04d}-01-01"
    else:
        end_date = f"{year:04d}-{month + 1:02d}-01"
    return get_summary(start_date=start_date, end_date=end_date)


if __name__ == "__main__":
    mcp.run()
