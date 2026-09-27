# Sandikala — Aplikasi Steganografi LSB Aman
### *"Sandi yang bersembunyi di setiap kala"*

Tugas Proyek Aplikasi Kriptografi — Topik B (Steganografi)
Mata Kuliah Keamanan Informasi — Program Studi Informatika, Universitas Siliwangi

## Anggota Kelompok
| Nama | NPM |
|---|---|
| (Adam Malik Rizkiyansyah) | (247006111001) |
| (Farhan Ramadhan) | (247006111 023) |
| (Sahrul Ramdani) | (247006111005) |

## Deskripsi
Aplikasi web untuk menyisipkan (embed) dan mengekstraksi (extract) pesan teks rahasia
ke/dari citra PNG/BMP menggunakan **metode LSB (Least Significant Bit)** dengan:
- posisi pixel yang **diacak** memakai PRNG yang di-seed dari *stego-key*,
- pesan **dienkripsi AES-256-GCM** (kunci diturunkan dari kata sandi via PBKDF2-HMAC-SHA256 + salt acak)
  sebelum disisipkan,
- header 32-bit penanda panjang pesan agar ekstraksi berhenti tepat,
- perhitungan & penolakan otomatis bila pesan melebihi kapasitas citra.

## Arsitektur
```
stego-app/
├── app.py                # Backend Flask (routing + API JSON)
├── stego_core.py          # Logika inti: AES-GCM + LSB PRNG (ditulis sendiri)
├── requirements.txt
├── templates/index.html   # Halaman utama (3 tab: sisipkan/ekstrak/analisis)
├── static/css/style.css
├── static/js/app.js       # Panggilan AJAX ke API
├── tests/test_stego.py    # 8 unit test (pytest)
├── testing/
│   ├── metrics.py          # PSNR, MSE, histogram, chi-square
│   └── run_full_test.py    # Menjalankan seluruh pengujian wajib -> Excel
└── sample_images/          # Taruh minimal 5 citra uji PNG/BMP di sini
```

## Cara Instalasi
1. Install Python 3.10+ dan VS Code.
2. Buka folder ini di VS Code (`code .`).
3. Buat virtual environment (opsional tapi disarankan):
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```
4. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

## Cara Menjalankan
```bash
python app.py
```
Buka browser ke `http://127.0.0.1:5000`. Antarmuka bersifat **responsif** — bisa dibuka dan digunakan dengan nyaman baik di desktop/laptop maupun di HP/tablet (tampilan otomatis menyesuaikan lebar layar).

## Contoh Penggunaan
1. Tab **Sisipkan Pesan**: unggah citra cover PNG, isi pesan, kata sandi, dan stego-key,
   klik "Sisipkan". Unduh `sandikala-stego.png` yang dihasilkan.
2. Tab **Ekstrak Pesan**: unggah `sandikala-stego.png`, isi kata sandi & stego-key yang SAMA persis,
   klik "Ekstrak Pesan". Pesan akan tampil bila kata sandi & stego-key benar; jika salah,
   aplikasi menolak dengan pesan error.
3. Tab **Steganalisis Visual**: unggah citra cover atau stego untuk melihat bidang LSB-nya.

## Menjalankan Unit Test
```bash
pytest tests/ -v
```

## Menjalankan Pengujian Kuantitatif Wajib (PSNR, MSE, histogram, chi-square, JPEG)
1. Taruh minimal 5 citra PNG/BMP berbeda di `sample_images/`.
2. ```bash
   cd testing
   python run_full_test.py
   ```
3. Hasil tersimpan di `testing/hasil_pengujian.xlsx` dan `testing/histogram_comparison.png`.

## Catatan Keamanan
- Kunci/kata sandi tidak pernah ditulis di kode sumber; semuanya diinput pengguna saat runtime.
- Salt, nonce, dan posisi pixel PRNG memakai sumber acak — salt & nonce dengan `os.urandom`
  (secrets-grade), stego-key ditentukan pengguna sebagai "kunci kedua" independen dari password AES.
- Mode ECB dan algoritma usang (MD5/SHA-1/DES/RC4) tidak dipakai untuk fitur keamanan utama.

