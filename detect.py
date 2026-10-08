import os
from dotenv import load_dotenv
load_dotenv()

import cv2
import base64
import requests
from ultralytics import YOLO
import matplotlib.pyplot as plt

# ==================== CONFIGURATION ====================
# ⚠️ Setelah training ulang model segmentasi, ganti path ini
# ke lokasi best.pt hasil training yolov8n-seg (biasanya di runs/segment/... bukan runs/detect/...)
MODEL_PATH = "runs/segment/train/weights/best.pt"
VIDEO_PATH = "src/video.mp4"
API_URL = os.getenv("API_URL", "https://monitoring-ta-mauve.vercel.app/upload") 

# 1. Load Model YOLOv8 (Segmentasi)
try:
    model = YOLO(MODEL_PATH)
    print("✅ MODEL BERHASIL DI-LOAD")
except Exception as e:
    print(f"❌ GAGAL LOAD MODEL: Periksa apakah file ada di {MODEL_PATH}. Error: {e}")
    exit()

# 2. Load Berkas Video
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"❌ VIDEO TIDAK TERBUKA: Periksa apakah file ada di {VIDEO_PATH}")
    exit()

# 3. Inisialisasi Koordinat GPS Awal (Simulasi pergerakan)
lat = -6.200000
lon = 106.816666

# 4. Penampung Data untuk Grafik Matplotlib
list_akurasi = []
list_frame = []

frame_count = 0

print("🚀 Memulai Sistem Deteksi (Segmentasi)... Tekan 'ESC' pada jendela video untuk berhenti awal.")

# ==================== LOOP DETEKSI VIDEO ====================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("🎞️ Video telah selesai diputar sampai habis.")
        break

    frame_count += 1
    
    # Jalankan deteksi+segmentasi YOLOv8 pada frame saat ini
    results = model(frame, verbose=False)[0]
    
    # Ambil gambar frame yang sudah otomatis digambari MASK/KONTUR oleh YOLO
    annotated_frame = results.plot()

    # Simulasi pergerakan koordinat GPS
    lat += 0.00001
    lon += 0.000005

    max_conf_in_frame = 0.0
    detected_label = "damage"

    # ===== PERIKSA APAKAH ADA OBJEK KERUSAKAN JALAN (VERSI SEGMENTASI) =====
    if results.masks is not None:
        for i, mask in enumerate(results.masks):
            conf = float(results.boxes[i].conf[0])
            cls_id = int(results.boxes[i].cls[0])
            label = results.names[cls_id]

            if conf > max_conf_in_frame:
                max_conf_in_frame = conf
                detected_label = label

        # --- PENGIRIMAN DATA KE DASHBOARD WEB ---
        if max_conf_in_frame > 0.3 and frame_count % 10 == 0:
            try:
                # Konversi frame menjadi format teks Base64
                kecil = cv2.resize(annotated_frame, (320, 240))
                _, buffer = cv2.imencode('.jpg', kecil, [cv2.IMWRITE_JPEG_QUALITY, 50])
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                # Bungkus data ke format JSON
                payload = {
                    "jenis": detected_label,
                    "confidence": max_conf_in_frame,
                    "lat": lat,
                    "lon": lon,
                    "image": img_base64
                }

                # Kirim data ke backend Flask
                response = requests.post(API_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"📤 [Frame {frame_count}] BERHASIL KIRIM -> {detected_label.upper()} ({max_conf_in_frame*100:.0f}%) + Screenshot")
            
            except Exception as e:
                print(f"⚠️ Gagal menembak data ke web server: {e}")

    # Catat skor akurasi untuk grafik
    list_akurasi.append(max_conf_in_frame * 100)
    list_frame.append(frame_count)

    # Tampilkan rekaman video hasil deteksi
    cv2.imshow("Sistem Real-time Deteksi Jalan", annotated_frame)

    # Jendela berhenti jika menekan tombol ESC
    if cv2.waitKey(1) & 0xFF == 27:
        print("🛑 Proses deteksi dihentikan paksa oleh pengguna.")
        break

# Tutup pemrosesan kamera video dan jendela OpenCV
cap.release()
cv2.destroyAllWindows()
