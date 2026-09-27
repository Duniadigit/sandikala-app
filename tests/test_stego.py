"""
test_stego.py — Unit test wajib (minimal 5) untuk fungsi inti.
Jalankan dari root folder: pytest -v
"""
import os
import sys

import pytest
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from stego_core import (  # noqa: E402
    StegoError,
    capacity_bytes,
    embed_message,
    extract_message,
    encrypt_message,
    decrypt_message,
)

PASSWORD = "SandiUji123!"
STEGO_KEY = "kunci-uji"


@pytest.fixture
def cover_image():
    # citra sintetis 64x64 supaya test cepat & tidak butuh file eksternal
    return Image.new("RGB", (64, 64), color=(120, 130, 140))


def test_encrypt_decrypt_roundtrip():
    msg = b"pesan rahasia"
    payload = encrypt_message(msg, PASSWORD)
    assert decrypt_message(payload, PASSWORD) == msg


def test_decrypt_wrong_password_fails():
    payload = encrypt_message(b"data", PASSWORD)
    with pytest.raises(StegoError):
        decrypt_message(payload, "password-salah")


def test_embed_extract_roundtrip(cover_image):
    msg = "Halo, ini pesan rahasia!"
    result = embed_message(cover_image, msg.encode(), PASSWORD, STEGO_KEY)
    extracted = extract_message(result.stego_image, PASSWORD, STEGO_KEY)
    assert extracted.decode() == msg


def test_extract_wrong_password_rejected(cover_image):
    result = embed_message(cover_image, b"rahasia", PASSWORD, STEGO_KEY)
    with pytest.raises(StegoError):
        extract_message(result.stego_image, "salah-password", STEGO_KEY)


def test_extract_wrong_stego_key_rejected(cover_image):
    result = embed_message(cover_image, b"rahasia", PASSWORD, STEGO_KEY)
    with pytest.raises(StegoError):
        extract_message(result.stego_image, PASSWORD, "kunci-salah")


def test_capacity_rejects_oversized_message(cover_image):
    huge_message = b"A" * 100_000  # jauh melebihi kapasitas citra 64x64
    with pytest.raises(StegoError):
        embed_message(cover_image, huge_message, PASSWORD, STEGO_KEY)


def test_capacity_bytes_calculation():
    # 10x10 RGB -> 10*10*3 bit kapasitas = 300 bit = 37.5 byte -> floor 37
    assert capacity_bytes(10, 10) == 37


def test_tamper_detection(cover_image):
    result = embed_message(cover_image, b"data penting", PASSWORD, STEGO_KEY)
    stego = result.stego_image
    px = stego.load()
    # ubah 1 pixel drastis di luar area header untuk mensimulasikan gangguan
    x, y = stego.size[0] - 1, stego.size[1] - 1
    r, g, b = px[x, y]
    px[x, y] = (255 - r, 255 - g, 255 - b)
    # tidak selalu menyebabkan error (tergantung posisi kena payload atau tidak),
    # tapi jika kena, harus StegoError, bukan crash lain / bukan sukses diam-diam
    try:
        extracted = extract_message(stego, PASSWORD, STEGO_KEY)
        # bila posisi yang diubah bukan bagian payload, pesan tetap benar
        assert extracted == b"data penting"
    except StegoError:
        pass  # sesuai spesifikasi: perubahan bit -> gagal verifikasi tag GCM
