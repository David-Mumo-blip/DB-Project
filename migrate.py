"""Bring an existing database up to date WITHOUT wiping any data.

    python migrate.py --check    show what is missing, change nothing
    python migrate.py            apply whatever is missing

Safe to run more than once: every step first checks whether it is already done.
It makes the same changes as DB_Scripts/migrate_to_latest.sql and admin_migration.sql.
"""
import sys

from db import get_db


def column_exists(cur, table, column):
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, column),
    )
    return cur.fetchone()[0] > 0


def table_exists(cur, table):
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (table,),
    )
    return cur.fetchone()[0] > 0


def column_type(cur, table, column):
    cur.execute(
        "SELECT column_type, is_nullable FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
        (table, column),
    )
    return cur.fetchone()


# (description, "is it already done?", SQL to run)
STEPS = [
    ("users.role accepts 'admin'",
     lambda c: "'admin'" in (column_type(c, 'users', 'role') or ('',))[0],
     "ALTER TABLE users MODIFY role ENUM('student', 'vendor', 'admin') NOT NULL"),
    ("vendors.balance",
     lambda c: column_exists(c, 'vendors', 'balance'),
     "ALTER TABLE vendors ADD COLUMN balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00"),
    ("vendors.revenue_goal",
     lambda c: column_exists(c, 'vendors', 'revenue_goal'),
     "ALTER TABLE vendors ADD COLUMN revenue_goal DECIMAL(10, 2) NOT NULL DEFAULT 10000.00"),
    ("orders.customer_id may be NULL (vendor self-orders)",
     lambda c: (column_type(c, 'orders', 'customer_id') or ('', ''))[1] == 'YES',
     "ALTER TABLE orders MODIFY customer_id INT NULL"),
    ("orders.quantity",
     lambda c: column_exists(c, 'orders', 'quantity'),
     "ALTER TABLE orders ADD COLUMN quantity INT NOT NULL DEFAULT 1"),
    ("notifications table",
     lambda c: table_exists(c, 'notifications'),
     """CREATE TABLE notifications (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            order_id INT NULL,
            message VARCHAR(255) NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE SET NULL
        )"""),
]


def main():
    check_only = '--check' in sys.argv
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT DATABASE()")
    print(f"Database: {cur.fetchone()[0]}")

    pending = 0
    for description, is_done, sql in STEPS:
        if is_done(cur):
            print(f"  ok       {description}")
            continue
        pending += 1
        if check_only:
            print(f"  MISSING  {description}")
        else:
            cur.execute(sql)
            db.commit()
            print(f"  ADDED    {description}")

    cur.close()
    db.close()
    if check_only:
        print(f"\n{pending} change(s) needed. Run `python migrate.py` to apply them." if pending
              else "\nDatabase is up to date.")
    else:
        print("\nDone. Database is up to date.")


if __name__ == '__main__':
    main()
