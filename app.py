import os, sqlite3, uuid, threading, time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)
DB = os.getenv("SMARTCART_DB", "smartcart.db")
LOCK = threading.Lock()

PRODUCTS = [
    ("8901001", "Milk 500ml", 32.00),
    ("8901002", "Bread", 40.00),
    ("8901003", "Rice 1kg", 68.00),
    ("8901004", "Cooking Oil 1L", 145.00),
    ("8901005", "Biscuits", 20.00),
    ("8901006", "Soap", 35.00),
]

def db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS products(
            rfid_uid TEXT PRIMARY KEY, name TEXT NOT NULL, price REAL NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS cart(
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
            rfid_uid TEXT NOT NULL, name TEXT NOT NULL, price REAL NOT NULL,
            added_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS transactions(
            id TEXT PRIMARY KEY, items_json TEXT NOT NULL, total REAL NOT NULL,
            created_at TEXT NOT NULL)""")
        for uid, name, price in PRODUCTS:
            con.execute("INSERT OR IGNORE INTO products VALUES(?,?,?)", (uid,name,price))

def cart_data(session_id="demo"):
    with db() as con:
        rows = con.execute("""SELECT rfid_uid, name, price, COUNT(*) quantity
            FROM cart WHERE session_id=? GROUP BY rfid_uid,name,price ORDER BY name""",
            (session_id,)).fetchall()
    items = [dict(r) for r in rows]
    total = round(sum(x["price"]*x["quantity"] for x in items), 2)
    return items, total

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/products")
def products():
    with db() as con:
        rows = con.execute("SELECT * FROM products ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/cart")
def get_cart():
    items,total = cart_data()
    return jsonify({"items":items,"total":total})

@app.post("/api/scan")
def scan():
    data = request.get_json(silent=True) or {}
    uid = str(data.get("uid","")).strip().upper().replace(" ","")
    if not uid:
        return jsonify({"ok":False,"message":"No RFID UID received"}), 400
    with db() as con:
        product = con.execute("SELECT * FROM products WHERE UPPER(REPLACE(rfid_uid,' ',''))=?",(uid,)).fetchone()
        if not product:
            return jsonify({"ok":False,"unknown":True,
                "message":f"Unknown RFID tag: {uid}. Please verify product manually."}), 404
        con.execute("INSERT INTO cart(session_id,rfid_uid,name,price,added_at) VALUES(?,?,?,?,?)",
            ("demo",product["rfid_uid"],product["name"],product["price"],datetime.now().isoformat(timespec="seconds")))
    items,total = cart_data()
    return jsonify({"ok":True,"message":product["name"]+" added","items":items,"total":total})

@app.post("/api/remove")
def remove():
    data = request.get_json(silent=True) or {}
    uid = str(data.get("uid",""))
    with db() as con:
        row = con.execute("SELECT id FROM cart WHERE session_id='demo' AND rfid_uid=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
        if row:
            con.execute("DELETE FROM cart WHERE id=?",(row["id"],))
    items,total = cart_data()
    return jsonify({"items":items,"total":total})

@app.post("/api/clear")
def clear():
    with db() as con:
        con.execute("DELETE FROM cart WHERE session_id='demo'")
    return jsonify({"items":[],"total":0})

@app.post("/api/checkout")
def checkout():
    items,total = cart_data()
    if not items:
        return jsonify({"ok":False,"message":"Cart is empty"}), 400
    txid = "SC-" + uuid.uuid4().hex[:10].upper()
    import json
    with db() as con:
        con.execute("INSERT INTO transactions VALUES(?,?,?,?)",
            (txid,json.dumps(items),total,datetime.now().isoformat(timespec="seconds")))
        con.execute("DELETE FROM cart WHERE session_id='demo'")
    return jsonify({"ok":True,"transaction_id":txid,"items":items,"total":total,
                    "created_at":datetime.now().strftime("%d-%m-%Y %H:%M:%S")})

@app.get("/api/transactions")
def transactions():
    with db() as con:
        rows = con.execute("SELECT id,total,created_at FROM transactions ORDER BY created_at DESC LIMIT 20").fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
