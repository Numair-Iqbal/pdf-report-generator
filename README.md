# PDF Report Generator

FlyRank Internship — Backend Track — Assignment A8 (Week 4)

A small API that seeds fake sales data into SQLite, aggregates it with SQL,
renders it into a real PDF via a headless browser (Playwright), and serves
the finished file by link.

**Dataset chosen:** Option A — the little shop (`orders` table, ~200 seeded rows).

## How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Seed the database (safe to run more than once — clears then re-inserts)
python seed.py

# 3. Start the API
uvicorn main:app --reload

# 4. Try it
curl http://localhost:8000/health
curl -X POST http://localhost:8000/reports
curl -o my-report.pdf http://localhost:8000/reports/1/file
```

## Aggregation SQL

```sql
-- Total orders
SELECT COUNT(*) FROM orders;

-- Total revenue
SELECT SUM(amount) FROM orders;

-- Top 5 products by revenue
SELECT product, SUM(amount) AS revenue, COUNT(*) AS orders_count
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5;

-- Orders per day, last 7 days
SELECT created_at AS day, COUNT(*) AS orders_count
FROM orders
WHERE created_at >= date('now', '-6 days')
GROUP BY created_at
ORDER BY created_at;
```

## POST → download proof

```
POST /reports          -> 201 {"id": 1, "file": "/reports/1/file"}
GET  /reports/1         -> 200 {"id": 1, "created_at": "...", "file": "/reports/1/file"}
GET  /reports/1/file    -> 200, application/pdf (downloads the actual report)
```

## Stage 4 note (moving work out of the request)

The `POST /reports` endpoint currently does the full pipeline (query, render,
save) synchronously, so the response takes a few seconds. For a single user
this is fine. If report generation started taking longer (bigger datasets,
many concurrent users), I would move it into a background job (A7 pattern):
return `202 Accepted` immediately with an id, run the pipeline in a worker,
and let the client poll `GET /reports/:id` for a `pending` / `done` status.

## Stage 5 note (why idempotency matters)

The duplicate-request check protects against a user double-clicking
"Generate report" and accidentally creating two (or more) files for the same
day — wasted disk space and a confusing history. A real-world example: an
e-commerce checkout button without this kind of guard can charge a customer's
card twice if they double-click "Pay Now".

## Proof

Two rapid `POST /reports` calls on the same day return the same `id`
(200 on the second call, `reused: true`), and exactly one new file appears
in `reports/`. Sending `{"force": true}` creates a genuinely new report.

*(Add a screenshot of page 1 of a generated PDF here before submitting.)*
