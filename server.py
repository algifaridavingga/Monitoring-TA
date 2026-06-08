import os
import math
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder=".", static_folder=".")
app.secret_key = "rahasia_sistem_ai_jalan_rusak_2026"

# Database User
AKUN_PENGGUNA = {
    "algifari": generate_password_hash("123"),
    "dinas": generate_password_hash("petugas1")
}

# Data Contoh Hasil Deteksi Jalan
database_deteksi = [
    {
        "id": 1,
        "lat": -6.2088, "lon": 106.8456,
        "jenis": "Pothole (Lubang)", "confidence": 0.88,
        "waktu": "04-06-2026 14:20",
        "image": "https://images.unsplash.com/photo-1515162305285-0293e4767cc2?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": 2,
        "lat": -6.2100, "lon": 106.8490,
        "jenis": "Longitudinal Crack (Retak Memanjang)", "confidence": 0.72,
        "waktu": "04-06-2026 15:05",
        "image": "https://images.unsplash.com/photo-1599740482930-da1022797e8d?auto=format&fit=crop&w=400&q=80"
    }
]

# Riwayat Training
database_training = [
    {
        "waktu": "04-06-2026 18:31",
        "model": "YOLOv8n_RoadDamage_v1.pt",
        "epoch": 50,
        "dataset": "420 Gambar",
        "map50": "79.4%",
        "status": "Selesai"
    }
]

# Fungsi Jarak Spasial
def hitung_jarak_meter(lat1, lon1, lat2, lon2):
    selisih_lat = (lat2 - lat1) * 111000
    selisih_lon = (lon2 - lon1) * 111000 * math.cos(math.radians(lat1))
    return math.sqrt(selisih_lat**2 + selisih_lon**2)

# ==================== AUTH ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in AKUN_PENGGUNA and check_password_hash(AKUN_PENGGUNA[username], password):
            session['user'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error="Username atau Password salah!")
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['user'])

# ==================== API ====================

@app.route('/api/data', methods=['GET'])
def get_data():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(database_deteksi)

@app.route('/api/training', methods=['GET'])
def get_training():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(database_training)

@app.route('/api/history', methods=['GET'])
def get_history():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    mode = request.args.get('mode', 'all')
    sekarang = datetime.now()
    hasil = []

    for item in database_deteksi:
        try:
            waktu_item = datetime.strptime(item['waktu'], "%d-%m-%Y %H:%M")
            if mode == 'today':
                if waktu_item.date() == sekarang.date():
                    hasil.append(item)
            elif mode == 'week':
                if waktu_item >= sekarang - timedelta(days=7):
                    hasil.append(item)
            elif mode == 'month':
                if waktu_item >= sekarang - timedelta(days=30):
                    hasil.append(item)
            else:
                hasil.append(item)
        except:
            hasil.append(item)

    return jsonify(hasil)

# ✅ FIX: Route /api/statistik duplikat dihapus, dijadikan satu saja
@app.route('/api/statistik', methods=['GET'])
def get_statistik():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    sekarang = datetime.now()
    hari_ini = 0
    minggu_ini = 0
    bulan_ini = 0

    for item in database_deteksi:
        try:
            waktu_item = datetime.strptime(item['waktu'], "%d-%m-%Y %H:%M")
            if waktu_item.date() == sekarang.date():
                hari_ini += 1
            if waktu_item >= sekarang - timedelta(days=7):
                minggu_ini += 1
            if waktu_item >= sekarang - timedelta(days=30):
                bulan_ini += 1
        except:
            pass

    return jsonify({
        "hari_ini": hari_ini,
        "minggu_ini": minggu_ini,
        "bulan_ini": bulan_ini
    })

# ==================== UPLOAD DARI DETECT.PY ====================

@app.route('/upload', methods=['POST'])
def upload_data():
    data_baru = request.json

    if not data_baru:
        return jsonify({"error": "Data kosong"}), 400

    data_baru['id'] = len(database_deteksi) + 1
    data_baru['waktu'] = datetime.now().strftime("%d-%m-%Y %H:%M")

    radius_toleransi = 30.0
    apakah_duplikat = False

    for data_lama in database_deteksi:
        jarak = hitung_jarak_meter(data_baru['lat'], data_baru['lon'], data_lama['lat'], data_lama['lon'])
        if jarak < radius_toleransi and data_baru['jenis'] == data_lama['jenis']:
            apakah_duplikat = True
            if data_baru['confidence'] > data_lama['confidence']:
                data_lama['confidence'] = data_baru['confidence']
                data_lama['image'] = data_baru['image']
                data_lama['waktu'] = data_baru['waktu']
            break

    if not apakah_duplikat:
        database_deteksi.append(data_baru)

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
   app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
