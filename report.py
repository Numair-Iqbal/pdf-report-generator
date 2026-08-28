"""
report.py — 3 kaam yahan hote hain (pipeline ke 3 moves):
  1. get_report_data()  -> QUERY: 200 rows ko 4 useful cheezon mein badalta hai
  2. build_html()        -> RENDER (part 1): numbers ko HTML page banata hai
  3. render_pdf()         -> RENDER (part 2): HTML ko asli PDF file banata hai
"""
from datetime import datetime, timedelta
from db import get_connection


def get_report_data():
    """
    Yahan 'aggregation' ho rahi hai — matlab bohot saari rows ko chand numbers
    mein convert karna (COUNT, SUM, GROUP BY).
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1) total number of orders
    total_orders = cur.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"]

    # 2) total revenue = sab amounts ka sum
    total_revenue = cur.execute("SELECT SUM(amount) AS s FROM orders").fetchone()["s"] or 0

    # 3) top 5 products by revenue (GROUP BY product, phir sort karke top 5)
    top_products = cur.execute("""
        SELECT product, SUM(amount) AS revenue, COUNT(*) AS orders_count
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """).fetchall()

    # 4) pichle 7 din ke orders, per-day count
    seven_days_ago = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    orders_per_day = cur.execute("""
        SELECT created_at AS day, COUNT(*) AS orders_count
        FROM orders
        WHERE created_at >= ?
        GROUP BY created_at
        ORDER BY created_at
    """, (seven_days_ago,)).fetchall()

    # Saari (sample) rows bhi chahiye honge report ki lambi table ke liye
    all_orders = cur.execute("""
        SELECT customer, product, amount, created_at
        FROM orders
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "top_products": [dict(r) for r in top_products],
        "orders_per_day": [dict(r) for r in orders_per_day],
        "all_orders": [dict(r) for r in all_orders],
    }


def build_html(data: dict) -> str:
    """Numbers/lists ko ek simple HTML page mein pour karta hai."""
    today = datetime.now().strftime("%Y-%m-%d")

    top_rows = "".join(
        f"<tr><td>{p['product']}</td><td>{p['orders_count']}</td>"
        f"<td>€{p['revenue']:.2f}</td></tr>"
        for p in data["top_products"]
    )

    all_rows = "".join(
        f"<tr><td>{o['customer']}</td><td>{o['product']}</td>"
        f"<td>€{o['amount']:.2f}</td><td>{o['created_at']}</td></tr>"
        for o in data["all_orders"]
    )

    html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; }}
        h1 {{ font-size: 22px; }}
        .totals {{ display: flex; gap: 30px; margin: 20px 0; }}
        .box {{ border: 1px solid #ccc; padding: 12px 20px; border-radius: 6px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; font-size: 12px; }}
        th {{ background: #f2f2f2; }}
        /* Yahan wo trick hai jo row ko page-break mein katne se rokti hai */
        tr {{ break-inside: avoid; }}
        thead {{ display: table-header-group; }} /* har page par header repeat hoga */
    </style>
    </head>
    <body>
        <h1>Sales Report — {today}</h1>
        <div class="totals">
            <div class="box"><strong>Total Orders</strong><br>{data['total_orders']}</div>
            <div class="box"><strong>Total Revenue</strong><br>€{data['total_revenue']:.2f}</div>
        </div>

        <h2>Top 5 Products</h2>
        <table>
            <thead><tr><th>Product</th><th>Orders</th><th>Revenue</th></tr></thead>
            <tbody>{top_rows}</tbody>
        </table>

        <h2>All Orders</h2>
        <table>
            <thead><tr><th>Customer</th><th>Product</th><th>Amount</th><th>Date</th></tr></thead>
            <tbody>{all_rows}</tbody>
        </table>
    </body>
    </html>
    """
    return html


def render_pdf(html: str, output_path: str):
    """
    HTML ko real PDF banata hai — Playwright ek headless (bina window ke)
    Chromium browser chalata hai, HTML load karta hai, aur "print" kar deta hai.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=output_path, format="A4", print_background=True)
        browser.close()
