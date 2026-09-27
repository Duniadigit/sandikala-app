"""
run_full_test.py
====================================================
Menjalankan SELURUH pengujian wajib Topik B dan menyimpan hasil ke
`testing/hasil_pengujian.xlsx` (butuh openpyxl) + grafik PNG.

Cara pakai:
  1. Taruh minimal 5 citra PNG/BMP di folder ../sample_images/
  2. python run_full_test.py

Pengujian yang dijalankan:
  - PSNR & MSE untuk tiap citra x 3 ukuran pesan (kecil/sedang/besar)
  - Perbandingan histogram cover vs stego (disimpan sebagai grafik)
  - Uji kerapuhan: simpan ulang stego sebagai JPEG lalu coba ekstraksi
  - Uji chi-square sederhana pada cover vs stego
"""
import glob
import os
import random
import string
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from stego_core import StegoError, capacity_bytes, embed_message, extract_message  # noqa: E402
from metrics import psnr, mse, histogram, chi_square_lsb  # noqa: E402

HERE = os.path.dirname(__file__)
IMG_DIR = os.path.join(HERE, "..", "sample_images")
OUT_DIR = HERE

PASSWORD = "PasswordUjiCoba123!"
STEGO_KEY = "kunci-rahasia-uji"
MESSAGE_SIZES = {"kecil (50 byte)": 50, "sedang (500 byte)": 500, "besar (2000 byte)": 2000}


def random_message(n_bytes: int) -> str:
    return "".join(random.choice(string.ascii_letters + " .,") for _ in range(n_bytes))


def main():
    images = sorted(glob.glob(os.path.join(IMG_DIR, "*.png")) + glob.glob(os.path.join(IMG_DIR, "*.bmp")))
    if len(images) < 1:
        print(f"Taruh minimal 5 citra PNG/BMP di {IMG_DIR} lalu jalankan ulang.")
        return

    rows = []
    for img_path in images:
        cover = Image.open(img_path)
        w, h = cover.size
        cap = capacity_bytes(w, h)
        for size_label, n_bytes in MESSAGE_SIZES.items():
            if n_bytes + 60 > cap:  # +overhead AES/header kasar
                continue
            msg = random_message(n_bytes)
            result = embed_message(cover, msg.encode(), PASSWORD, STEGO_KEY)
            stego = result.stego_image

            p = psnr(cover, stego)
            m = mse(cover, stego)
            chi_cover = chi_square_lsb(cover)
            chi_stego = chi_square_lsb(stego)

            # uji ekstraksi normal
            extracted = extract_message(stego, PASSWORD, STEGO_KEY)
            ok_extract = extracted.decode() == msg

            # uji kerapuhan: simpan ulang sebagai JPEG lalu coba ekstrak
            jpeg_path = os.path.join(OUT_DIR, "_tmp_resave.jpg")
            stego.convert("RGB").save(jpeg_path, format="JPEG", quality=90)
            survives_jpeg = True
            try:
                extract_message(Image.open(jpeg_path), PASSWORD, STEGO_KEY)
            except StegoError:
                survives_jpeg = False
            os.remove(jpeg_path)

            rows.append({
                "citra": os.path.basename(img_path),
                "ukuran_citra": f"{w}x{h}",
                "ukuran_pesan": size_label,
                "PSNR_dB": round(p, 3) if p != float("inf") else "inf",
                "MSE": round(m, 6),
                "chi_square_cover": round(chi_cover, 2),
                "chi_square_stego": round(chi_stego, 2),
                "ekstraksi_benar": ok_extract,
                "bertahan_setelah_JPEG_q90": survives_jpeg,
            })
            print(rows[-1])

            # simpan histogram pembanding untuk citra pertama & pesan pertama saja
            if img_path == images[0] and size_label == list(MESSAGE_SIZES)[0]:
                _save_histogram_plot(cover, stego, os.path.join(OUT_DIR, "histogram_comparison.png"))

    df = pd.DataFrame(rows)
    xlsx_path = os.path.join(OUT_DIR, "hasil_pengujian.xlsx")
    df.to_excel(xlsx_path, index=False)
    print(f"\nSelesai. Hasil disimpan di: {xlsx_path}")
    print(f"Grafik histogram: histogram_comparison.png")


def _save_histogram_plot(cover, stego, out_path):
    hc, hs = histogram(cover), histogram(stego)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, ch in zip(axes, ["R", "G", "B"]):
        ax.plot(hc[ch], label="cover", alpha=0.7)
        ax.plot(hs[ch], label="stego", alpha=0.7)
        ax.set_title(f"Histogram kanal {ch}")
        ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
