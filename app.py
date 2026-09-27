"""
app.py — Backend Flask untuk Aplikasi Steganografi (Topik B)

Endpoint:
  POST /api/capacity   -> hitung kapasitas maksimum citra cover
  POST /api/embed      -> sisipkan pesan (dienkripsi AES-256-GCM) ke citra -> stego PNG
  POST /api/extract    -> ekstraksi pesan dari citra stego
  POST /api/lsb-plane  -> kembalikan citra bidang-LSB untuk steganalisis visual

Jalankan:  python app.py   (lihat README.md)
"""

import base64
import io

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image

from stego_core import (
    StegoError,
    capacity_bytes,
    embed_message,
    extract_message,
    lsb_plane_image,
)

app = Flask(__name__, static_folder="static", template_folder="templates")
MAX_UPLOAD_MB = 20
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def _img_to_base64_png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/api/capacity", methods=["POST"])
def api_capacity():
    file = request.files.get("cover")
    if not file:
        return jsonify(error="Citra cover wajib diunggah."), 400
    img = Image.open(file.stream).convert("RGB")
    w, h = img.size
    cap = capacity_bytes(w, h)
    # sisakan ruang untuk header 4 byte + overhead AES (salt16+nonce12+tag16=44 byte)
    usable = max(cap - 4 - 44, 0)
    return jsonify(width=w, height=h, capacity_bytes=cap, usable_message_bytes=usable)


@app.route("/api/embed", methods=["POST"])
def api_embed():
    file = request.files.get("cover")
    message = request.form.get("message", "")
    password = request.form.get("password", "")
    stego_key = request.form.get("stego_key", "")

    if not file or not message or not password or not stego_key:
        return jsonify(error="cover, message, password, dan stego_key wajib diisi."), 400

    try:
        cover_img = Image.open(file.stream)
        result = embed_message(cover_img, message.encode("utf-8"), password, stego_key)
    except StegoError as e:
        return jsonify(error=str(e)), 422
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"Gagal memproses citra: {e}"), 400

    return jsonify(
        stego_png_base64=_img_to_base64_png(result.stego_image),
        cover_png_base64=_img_to_base64_png(cover_img.convert("RGB")),
        bits_used=result.bits_used,
        capacity_bits=result.capacity_bits,
    )


@app.route("/api/extract", methods=["POST"])
def api_extract():
    file = request.files.get("stego")
    password = request.form.get("password", "")
    stego_key = request.form.get("stego_key", "")

    if not file or not password or not stego_key:
        return jsonify(error="stego, password, dan stego_key wajib diisi."), 400

    try:
        stego_img = Image.open(file.stream)
        plaintext = extract_message(stego_img, password, stego_key)
    except StegoError as e:
        # Kegagalan yang DIHARAPKAN (kata sandi/stego-key salah, data diubah)
        return jsonify(error=str(e)), 422
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"Gagal memproses citra: {e}"), 400

    return jsonify(message=plaintext.decode("utf-8", errors="replace"))


@app.route("/api/lsb-plane", methods=["POST"])
def api_lsb_plane():
    file = request.files.get("image")
    if not file:
        return jsonify(error="Citra wajib diunggah."), 400
    img = Image.open(file.stream)
    plane = lsb_plane_image(img)
    return jsonify(image_base64=_img_to_base64_png(plane))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
