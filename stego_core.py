"""
stego_core.py
====================================================
Inti logika Steganografi LSB (ditulis sendiri sesuai ketentuan tugas)
+ Enkripsi AES-256-GCM (memakai pustaka teruji `cryptography`, sesuai ketentuan
  bahwa algoritma modern WAJIB memakai pustaka yang sudah teruji).

Alur:
  pesan (teks) --AES-256-GCM--> ciphertext -> [header 4 byte panjang] + ciphertext
  -> disisipkan ke bit LSB pixel citra pada POSISI YANG DIACAK
     memakai PRNG (Python `random.Random`) yang di-seed dari stego-key.

Ekstraksi adalah kebalikannya: seed PRNG yang sama -> urutan posisi pixel yang
sama -> baca 32 bit pertama (header panjang) -> baca N byte ciphertext -> AES
decrypt. Jika stego-key salah, seed berbeda -> posisi bit berbeda -> AES-GCM
tag verification gagal -> ekstraksi ditolak.
"""

from __future__ import annotations

import os
import random
import struct
from dataclasses import dataclass

from PIL import Image
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# ---------------------------------------------------------------------------
# Parameter kriptografi
# ---------------------------------------------------------------------------
PBKDF2_ITERATIONS = 200_000
SALT_LEN = 16          # bytes
NONCE_LEN = 12         # bytes, standar untuk AES-GCM
AES_KEY_LEN = 32       # 256 bit
HEADER_LEN_BITS = 32   # 32-bit header = panjang payload dalam byte (maks ~4 GB)


class StegoError(Exception):
    """Dipakai untuk semua kegagalan yang harus ditolak aplikasi (bukan crash)."""


# ---------------------------------------------------------------------------
# 1. Derivasi kunci dari kata sandi (PBKDF2-HMAC-SHA256 + salt acak)
# ---------------------------------------------------------------------------
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=AES_KEY_LEN,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


# ---------------------------------------------------------------------------
# 2. Enkripsi / dekripsi pesan dengan AES-256-GCM
#    Format payload = salt(16) || nonce(12) || ciphertext_dan_tag
# ---------------------------------------------------------------------------
def encrypt_message(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(SALT_LEN)          # acak, secrets-grade (os.urandom)
    nonce = os.urandom(NONCE_LEN)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return salt + nonce + ct


def decrypt_message(payload: bytes, password: str) -> bytes:
    if len(payload) < SALT_LEN + NONCE_LEN:
        raise StegoError("Payload rusak/terlalu pendek.")
    salt = payload[:SALT_LEN]
    nonce = payload[SALT_LEN:SALT_LEN + NONCE_LEN]
    ct = payload[SALT_LEN + NONCE_LEN:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ct, associated_data=None)
    except Exception as exc:  # tag GCM tidak valid -> kata sandi salah / data diubah
        raise StegoError("Dekripsi gagal: kata sandi salah atau data telah diubah.") from exc


# ---------------------------------------------------------------------------
# 3. Utilitas kapasitas
# ---------------------------------------------------------------------------
def capacity_bits(width: int, height: int, channels: int = 3) -> int:
    """1 bit LSB per kanal warna yang dipakai (RGB, alpha tidak dipakai)."""
    return width * height * channels


def capacity_bytes(width: int, height: int, channels: int = 3) -> int:
    return capacity_bits(width, height, channels) // 8


# ---------------------------------------------------------------------------
# 4. PRNG posisi pixel dari stego-key (bukan dari password AES -> key terpisah
#    supaya kompromi salah satu tidak otomatis membuka yang lain)
# ---------------------------------------------------------------------------
def _prng_positions(total_slots: int, n_needed: int, stego_key: str) -> list[int]:
    if n_needed > total_slots:
        raise StegoError("Pesan melebihi kapasitas citra.")
    rng = random.Random(stego_key)  # seed deterministik dari stego-key (string)
    positions = list(range(total_slots))
    rng.shuffle(positions)
    return positions[:n_needed]


# ---------------------------------------------------------------------------
# 5. Bit <-> byte helpers
# ---------------------------------------------------------------------------
def _bytes_to_bits(data: bytes) -> list[int]:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        out.append(byte)
    return bytes(out)


# ---------------------------------------------------------------------------
# 6. Embed / extract pada array pixel
# ---------------------------------------------------------------------------
@dataclass
class EmbedResult:
    stego_image: Image.Image
    bits_used: int
    capacity_bits: int


def embed_message(cover_img: Image.Image, message: bytes, password: str, stego_key: str) -> EmbedResult:
    img = cover_img.convert("RGB")
    w, h = img.size
    pixels = bytearray(img.tobytes())  # urutan R,G,B,R,G,B,...

    encrypted = encrypt_message(message, password)
    header = struct.pack(">I", len(encrypted))  # 4 byte big-endian = panjang ciphertext
    payload = header + encrypted
    bits = _bytes_to_bits(payload)

    total_slots = len(pixels)  # 1 slot = 1 byte warna = 1 bit LSB
    cap_bits = total_slots
    if len(bits) > cap_bits:
        raise StegoError(
            f"Pesan terenkripsi butuh {len(bits)} bit, kapasitas citra hanya {cap_bits} bit."
        )

    positions = _prng_positions(total_slots, len(bits), stego_key)
    for pos, bit in zip(positions, bits):
        pixels[pos] = (pixels[pos] & 0xFE) | bit

    stego_img = Image.frombytes("RGB", (w, h), bytes(pixels))
    return EmbedResult(stego_image=stego_img, bits_used=len(bits), capacity_bits=cap_bits)


def extract_message(stego_img: Image.Image, password: str, stego_key: str) -> bytes:
    img = stego_img.convert("RGB")
    pixels = img.tobytes()
    total_slots = len(pixels)

    # 1) baca header 32 bit di posisi PRNG pertama
    header_positions = _prng_positions(total_slots, HEADER_LEN_BITS, stego_key)
    header_bits = [pixels[p] & 1 for p in header_positions]
    header_bytes = _bits_to_bytes(header_bits)
    (payload_len,) = struct.unpack(">I", header_bytes)

    max_reasonable = total_slots // 8
    if payload_len <= 0 or payload_len > max_reasonable:
        raise StegoError("Header pesan tidak valid (stego-key kemungkinan salah).")

    total_needed_bits = HEADER_LEN_BITS + payload_len * 8
    if total_needed_bits > total_slots:
        raise StegoError("Header pesan tidak valid (stego-key kemungkinan salah).")

    all_positions = _prng_positions(total_slots, total_needed_bits, stego_key)
    payload_positions = all_positions[HEADER_LEN_BITS:]
    payload_bits = [pixels[p] & 1 for p in payload_positions]
    encrypted = _bits_to_bytes(payload_bits)

    return decrypt_message(encrypted, password)  # raises StegoError jika password salah


# ---------------------------------------------------------------------------
# 7. Visualisasi bidang LSB (untuk steganalisis visual wajib)
# ---------------------------------------------------------------------------
def lsb_plane_image(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    w, h = rgb.size
    data = bytearray(rgb.tobytes())
    out = bytearray(len(data))
    for i, v in enumerate(data):
        out[i] = 255 if (v & 1) else 0
    return Image.frombytes("RGB", (w, h), bytes(out))
