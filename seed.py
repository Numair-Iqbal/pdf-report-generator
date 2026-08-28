"""
seed.py — fake data generate karke orders table mein daalta hai.

Ye script IDEMPOTENT hai: pehle sab purani rows delete karta hai, phir 200 nayi
insert karta hai. Isliye ise 2 dafa chalao to bhi row count 200 hi rahega
(double nahi hoga) — assignment ka Stage 1 checkpoint yehi test karta hai.

Chalane ka tareeqa:  python seed.py
"""
import random
from datetime import datetime, timedelta
from db import get_connection, init_db

PRODUCTS = ["Notebook", "Backpack", "Water Bottle", "Headphones", "Desk Lamp", "Mouse"]
CUSTOMERS = ["Ali", "Sara", "Bilal", "Ayesha", "Hassan", "Fatima", "Usman", "Zainab"]


def seed():
    init_db()  # tables exist karna confirm karo
    conn = get_connection()
    cur = conn.cursor()

    # Step 1: purani sab rows delete — taake dobara run karne se duplicate na banein
    cur.execute("DELETE FROM orders")

    # Step 2: 200 random orders insert karo
    today = datetime.now()
    rows = []
    for _ in range(200):
        customer = random.choice(CUSTOMERS)
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5, 200), 2)
        days_ago = random.randint(0, 29)  # pichle 30 din ke andar
        created_at = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        rows.append((customer, product, amount, created_at))

    cur.executemany(
        "INSERT INTO orders (customer, product, amount, created_at) VALUES (?, ?, ?, ?)",
        rows,
    )

    conn.commit()

    # Step 3: confirm karo kitni rows hain (checkpoint)
    count = cur.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]
    print(f"Seeded. orders table now has {count} rows.")

    conn.close()


if __name__ == "__main__":
    seed()
