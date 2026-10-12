import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

COUNTERS = ("Ventanilla 1", "Ventanilla 2", "Ventanilla 3", "Ventanilla 4")
DB_PATH = os.environ.get("QUEUE_DB_PATH", "/tmp/turnos.db" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "turnos.db"))


def connect():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'waiting',
        counter_id INTEGER,
        created_at TEXT NOT NULL,
        finished_at TEXT
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS counters (
        id INTEGER PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'available',
        ticket_id INTEGER
    )""")
    connection.executemany("INSERT OR IGNORE INTO counters(id) VALUES (?)", [(i,) for i in range(1, 5)])
    connection.commit()
    return connection


def ticket_dict(row):
    return {"id": row["id"], "code": row["code"], "status": row["status"],
            "counter": row["counter_id"], "createdAt": row["created_at"]}


def dashboard(connection):
    tickets = [ticket_dict(row) for row in connection.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 50")]
    counter_rows = connection.execute("""SELECT c.id, c.status, t.id ticket_id, t.code, t.status ticket_status,
      t.counter_id, t.created_at FROM counters c LEFT JOIN tickets t ON t.id=c.ticket_id ORDER BY c.id""").fetchall()
    counters = []
    for row in counter_rows:
        current = ({"id": row["ticket_id"], "code": row["code"], "status": row["ticket_status"],
                    "counter": row["counter_id"], "createdAt": row["created_at"]} if row["ticket_id"] else None)
        counters.append({"id": row["id"], "name": COUNTERS[row["id"] - 1], "status": row["status"], "ticket": current})
    next_row = connection.execute("SELECT * FROM tickets WHERE status='waiting' ORDER BY id LIMIT 1").fetchone()
    stats = {
        "waiting": connection.execute("SELECT count(*) FROM tickets WHERE status='waiting'").fetchone()[0],
        "served": connection.execute("SELECT count(*) FROM tickets WHERE status='done' AND date(finished_at)=date('now')").fetchone()[0],
        "available": sum(1 for counter in counters if counter["status"] == "available"),
    }
    return {"tickets": tickets, "counters": counters, "nextTicket": ticket_dict(next_row) if next_row else None, "stats": stats}


@app.get("/api/dashboard")
def get_dashboard():
    connection = connect()
    try:
        return jsonify(dashboard(connection))
    finally:
        connection.close()


@app.post("/api/tickets")
def create_ticket():
    connection = connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        number = connection.execute("SELECT coalesce(max(id), 0) + 1 FROM tickets").fetchone()[0]
        code = f"A{number:02d}"
        created = datetime.now(timezone.utc).isoformat()
        cursor = connection.execute("INSERT INTO tickets(code, created_at) VALUES (?, ?)", (code, created))
        connection.commit()
        return jsonify(ticket_dict(connection.execute("SELECT * FROM tickets WHERE id=?", (cursor.lastrowid,)).fetchone())), 201
    except sqlite3.Error:
        connection.rollback()
        return jsonify(error="No se pudo crear el turno. Intenta de nuevo."), 500
    finally:
        connection.close()


@app.post("/api/counters/<int:counter_id>/call")
def call_next(counter_id):
    if not 1 <= counter_id <= 4:
        return jsonify(error="Ventanilla no válida."), 404
    connection = connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        counter = connection.execute("SELECT * FROM counters WHERE id=?", (counter_id,)).fetchone()
        if counter["status"] == "busy":
            connection.rollback()
            return jsonify(error="Esta ventanilla está ocupada."), 409
        ticket = connection.execute("SELECT * FROM tickets WHERE status='waiting' ORDER BY id LIMIT 1").fetchone()
        if not ticket:
            connection.rollback()
            return jsonify(error="No hay turnos en espera."), 409
        connection.execute("UPDATE tickets SET status='serving', counter_id=? WHERE id=?", (counter_id, ticket["id"]))
        connection.execute("UPDATE counters SET status='busy', ticket_id=? WHERE id=?", (ticket["id"], counter_id))
        connection.commit()
        return jsonify(dashboard(connection))
    except sqlite3.Error:
        connection.rollback()
        return jsonify(error="No se pudo llamar al siguiente turno."), 500
    finally:
        connection.close()


@app.post("/api/counters/<int:counter_id>/finish")
def finish(counter_id):
    connection = connect()
    try:
        connection.execute("BEGIN IMMEDIATE")
        counter = connection.execute("SELECT * FROM counters WHERE id=?", (counter_id,)).fetchone()
        if not counter:
            connection.rollback()
            return jsonify(error="Ventanilla no válida."), 404
        if counter["status"] != "busy":
            connection.rollback()
            return jsonify(error="Esta ventanilla ya está disponible."), 409
        connection.execute("UPDATE tickets SET status='done', finished_at=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), counter["ticket_id"]))
        connection.execute("UPDATE counters SET status='available', ticket_id=NULL WHERE id=?", (counter_id,))
        connection.commit()
        return jsonify(dashboard(connection))
    except sqlite3.Error:
        connection.rollback()
        return jsonify(error="No se pudo finalizar la atención."), 500
    finally:
        connection.close()


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="turnos-atencion")
