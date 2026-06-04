import subprocess
import time
import sys

def main():
    print("🚀 [1/2] Menghidupkan Server Website Flask...")
    # Menjalankan server.py di latar belakang
    server_process = subprocess.Popen([sys.executable, "src/server.py"])

    # Memberikan jeda 2 detik agar Flask benar-benar siap menerima data
    time.sleep(2)

    print("👁️  [2/2] Menjalankan Deteksi AI YOLOv8...")
    try:
        # Menjalankan detect.py di layar utama
        subprocess.run([sys.executable, "src/detect.py"])
    except KeyboardInterrupt:
        print("\n🛑 Menerima perintah stop...")
    finally:
        # Menutup server Flask secara otomatis agar port 5000 tidak nyangkut/bocor
        print("🧹 Mematikan server website...")
        server_process.terminate()
        server_process.wait()
        print("✅ Semua proses berhasil dihentikan dengan bersih!")

if __name__ == "__main__":
    main()