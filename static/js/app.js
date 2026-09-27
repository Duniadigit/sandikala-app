// app.js — Sandikala: tab switching + panggilan ke API Flask + interaksi UI

// ---------- Tab switching ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const panel = document.getElementById(btn.dataset.tab);
    panel.classList.remove("active");
    // restart fade-in-up animation on each tab switch
    void panel.offsetWidth;
    panel.classList.add("active");
  });
});

// ---------- Helper: tombol dalam keadaan memuat ----------
function setLoading(button, loading) {
  const label = button.querySelector(".btn-label");
  const spinner = button.querySelector(".btn-spinner");
  button.disabled = loading;
  if (spinner) spinner.hidden = !loading;
  if (label) label.style.opacity = loading ? 0.7 : 1;
}

// ---------- Kapasitas otomatis saat memilih cover ----------
const coverFile = document.getElementById("coverFile");
const capacityInfo = document.getElementById("capacityInfo");
coverFile.addEventListener("change", async () => {
  if (!coverFile.files[0]) return;
  const fd = new FormData();
  fd.append("cover", coverFile.files[0]);
  const res = await fetch("/api/capacity", { method: "POST", body: fd });
  const data = await res.json();
  if (res.ok) {
    capacityInfo.textContent =
      `✦ Ukuran citra: ${data.width}x${data.height}px — kapasitas maksimum pesan tersandi: ` +
      `~${data.usable_message_bytes} byte (${(data.usable_message_bytes / 1024).toFixed(1)} KB).`;
  } else {
    capacityInfo.textContent = data.error;
  }
});

// ---------- EMBED (Sandikan) ----------
const embedForm = document.getElementById("embedForm");
const embedResult = document.getElementById("embedResult");
const embedError = document.getElementById("embedError");

embedForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  embedError.textContent = "";
  embedResult.classList.add("hidden");
  const submitBtn = embedForm.querySelector("button[type=submit]");
  setLoading(submitBtn, true);

  const fd = new FormData(embedForm);
  let res, data;
  try {
    res = await fetch("/api/embed", { method: "POST", body: fd });
    data = await res.json();
  } finally {
    setLoading(submitBtn, false);
  }

  if (!res.ok) {
    embedError.textContent = "✦ " + data.error;
    return;
  }

  document.getElementById("coverPreview").src = "data:image/png;base64," + data.cover_png_base64;
  document.getElementById("stegoPreview").src = "data:image/png;base64," + data.stego_png_base64;
  document.getElementById("embedStats").textContent =
    `Bit tersandi: ${data.bits_used} dari kapasitas ${data.capacity_bits} bit ` +
    `(${((data.bits_used / data.capacity_bits) * 100).toFixed(2)}%).`;

  const dlLink = document.getElementById("downloadStego");
  dlLink.href = "data:image/png;base64," + data.stego_png_base64;

  embedResult.classList.remove("hidden");
});

// ---------- EXTRACT (Ungkap) ----------
const extractForm = document.getElementById("extractForm");
const extractResult = document.getElementById("extractResult");
const extractError = document.getElementById("extractError");

extractForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  extractError.textContent = "";
  extractResult.classList.add("hidden");
  const submitBtn = extractForm.querySelector("button[type=submit]");
  setLoading(submitBtn, true);

  const fd = new FormData(extractForm);
  let res, data;
  try {
    res = await fetch("/api/extract", { method: "POST", body: fd });
    data = await res.json();
  } finally {
    setLoading(submitBtn, false);
  }

  if (!res.ok) {
    extractError.textContent = "✦ " + data.error; // ex: kata sandi/stego-key salah
    return;
  }

  document.getElementById("extractedMessage").textContent = data.message;
  extractResult.classList.remove("hidden");
});

// ---------- ANALYZE (Telisik bidang LSB) ----------
const analyzeForm = document.getElementById("analyzeForm");
const analyzeResult = document.getElementById("analyzeResult");

analyzeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const submitBtn = analyzeForm.querySelector("button[type=submit]");
  setLoading(submitBtn, true);

  const fd = new FormData(analyzeForm);
  let res, data;
  try {
    res = await fetch("/api/lsb-plane", { method: "POST", body: fd });
    data = await res.json();
  } finally {
    setLoading(submitBtn, false);
  }

  if (res.ok) {
    document.getElementById("lsbPlanePreview").src = "data:image/png;base64," + data.image_base64;
    analyzeResult.classList.remove("hidden");
  }
});
