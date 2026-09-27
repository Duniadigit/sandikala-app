# Sandikala — Aplikasi Steganografi LSB Aman
### *"Sandi yang bersembunyi di setiap kala"*

Tugas Proyek Aplikasi Kriptografi — Topik B (Steganografi)
Mata Kuliah Keamanan Informasi — Program Studi Informatika, Universitas Siliwangi

## 👥 Anggota Kelompok
| Nama | NPM |
|---|---|
| (Adam Malik Rizkiyansyah) | (247006111001) |
| (Farhan Ramadhan) | (247006111018) |
| (Sahrul Ramdhani) | (247006111005) |

---

## 📄 Deskripsi

Sandikala adalah aplikasi web untuk menyisipkan (embed) dan mengekstraksi (extract) pesan teks rahasia ke/dari citra digital (PNG/BMP) menggunakan **metode LSB (Least Significant Bit)**, dengan lapisan keamanan tambahan:

- Posisi pixel yang disisipi **diacak** memakai PRNG yang di-*seed* dari **stego-key** rahasia (bukan berurutan, sehingga tidak mudah ditebak).
- Pesan **dienkripsi AES-256-GCM** sebelum disisipkan — kunci diturunkan dari kata sandi pengguna via **PBKDF2-HMAC-SHA256** (200.000 iterasi) dengan salt acak, sehingga pesan tetap aman walau posisi penyisipan berhasil ditebak.
- Header 32-bit penanda panjang pesan, agar proses ekstraksi berhenti tepat tanpa membaca data sampah.
- Kapasitas penyisipan dihitung otomatis, dan pesan yang melebihi kapasitas citra **ditolak** (bukan dipotong diam-diam).
- Antarmuka **responsif** — dapat dibuka dan digunakan dengan nyaman baik dari desktop maupun HP/tablet.

Contoh kasus penggunaan nyata: mengirim pesan rahasia lewat foto yang diunggah ke media sosial, atau menyisipkan kode verifikasi internal ke dalam gambar produk.

---

## 🏗️ Arsitektur / Struktur Folder

```
sandikala/
├── app.py                  # Backend Flask (routing + REST API JSON)
├── stego_core.py            # Logika inti: AES-256-GCM + LSB dengan PRNG (ditulis sendiri)
├── requirements.txt         # Daftar dependensi Python
├── README.md                # File ini
├── templates/
│   └── index.html           # Halaman web (3 tab: Sandikan/Ungkap/Telisik)
├── static/
│   ├── css/style.css        # Tema visual Sandikala + desain responsif
│   └── js/app.js            # Panggilan AJAX ke backend + interaksi UI
├── tests/
│   └── test_stego.py        # 8 unit test (pytest) untuk fungsi inti
├── testing/
│   ├── metrics.py            # Fungsi PSNR, MSE, histogram, chi-square
│   └── run_full_test.py      # Otomatisasi pengujian kuantitatif -> Excel
└── sample_images/            # Taruh minimal 5 citra uji PNG/BMP berbeda di sini
```

---

## ⚙️ Cara Instalasi

1. Install **Python 3.10+** dan **VS Code** di komputer Anda.
2. Clone repositori ini dan masuk ke dalam folder proyek:
   ```bash
   git clone https://github.com
   cd sandikala
   ```
3. Buat dan aktifkan virtual environment:
   - **Windows:**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```
4. Install seluruh dependensi yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Cara Menjalankan

```bash
python app.py
```

Buka browser ke **http://127.0.0.1:5000**.

Antarmuka bersifat **responsif** — bisa dibuka dari laptop/desktop maupun dari HP/tablet, tampilan akan otomatis menyesuaikan lebar layar. Untuk mengakses dari HP fisik (bukan hanya simulasi DevTools), ubah baris terakhir `app.py` menjadi `app.run(debug=True, host='0.0.0.0', port=5000)`, lalu buka `http://ALAMAT-IP-LAPTOP:5000` dari browser HP yang terhubung ke WiFi yang sama.

---

## 🖱️ Contoh Penggunaan

1. **Tab "Sandikan Pesan"** — unggah citra cover (PNG/BMP), ketik pesan rahasia, isi kata sandi enkripsi dan stego-key, lalu klik **"Sandikan & Hasilkan Citra"**. Citra cover dan citra stego akan tampil berdampingan, lalu unduh hasilnya lewat tombol **"Unduh Citra Bersandi"**.
2. **Tab "Ungkap Pesan"** — unggah citra stego hasil langkah 1, isi kata sandi dan stego-key yang **SAMA PERSIS** dengan saat menyandikan, lalu klik **"Ungkap Pesan"**. Pesan asli akan tampil kembali. Jika kata sandi/stego-key salah, aplikasi menolak dan menampilkan pesan kesalahan yang jelas (bukan pesan rusak/acak).
3. **Tab "Telisik Visual"** — unggah citra cover atau citra stego untuk melihat visualisasi bidang LSB-nya

---

## 🧪 Menjalankan Unit Test

```bash
pytest tests/ -v
```
Akan menjalankan 8 unit test (melebihi minimal 5 sesuai pedoman tugas): roundtrip enkripsi, roundtrip sandi-ungkap, penolakan kata sandi salah, penolakan stego-key salah, penolakan pesan melebihi kapasitas, perhitungan kapasitas, dan deteksi tamper.

---

## 📊 Menjalankan Pengujian Kuantitatif Wajib (PSNR, MSE, Histogram, Chi-Square, JPEG)

1. Taruh **minimal 5 citra PNG/BMP berbeda karakter** (misalnya: foto natural, noise, gradasi, blok warna, tekstur ramai) di folder `sample_images/`.
2. Jalankan:
   ```bash
   cd testing
   python run_full_test.py
   ```
3. Skrip otomatis menguji setiap citra × 3 ukuran pesan (kecil/sedang/besar), lalu menyimpan hasil ke:
   - `testing/hasil_pengujian.xlsx` — tabel PSNR, MSE, chi-square, status ekstraksi, dan ketahanan JPEG
   - `testing/histogram_comparison.png` — grafik perbandingan histogram cover vs stego

---

## 🔒 Catatan Keamanan

- Kunci/kata sandi **tidak pernah** ditulis langsung di kode sumber; semuanya diinput pengguna saat aplikasi berjalan (runtime).
- Salt dan nonce AES dibangkitkan dengan `os.urandom` (generator acak aman secara kriptografis); posisi pixel PRNG di-*seed* dari stego-key sebagai "kunci kedua" yang independen dari kata sandi enkripsi.
- Mode ECB dan algoritma usang (MD5, SHA-1, DES, RC4) **tidak** dipakai untuk fitur keamanan utama aplikasi.
- File `.env`, `venv/`, dan cache tidak ikut ter-*commit* ke repositori (lihat `.gitignore`).

---

#Bagian yang Dibantu AI

bagian yang dibantu asisten AI (Claude):
- Kerangka awal backend Flask (`app.py`) dan modul inti kriptografi/steganografi (`stego_core.py`).
- Skrip pengujian otomatis (`testing/run_full_test.py`, `testing/metrics.py`).
- Draf desain antarmuka (`templates/`, `static/`) dan dokumen pendukung (panduan, laporan).

Seluruh kode telah dijalankan, diuji ulang (`pytest tests/ -v` — 8/8 lulus)