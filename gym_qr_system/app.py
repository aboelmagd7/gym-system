from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import sqlite3
import qrcode
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_PATH = 'database.db'
QR_FOLDER = os.path.join('static', 'qr')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def subscription_days(sub_type):
    return {
        'شهري': 30,
        'ربع سنوي': 90,
        'سنوي': 365
    }.get(sub_type, 0)

@app.route('/')
def index():
    conn = get_db_connection()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    return render_template('index.html', clients=clients)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        subscription_type = request.form['subscription_type']
        start_date = datetime.now().strftime('%Y-%m-%d')
        barcode = f"{phone[-4:]}{int(datetime.now().timestamp())}"
        qr = qrcode.make(barcode)
        qr.save(os.path.join(QR_FOLDER, f"{barcode}.png"))

        conn = get_db_connection()
        conn.execute('INSERT INTO clients (name, phone, subscription_type, start_date, barcode) VALUES (?, ?, ?, ?, ?)',
                     (name, phone, subscription_type, start_date, barcode))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    client = None
    if request.method == 'POST':
        barcode = request.form['barcode']
        conn = get_db_connection()
        client = conn.execute('SELECT * FROM clients WHERE barcode = ?', (barcode,)).fetchone()
        conn.close()
        if not client:
            flash('العميل غير موجود')
        else:
            start_date = datetime.strptime(client['start_date'], '%Y-%m-%d')
            days = subscription_days(client['subscription_type'])
            remaining = (start_date + timedelta(days=days)) - datetime.now()
            client = dict(client)
            client['remaining'] = remaining.days
    return render_template('scan.html', client=client)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    client = conn.execute('SELECT * FROM clients WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        subscription_type = request.form['subscription_type']
        conn.execute('UPDATE clients SET name = ?, phone = ?, subscription_type = ? WHERE id = ?',
                     (name, phone, subscription_type, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', client=client)

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM clients WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
