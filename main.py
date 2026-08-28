"""
main.py — hamara API. 4 endpoints:
  GET  /health              -> server zinda hai check karne ke liye
  POST /reports              -> pura pipeline chalao: query -> render -> save -> DB row
  GET  /reports/{id}         -> ek report ki details (aur uska download link)
  GET  /reports/{id}/file    -> asli PDF file download karo

Chalane ka tareeqa:  uvicorn main:app --reload
"""
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Response, Body
from fastapi.responses import FileResponse

from db import get_connection, init_db
from report import get_report_data, build_html, render_pdf

app = FastAPI()
REPORTS_DIR = "reports"

init_db()
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports")
def create_report(response: Response, body: dict = Body(default={})):
    """
    Idempotency (Stage 5): agar AAJ pehle se ek report ban chuki hai, to
    nayi mat banao — wohi purani wapis kar do (status 200, 201 nahi).
    force: true bhejo to naya bana dega, purana check ignore karke.
    """
    body = body or {}
    force = body.get("force", False)
    today = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cur = conn.cursor()

    if not force:
        existing = cur.execute(
            "SELECT id, path FROM reports WHERE created_at = ? ORDER BY id DESC LIMIT 1",
            (today,),
        ).fetchone()
        if existing:
            conn.close()
            response.status_code = 200  # naya nahi bana isliye 201 nahi, 200 (OK)
            return {"id": existing["id"], "file": f"/reports/{existing['id']}/file", "reused": True}

    response.status_code = 201  # naya resource banaya

    # ---- yahan se pura pipeline chalta hai (Query -> Render -> Store) ----
    data = get_report_data()                 # QUERY
    html = build_html(data)                  # RENDER (html)
    conn2 = get_connection()
    cur2 = conn2.cursor()
    cur2.execute("INSERT INTO reports (path, created_at) VALUES (?, ?)", ("", today))
    report_id = cur2.lastrowid
    pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
    render_pdf(html, pdf_path)                # RENDER (pdf) + STORE
    cur2.execute("UPDATE reports SET path = ? WHERE id = ?", (pdf_path, report_id))
    conn2.commit()
    conn2.close()
    conn.close()

    return {"id": report_id, "file": f"/reports/{report_id}/file"}


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "file": f"/reports/{row['id']}/file",
    }


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    """SERVE: sirf ye endpoint bytes bhejta hai — baaki sab JSON hi bhejte hain."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    if not row or not os.path.exists(row["path"]):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(row["path"], media_type="application/pdf", filename=f"report-{report_id}.pdf")
