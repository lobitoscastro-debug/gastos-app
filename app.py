from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura_123"  # cámbiala en producción

DB_NAME = "gastos.db"

# ---------- Funciones de base de datos ----------
def init_db():
    """Crea la tabla de gastos si no existe."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Rutas ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "").strip()
        if usuario == "admin" and clave == "123":
            session["usuario"] = usuario
            return redirect(url_for("index"))
        else:
            flash("Credenciales incorrectas", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/index", methods=["GET", "POST"])
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        fecha = request.form.get("fecha")
        descripcion = request.form.get("descripcion", "").strip()
        monto = request.form.get("monto", "").strip()
        if fecha and descripcion and monto:
            try:
                monto_val = float(monto)
                conn = get_db()
                conn.execute(
                    "INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)",
                    (fecha, descripcion, monto_val),
                )
                conn.commit()
                conn.close()
                flash("Gasto registrado correctamente", "ok")
            except ValueError:
                flash("El monto debe ser numérico", "error")
        else:
            flash("Completa todos los campos", "error")
        return redirect(url_for("index"))

    conn = get_db()
    gastos = conn.execute(
        "SELECT * FROM gastos ORDER BY fecha DESC, id DESC"
    ).fetchall()
    total = sum(g["monto"] for g in gastos)
    conn.close()
    return render_template("index.html", gastos=gastos, total=total)

@app.route("/reporte")
def reporte():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    gastos = conn.execute(
        "SELECT * FROM gastos ORDER BY fecha ASC"
    ).fetchall()
    conn.close()

    total = sum(g["monto"] for g in gastos)

    # Agrupación por mes para el reporte
    por_mes = {}
    for g in gastos:
        mes = g["fecha"][:7]  # formato YYYY-MM
        por_mes[mes] = por_mes.get(mes, 0) + g["monto"]

    return render_template(
        "reporte.html",
        gastos=gastos,
        total=total,
        por_mes=sorted(por_mes.items()),
        fecha_generacion=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )

@app.route("/eliminar/<int:gasto_id>", methods=["POST"])
def eliminar(gasto_id):
    if "usuario" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
    conn.commit()
    conn.close()
    flash("Gasto eliminado", "ok")
    return redirect(url_for("index"))

# ---------- Inicio ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)