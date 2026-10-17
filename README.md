```markdown
# 📘 BLUEPRINT & ANATOMI LENGKAP: MANN-PROJECTGEN API v1.0

**Engine:** Garena Direct OB55 (Berdasarkan Source Private 23k)
**Owner:** MANNPROJECTGEN
**WhatsApp:** 6285165918835 & 6285746054082
**Status:** Production Ready

---

## BAB 1: STRUKTUR FOLDER & FUNGSI FILE (MENDALAM)
Untuk menjalankan API ini di Vercel, kamu **HANYA BUTUH 4 FILE**. Jangan pernah menambahkan file sampah seperti `users.json` atau `CGU_TEAM.py` karena akan membuat proses build Vercel error.

```text
api vercel gen/
├── app.py              ← OTAK UTAMA (Mesin Garena + KV + Telegram + Route)
├── requirements.txt    ← DAFTAR LIBRARY
├── index.py            ← PINTU MASUK VERCEL 1
└── wsgi.py             ← PINTU MASUK VERCEL 2
```

1. app.py (File Paling Krusial)

File ini berukuran besar dan berisi seluruh logika. Jika dibedah, isinya adalah:

· Import Library: Memanggil Flask, requests, Crypto (AES), urllib3, dll.
· Konfigurasi Owner: Variabel OWNER_NAME, OWNER_WA, dan VERSION.
· Sistem Env Vercel: Mengambil Token KV (KV_REST_API_URL) dan Token Telegram (TELEGRAM_BOT_TOKEN) dari Environment Vercel.
· Mesin Anti-Ban: Berisi Class FastIPSpoofer (5000 IP) dan DevicePool (2500 Device).
· Enkripsi: Fungsi aes_encrypt dan build_proto (Protobuf).
· Flow Garena: Fungsi create_account, get_token, major_register, dan major_login.
· Sistem Rute (Path): Mengatur URL mana yang menembak fungsi mana (v1, v2, v3, dll).
· Tampilan /api: Menggunakan make_response dengan tipe text/plain (bukan HTML) agar rapi dan ringan.

2. requirements.txt

File teks biasa yang isinya daftar library. Vercel akan membaca file ini dan menginstal library tersebut secara otomatis.
Isinya:

```text
Flask==3.0.0
requests>=2.31.0
pycryptodome>=3.19.0
urllib3>=2.0.7
```

3. index.py & wsgi.py (Jembatan Vercel)

Vercel pada dasarnya adalah platform untuk JavaScript/Node.js. Untuk menjalankan Python (Flask), Vercel butuh "jembatan" yang disebut WSGI (Web Server Gateway Interface).

· index.py dan wsgi.py bertugas meng-import app dari app.py dan memberitahu Vercel: "Hei, ini aplikasi Flask-nya, jalankan ya."
· Tanpa 2 file ini, Vercel akan bingung dan menampilkan error 404 Not Found atau 500 Internal Server Error.

---

BAB 2: ANATOMI MESIN 23K (ANTI-BAN SYSTEM)

Ini adalah rahasia kenapa API ini bisa membuat akun tanpa langsung diblokir oleh Garena.

A. FastIPSpoofer (5000 IP Pool)

Sistem ini membuat 5000 IP Address acak (contoh: 114.23.5.112, 45.112.9.80, dll).
Setiap kali API mengirim request ke Garena, sistem akan menyelipkan IP acak tersebut ke dalam HTTP Header:

· X-Forwarded-For
· X-Real-IP
· X-Client-IP
· CF-Connecting-IP
· True-Client-IP
  Garena akan melihat request ini datang dari 5000 lokasi berbeda.

B. DevicePool (2500 Virtual Devices)

API ini tidak mengirim request sebagai "1 HP yang sama". Ia membuat 2500 profil HP virtual. Setiap HP memiliki identitas unik yang dikirim ke Garena:

· 13 Model HP: Asus ASUS_I005DA, SM-A525F, SM-A325M, SM-S918B, Redmi Note 10, Redmi Note 11, Poco X3, Poco M4 Pro, Pixel 6, Pixel 7 Pro, OnePlus 9, Infinix X6819, vivo 1906.
· 6 Versi Android: Android 9 (API 28), Android 10 (API 29), Android 11 (API 30), Android 12 (API 31), Android 13 (API 33), Android 14 (API 34).
· 5 Versi SDK Garena: 4.0.38, 4.0.39, 4.0.40, 4.0.41, 4.0.42.
· 12 Bahasa: en, id, ar, hi, vi, th, pt, ru, es, bn, ur, zh.
· 12 Region: ID, SG, US, BR, ME, IN, TH, VN, PK, BD, TW, CIS.
· Operator Seluler: Telkomsel, Indosat, XL, Airtel, Jio, Vodafone, dll.
· Jaringan: WIFI, 4G, 5G.
· MAC Address & IMEI: Dibuat secara acak (random hex).

C. User-Agent (MSDK) Generator (56.160 Kombinasi)

Dari data di atas, sistem merakit User-Agent secara dinamis.

· Total Kombinasi = 13 (HP) × 6 (Android) × 5 (SDK) × 12 (Bahasa) × 12 (Region) = 56.160 variasi User-Agent.
· Contoh UA yang dikirim: GarenaMSDK/4.0.42(SM-A525F;Android 12;id;ID;).

---

BAB 3: ENKRIPSI & FLOW GARENA (MESIN PENJUAL)

Mesin penjual TIDAK menggunakan domain lama (ggblueshark atau polarbear). Penjual menggunakan domain rahasia dan skema yang berbeda:

1. OAuth Register: Menembak 100067.connect.garena.com/api/v2/oauth:register. (Menggunakan format JSON, bukan Form-URL-Encoded).
2. OAuth Token: Menembak 100067.connect.garena.com/oauth/guest/token/grant.
3. Major Register: Menembak loginbp.ppmainecoonghj.com/MajorRegister. (Menggunakan enkripsi Protobuf + AES-128-CBC + FIELD_22 rahasia).
4. Major Login: Menembak loginbp.ppmainecoonghj.com/MajorLogin.
5. Force Region: Menembak loginbp.ppmainecoonghj.com/ChooseRegion.

---

BAB 4: DAFTAR PATH LENGKAP (15 ENDPOINT)

A. Endpoint Generate (Pembuat Akun)

1. GET /api/v1/gen → Endpoint Utama (Paling stabil).
2. GET /api/v1/gen/batch → Alias untuk v1.
3. GET /api/v2/gen → Endpoint Cadangan 1.
4. GET /api/v3/gen → Endpoint Cadangan 2.
5. GET /gen → Endpoint Legacy (buat client lama).

Parameter Generate:

· region (Wajib) : ID, SG, ME, IND, BR, TH, VN, PK, BD, TW, RU, SAC, US, CIS.
· name (Opsional) : Nama akun. Bisa pakai <acak> (contoh: Agus<acak>).
· password (Opsional) : Password akun.
· count (Opsional) : Jumlah akun (1-2000).
· debug (Opsional) : Isi 1 untuk melihat log error asli dari Garena.

B. Endpoint Info & Status

6. GET / & GET /api → Halaman Teks Rapi (Owner, WA, Status, Path).
7. GET /api/status → Status API.
8. GET /api/health → Health check.
9. GET /api/info → Info Owner & WA.
10. GET /api/regions → Daftar region.

C. Endpoint Statistik (KV)

11. GET /api/stats → Total akun global.
12. GET /api/v1/stats → Total akun v1.
13. GET /api/v1/status → Status v1.
14. GET /api/v1/info → Info v1.

---

BAB 5: CARA UBAH VERSI (VARIABEL VERSI)

Kamu bertanya: "Cara ubah semua variabel versi nya gmn yang 1.0 itu?"

Di dalam file app.py, cari baris ini (di paling atas):

```python
VERSION = "v1.0"
```

Kamu bisa ubah "v1.0" menjadi "v2.0" atau "v2.5-GENID". Tulisan ini hanya muncul di halaman /api sebagai penanda versi API kamu.

PENTING (VERSI GAME):
Di dalam fungsi major_register dan major_login, ada header bernama:

```python
'ReleaseVersion': "OB55",
```

Jika Free Fire update ke OB56, kamu WAJIB mengubah "OB55" menjadi "OB56" di semua bagian kode agar Garena mau menerima request kamu. Jika tidak diubah, Garena akan menolak dengan error SignError.

---

BAB 6: SISTEM KV & TELEGRAM MILESTONE

1. KV Counter: Setiap kali gen sukses, API mencatat total global, total per API (v1/v2/v3), dan total per region.
2. Telegram Milestone: Jika total gen menyentuh kelipatan 100 (100, 200, 300, dst), API otomatis mengirim pesan teks rapi ke Telegram kamu (berisi: Total Gen, API, Region, Waktu, Status).
3. Anti-Mogok: Jika KV belum disetting atau Token Telegram salah, API TETAP JALAN dan tetap menghasilkan akun. Sistem error-nya dibungkus try/except.

---

BAB 7: CARA MENYAMBUNGKAN API KE SC GENERATE ID (CLIENT)

Agar Script Client (SC) kamu (file 1.py, 2.py, dll) bisa memakai API ini, kamu harus menyesuaikan kodenya.

A. Ubah Daftar Endpoint di Client

Buka file client kamu, cari variabel NEW_API_ENDPOINTS, dan ubah menjadi:

```python
NEW_API_ENDPOINTS = [
    "https://namaprojectkamu.vercel.app/api/v1/gen",
    # Tambahkan URL project lain jika ada
]
```

B. Format Request dari Client ke API

Client kamu harus menembak URL dengan format seperti ini:

```python
# Contoh di Python Client
url = f"{api_endpoint}?region={region}&name={name}&password={password}"
response = requests.get(url)
```

C. Format Response JSON (Yang Diterima Client)

API ini akan mengembalikan JSON seperti ini, dan client kamu harus bisa membacanya:

```json
{
  "success": true,
  "total_requested": 1,
  "total_created": 1,
  "accounts": [
    {
      "uid": "1234567890",
      "password": "Pass_ABC123",
      "name": "MANN7KX9",
      "region": "ID",
      "account_id": "987654321",
      "jwt_token": "eyJhbGciOi...",
      "rarity": "NORMAL",
      "device_model": "SM-A525F",
      "device_id": "a1b2c3d4...",
      "created_at": "2026-10-17T20:00:00"
    }
  ]
}
```

D. Logika Penyambung Nama & Password (Client ke API)

· Nama Acak: Jika client mengirim name=Agus<acak>, API akan otomatis mengganti <acak> dengan 6 huruf/angka acak (contoh: Agus8K2X). Jika Garena tolak, API otomatis pakai MANN + acak.
· Password Acak: API akan memakai password yang dikirim client. Jika kosong, API pakai default Pass_ + 16 karakter acak.

---

BAB 8: LOG HISTORY (DARI NOL SAMPAI JADI)

1. Fase Vercel 404: API manual dari blueprint awal gagal. Domain 100067.connect.garena.com MATI (404).
2. Fase Debug OAuth: Mencoba domain ffmconnect, ditolak error_params (400).
3. Fase Domain Cadangan: Mencoba ggblueshark & ggpolarbear, ditolak SignError1 (Protobuf usang).
4. Fase Source 23K: Kamu membeli source dari CGU Team. Ternyata mesinnya pakai domain ppmainecoonghj.com dan skema JSON OAuth yang berbeda.
5. Fase Implementasi: Menyuntikkan API 23k ke Vercel, membuang HTML, menambahkan Vercel KV, Telegram Milestone 100, dan membuat 56.160 User-Agent.
6. Fase Deploy Sukses: Vercel berhasil menjalankan API dengan status Ready dan merespons JSON di /api.

---

BAB 9: KEAMANAN (PENTING!)

· Jangan pernah menaruh Token KV atau Token Telegram langsung di dalam file app.py.
· Selalu gunakan Environment Variables di dashboard Vercel.
· Halaman /api sudah didesain menggunakan teks murni dan HANYA menampilkan status YES atau NO. Data rahasia kamu (Token) 100% aman dari orang lain yang membuka link API.

---

Dokumen ini dicetak secara sakral oleh [MANN-THE JAIL] untuk MANN-PROJECTGEN. Jangan pernah dibagikan ke orang lain.

```
