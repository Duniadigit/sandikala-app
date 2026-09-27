"""metrics.py — MSE, PSNR, dan histogram untuk pengujian wajib topik B."""
import numpy as np
from PIL import Image


def mse(img_a: Image.Image, img_b: Image.Image) -> float:
    a = np.asarray(img_a.convert("RGB"), dtype=np.float64)
    b = np.asarray(img_b.convert("RGB"), dtype=np.float64)
    return float(np.mean((a - b) ** 2))


def psnr(img_a: Image.Image, img_b: Image.Image, max_pixel: float = 255.0) -> float:
    m = mse(img_a, img_b)
    if m == 0:
        return float("inf")
    return 20 * np.log10(max_pixel) - 10 * np.log10(m)


def histogram(img: Image.Image):
    """Return dict channel -> np.array(256,) of pixel counts."""
    arr = np.asarray(img.convert("RGB"))
    return {
        "R": np.bincount(arr[:, :, 0].ravel(), minlength=256),
        "G": np.bincount(arr[:, :, 1].ravel(), minlength=256),
        "B": np.bincount(arr[:, :, 2].ravel(), minlength=256),
    }


def chi_square_lsb(img: Image.Image) -> float:
    """
    Uji chi-square sederhana ala Westfeld & Pfitzmann untuk mendeteksi LSB:
    membandingkan frekuensi pasangan nilai (2i, 2i+1) yang seharusnya mendekati
    sama pada citra ber-LSB acak. Mengembalikan statistik chi-square (semakin
    tinggi => indikasi penyisipan LSB semakin kuat, bukan p-value pasti).
    """
    arr = np.asarray(img.convert("L")).ravel()
    counts = np.bincount(arr, minlength=256).astype(np.float64)
    chi2 = 0.0
    for i in range(128):
        obs0, obs1 = counts[2 * i], counts[2 * i + 1]
        expected = (obs0 + obs1) / 2.0
        if expected > 0:
            chi2 += ((obs0 - expected) ** 2) / expected
    return float(chi2)
