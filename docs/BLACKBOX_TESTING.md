# Dokumentasi Blackbox Testing — Smart Chicken Box (PCB)

> Versi: 1.0.0  
> Terakhir diperbarui: 2026-05-27  
> Project: PKL PCB Smart Kandang / Smart Chicken Box  
> Fokus: Pengujian endpoint API, autentikasi, otorisasi, validasi input, dan response sistem

---

## 1. Ringkasan

Dokumen ini menjelaskan blackbox testing yang digunakan pada project Smart Chicken Box (PCB). Pengujian dilakukan dengan memperlakukan backend sebagai sistem yang menerima input HTTP/API dan mengembalikan output berupa status code serta JSON response.

Pada project ini, sebagian besar test dijalankan melalui `FastAPI TestClient`, sehingga test berinteraksi dengan aplikasi seperti client eksternal yang memanggil endpoint REST API. Test tidak berfokus pada implementasi internal route handler, tetapi pada perilaku yang terlihat dari luar.

Namun, secara teknis test juga memiliki unsur graybox karena data awal dibuat menggunakan fixture database dan model SQLAlchemy. Jadi klasifikasi yang paling akurat adalah:

```text
API-level blackbox testing dengan dukungan fixture internal (graybox).
```

Untuk kebutuhan laporan, pengujian ini dapat disebut sebagai blackbox testing karena fokus utamanya adalah:

- Memberikan input request ke endpoint.
- Memeriksa output response.
- Memastikan aturan akses berjalan sesuai role.
- Memastikan input invalid ditolak.
- Memastikan resource yang tidak ada atau tidak boleh diakses menghasilkan error yang benar.

---

## 2. Tujuan Pengujian

Tujuan blackbox testing pada project ini adalah memastikan backend bekerja sesuai kontrak API dari sudut pandang pengguna/client.

Pengujian mencakup:

1. Autentikasi JWT.
2. Otorisasi berdasarkan role.
3. CRUD dan akses device.
4. Claim, unclaim, register, rename, dan delete device.
5. Assignment user ke device.
6. Pembacaan log sensor dan alert.
7. Kontrol aktuator device.
8. Statistik harian sensor.
9. FCM token register/unregister.
10. Cleanup sensor logs.
11. Health check API.
12. Validasi token security.
13. Validasi input dan parameter query.

---

## 3. Ruang Lingkup Testing

Testing yang ada saat ini berada di folder:

```text
tests/
├── test_device.py
├── test_user.py
├── test_stats.py
└── test_security.py
```

Jumlah test:

| File | Jumlah Test | Area Pengujian |
|------|------------:|----------------|
| `test_device.py` | 49 | Device endpoint, claim, list, logs, control, alert, assignment, update, delete |
| `test_user.py` | 37 | User endpoint, role hierarchy, admin access, FCM token, cleanup logs, health check |
| `test_stats.py` | 23 | Statistik harian sensor, validasi parameter, akses device, data kosong |
| `test_security.py` | 8 | Pembuatan dan verifikasi JWT |
| **Total** | **117** | Backend API dan security |

Hasil eksekusi terakhir:

```text
117 passed in 1.92s
```

---

## 4. Tabel Ringkasan Hasil Blackbox Testing

Tabel berikut merangkum fitur yang diuji, penjelasan pengujian, output yang diharapkan, dan hasil aktual berdasarkan eksekusi unit testing terakhir.

| No | Test yang Diuji | Penjelasan | Output yang Diharapkan | Hasil |
|---:|-----------------|------------|------------------------|-------|
| 1 | Claim device berhasil | Admin mengklaim device yang sudah terdaftar dan belum dimiliki user lain. | Sistem mengembalikan `200 OK`, data device berisi MAC address, nama device, dan `user_id`. | Berhasil |
| 2 | Claim device tidak ditemukan | Admin mencoba mengklaim MAC address yang belum terdaftar. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 3 | Claim device sudah diklaim | Admin mencoba mengklaim device yang sudah punya pemilik. | Sistem mengembalikan `400 Bad Request`. | Berhasil |
| 4 | Claim device oleh user biasa | User role `user` mencoba mengklaim device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 5 | Claim device tanpa login | Request claim dikirim tanpa token autentikasi. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 6 | List device admin | Admin meminta daftar device. | Sistem mengembalikan `200 OK` dan hanya menampilkan device milik admin tersebut. | Berhasil |
| 7 | List device user biasa | User biasa meminta daftar device. | Sistem mengembalikan `200 OK` dengan `data` kosong dan `total = 0`. | Berhasil |
| 8 | List device operator | Operator yang memiliki assignment meminta daftar device. | Sistem mengembalikan `200 OK` dan menampilkan device yang di-assign. | Berhasil |
| 9 | List device super admin | Super admin meminta daftar device. | Sistem mengembalikan `200 OK` dan menampilkan semua device. | Berhasil |
| 10 | List device tanpa login | Request daftar device dikirim tanpa token. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 11 | Baca sensor logs oleh admin | Admin membaca log sensor device miliknya. | Sistem mengembalikan `200 OK` dan jumlah log lebih dari 0. | Berhasil |
| 12 | Baca sensor logs oleh operator | Operator membaca log sensor device yang di-assign. | Sistem mengembalikan `200 OK`. | Berhasil |
| 13 | Baca sensor logs oleh viewer | Viewer membaca log sensor device yang di-assign. | Sistem mengembalikan `200 OK`. | Berhasil |
| 14 | Baca sensor logs oleh user biasa | User biasa mencoba membaca log sensor. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 15 | Baca sensor logs tanpa assignment | Operator tanpa assignment mencoba membaca log device. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 16 | Limit sensor logs | Admin membaca log sensor dengan parameter `limit=3`. | Sistem mengembalikan `200 OK` dan jumlah data maksimal 3. | Berhasil |
| 17 | Kontrol device oleh admin | Admin mengirim perintah kontrol ke device miliknya. | Sistem mengembalikan `200 OK` jika MQTT tersedia atau `500` jika MQTT tidak tersedia di test. | Berhasil |
| 18 | Kontrol device oleh operator | Operator mengirim perintah kontrol ke device assigned. | Sistem mengembalikan `200 OK` jika MQTT tersedia atau `500` jika MQTT tidak tersedia di test. | Berhasil |
| 19 | Kontrol device oleh viewer | Viewer mencoba mengontrol device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 20 | Kontrol device oleh user biasa | User biasa mencoba mengontrol device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 21 | Kontrol device tanpa login | Request kontrol dikirim tanpa token. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 22 | Baca alert device | Admin membaca daftar alert device. | Sistem mengembalikan `200 OK` dan semua data memiliki `is_alert = true`. | Berhasil |
| 23 | Baca alert oleh user biasa | User biasa mencoba membaca alert device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 24 | Unclaim device oleh admin | Admin melepas kepemilikan device miliknya. | Sistem mengembalikan `200 OK` dan `status = success`. | Berhasil |
| 25 | Unclaim device oleh user biasa | User biasa mencoba unclaim device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 26 | Unclaim device tanpa login | Request unclaim dikirim tanpa token. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 27 | Assign operator | Admin memberi akses operator ke user pada device miliknya. | Sistem mengembalikan `200 OK` dan `role = operator`. | Berhasil |
| 28 | Assign viewer | Admin memberi akses viewer ke user pada device miliknya. | Sistem mengembalikan `200 OK` dan `role = viewer`. | Berhasil |
| 29 | Assign ke device milik admin lain | Admin mencoba assign user ke device yang bukan miliknya. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 30 | Assign oleh user biasa | User biasa mencoba assign user ke device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 31 | Duplicate assignment | Admin mencoba assign user yang sudah memiliki assignment pada device yang sama. | Sistem mengembalikan `400 Bad Request`. | Berhasil |
| 32 | Unassign user | Admin mencabut assignment user dari device. | Sistem mengembalikan `200 OK`. | Berhasil |
| 33 | Lihat daftar assignment | Admin melihat daftar user yang di-assign ke device. | Sistem mengembalikan `200 OK` dan response berupa array assignment. | Berhasil |
| 34 | Super admin assign device manapun | Super admin memberi assignment pada device manapun. | Sistem mengembalikan `200 OK`. | Berhasil |
| 35 | Lihat semua device oleh super admin | Super admin membuka endpoint `/api/devices/all`. | Sistem mengembalikan `200 OK` dan menampilkan semua device. | Berhasil |
| 36 | Lihat semua device oleh admin | Admin membuka endpoint `/api/devices/all`. | Sistem mengembalikan `200 OK` dan menampilkan device miliknya serta device unclaimed. | Berhasil |
| 37 | Lihat semua device oleh user biasa | User biasa membuka endpoint `/api/devices/all`. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 38 | Rename device oleh admin | Admin mengganti nama device miliknya. | Sistem mengembalikan `200 OK` dan nama device berubah. | Berhasil |
| 39 | Rename device oleh super admin | Super admin mengganti nama device manapun. | Sistem mengembalikan `200 OK` dan nama device berubah. | Berhasil |
| 40 | Rename device milik user lain | Admin mencoba rename device milik admin lain. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 41 | Rename device oleh user biasa | User biasa mencoba rename device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 42 | Rename dengan nama kosong | Admin mengirim nama kosong atau hanya spasi. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 43 | Rename dengan nama terlalu panjang | Admin mengirim nama lebih dari 100 karakter. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 44 | Delete device oleh super admin | Super admin menghapus device. | Sistem mengembalikan `200 OK` dan `status = success`. | Berhasil |
| 45 | Delete device oleh admin | Admin biasa mencoba delete device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 46 | Delete device oleh user biasa | User biasa mencoba delete device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 47 | Delete device tidak ditemukan | Super admin menghapus device ID yang tidak ada. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 48 | Delete device beserta sensor logs | Super admin menghapus device yang memiliki log sensor. | Sistem mengembalikan `200 OK` dan device tidak muncul lagi pada list. | Berhasil |
| 49 | Profile user dengan token valid | User mengambil profil dirinya sendiri. | Sistem mengembalikan `200 OK`, email dan role sesuai. | Berhasil |
| 50 | Profile tanpa token | Request profil dikirim tanpa token. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 51 | Profile dengan token invalid | Request profil memakai token tidak valid. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 52 | Profile dengan token expired | Request profil memakai token yang sudah expired. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 53 | Profile dengan token malformed | Request profil memakai token rusak. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 54 | Field role pada profile | Profile semua role dicek: user, admin, super_admin, operator, viewer. | Sistem mengembalikan field `role` sesuai role user. | Berhasil |
| 55 | Super admin ubah role | Super admin mengubah role user. | Sistem mengembalikan `200 OK` dan role berubah. | Berhasil |
| 56 | Admin ubah role terbatas | Admin mengubah user menjadi operator, viewer, atau user. | Sistem mengembalikan `200 OK`. | Berhasil |
| 57 | Admin promote ke admin | Admin mencoba menjadikan user sebagai admin. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 58 | Admin promote ke super admin | Admin mencoba menjadikan user sebagai super_admin. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 59 | Admin ubah role super admin | Admin mencoba mengubah role super_admin. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 60 | Ubah role diri sendiri | Admin mencoba mengubah role dirinya sendiri. | Sistem mengembalikan `400 Bad Request`. | Berhasil |
| 61 | User biasa ubah role | User biasa mencoba mengubah role user lain. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 62 | Operator ubah role | Operator mencoba mengubah role user lain. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 63 | Role invalid | Request update role memakai value tidak valid. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 64 | User target tidak ditemukan | Super admin mengubah role user ID yang tidak ada. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 65 | Register device oleh super admin | Super admin mendaftarkan MAC address device baru. | Sistem mengembalikan `201 Created`. | Berhasil |
| 66 | Register device oleh admin | Admin biasa mencoba register device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 67 | Register device oleh user | User biasa mencoba register device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 68 | Lihat unclaimed device oleh admin | Admin melihat device yang belum diklaim. | Sistem mengembalikan `200 OK`. | Berhasil |
| 69 | Lihat unclaimed device oleh user | User biasa mencoba melihat unclaimed device. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 70 | Register FCM token | User mendaftarkan FCM token. | Sistem mengembalikan `200 OK` dan `status = success`. | Berhasil |
| 71 | Register duplicate FCM token | User mendaftarkan token yang sama dua kali. | Sistem tetap mengembalikan `200 OK`. | Berhasil |
| 72 | Unregister FCM token | User menghapus FCM token. | Sistem mengembalikan `200 OK`. | Berhasil |
| 73 | Register FCM token tanpa login | Request register FCM token dikirim tanpa token auth. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 74 | Cleanup logs oleh super admin | Super admin menjalankan cleanup sensor logs. | Sistem mengembalikan `200 OK` dan field `deleted_count`. | Berhasil |
| 75 | Cleanup logs oleh admin | Admin biasa mencoba cleanup logs. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 76 | Cleanup logs oleh user | User biasa mencoba cleanup logs. | Sistem mengembalikan `403 Forbidden`. | Berhasil |
| 77 | Cleanup logs tanpa data lama | Super admin menjalankan cleanup saat tidak ada data lama. | Sistem mengembalikan `200 OK` dan `deleted_count = 0`. | Berhasil |
| 78 | Health check | Client membuka endpoint `/api/health`. | Sistem mengembalikan `200 OK`, `status = healthy`, dan `database_alive = true`. | Berhasil |
| 79 | Statistik harian default | Admin mengambil statistik harian dengan default `days=7`. | Sistem mengembalikan `200 OK` dan wrapper response lengkap. | Berhasil |
| 80 | Statistik harian custom days | Admin mengambil statistik dengan `days=30`. | Sistem mengembalikan `200 OK`. | Berhasil |
| 81 | Struktur response statistik | Response statistik dicek field dan tipe datanya. | Field statistik lengkap dan tipe data sesuai. | Berhasil |
| 82 | Nilai status statistik | Field `status` pada statistik dicek. | Nilai hanya `Normal`, `Waspada`, atau `Bahaya`. | Berhasil |
| 83 | Validasi data_points statistik | Statistik yang memiliki data harus punya `data_points > 0`. | Semua `data_points` bernilai positif. | Berhasil |
| 84 | Validasi min/max suhu | Statistik dicek agar suhu minimum tidak lebih besar dari maksimum. | `min_temperature <= max_temperature`. | Berhasil |
| 85 | Validasi periode statistik | `period_start` dan `period_end` dicek sesuai parameter `days`. | Periode tanggal sesuai. | Berhasil |
| 86 | Urutan statistik | Statistik dicek urut berdasarkan tanggal. | Data terurut ascending dari tanggal lama ke baru. | Berhasil |
| 87 | Statistik `days=1` | Admin mengambil statistik satu hari. | Sistem mengembalikan `200 OK` dan `period_start = period_end`. | Berhasil |
| 88 | Statistik `days=90` | Admin mengambil statistik batas maksimum 90 hari. | Sistem mengembalikan `200 OK`. | Berhasil |
| 89 | Statistik `days=0` | Admin mengirim parameter di bawah minimum. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 90 | Statistik `days=91` | Admin mengirim parameter di atas maksimum. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 91 | Statistik `days` negatif | Admin mengirim parameter negatif. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 92 | Statistik `days` bukan angka | Admin mengirim `days=abc`. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 93 | Statistik device tidak ditemukan | Admin mengambil statistik device ID yang tidak ada. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 94 | Statistik UUID invalid | Admin mengambil statistik dengan format UUID tidak valid. | Sistem mengembalikan `422 Validation Error`. | Berhasil |
| 95 | Statistik device unclaimed | Admin mengambil statistik device yang belum diklaim. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 96 | Statistik device milik user lain | Admin mengambil statistik device milik admin lain. | Sistem mengembalikan `404 Not Found`. | Berhasil |
| 97 | Statistik tanpa token | Request statistik dikirim tanpa token. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 98 | Statistik token invalid | Request statistik memakai token tidak valid. | Sistem mengembalikan `401 Unauthorized`. | Berhasil |
| 99 | Statistik tanpa sensor log | Device tidak memiliki log sensor. | Sistem mengembalikan `200 OK`, `statistics = []`, dan `total_days = 0`. | Berhasil |
| 100 | Statistik data di luar range | Sensor log ada tetapi di luar rentang tanggal yang diminta. | Sistem mengembalikan `200 OK`, `statistics = []`, dan `total_days = 0`. | Berhasil |
| 101 | Buat JWT valid | Sistem membuat token dari payload valid. | Output berupa string token yang tidak kosong. | Berhasil |
| 102 | Buat JWT custom expiry | Sistem membuat token dengan masa berlaku custom. | Token valid dan payload dapat diverifikasi. | Berhasil |
| 103 | JWT menyimpan payload | Token dibuat dengan field tambahan. | Payload hasil verify tetap berisi data yang diberikan. | Berhasil |
| 104 | Verify JWT valid | Sistem memverifikasi token valid. | Payload tidak `None` dan memiliki `sub`, `email`, serta `exp`. | Berhasil |
| 105 | Verify JWT invalid | Sistem memverifikasi token tidak valid. | Output `None`. | Berhasil |
| 106 | Verify JWT kosong | Sistem memverifikasi token kosong. | Output `None`. | Berhasil |
| 107 | Verify JWT malformed | Sistem memverifikasi token rusak. | Output `None`. | Berhasil |
| 108 | Verify JWT expired | Sistem memverifikasi token yang sudah expired. | Output `None`. | Berhasil |

Catatan:

- Semua test pada tabel di atas berstatus `Berhasil` karena hasil eksekusi terakhir menunjukkan `117 passed`.
- Jumlah baris tabel tidak selalu sama dengan jumlah total test karena beberapa test yang mirip digabung menjadi satu baris ringkasan agar tabel lebih mudah dibaca untuk laporan.
- Status `Gagal` digunakan jika output aktual tidak sesuai dengan output yang diharapkan.

---

## 5. Environment Testing

Testing dijalankan menggunakan environment lokal Python dan database SQLite in-memory.

Konfigurasi utama:

| Komponen | Nilai |
|----------|-------|
| Test runner | `pytest` |
| API client | `FastAPI TestClient` |
| Database test | SQLite in-memory |
| Production database | PostgreSQL 15 |
| Auth test | JWT lokal |
| External service | Firebase dan MQTT tidak benar-benar dipanggil secara end-to-end |

Command yang digunakan:

```bash
.venv/bin/python -m pytest -q
```

Output hasil testing:

```text
tests/test_device.py .................................................   [ 41%]
tests/test_security.py ........                                          [ 48%]
tests/test_stats.py .......................                              [ 68%]
tests/test_user.py .....................................                 [100%]

117 passed in 1.92s
```

Catatan environment:

- Di sandbox terbatas, `FastAPI TestClient` dapat menggantung karena pembatasan threading/event loop.
- Saat dijalankan di luar sandbox, seluruh test lulus.
- Ada warning non-fatal dari `pytest-asyncio` tentang `asyncio_default_fixture_loop_scope`.

---

## 6. Pendekatan Blackbox Testing

Pendekatan yang digunakan adalah menguji endpoint berdasarkan kombinasi:

- Endpoint URL.
- HTTP method.
- Header autentikasi.
- Request body.
- Query parameter.
- Role user.
- Kondisi data awal.
- Expected status code.
- Expected JSON response.

Contoh pola blackbox:

| Input | Expected Output |
|-------|-----------------|
| `POST /api/devices/claim` dengan role admin dan MAC valid | `200 OK`, device berhasil diklaim |
| `POST /api/devices/claim` dengan role user | `403 Forbidden` |
| `GET /api/users/me` tanpa token | `401 Unauthorized` |
| `GET /api/devices/{id}/stats/daily?days=0` | `422 Validation Error` |
| `DELETE /api/devices/{id}` dengan super_admin | `200 OK` |
| `DELETE /api/devices/{id}` dengan admin biasa | `403 Forbidden` |

---

## 7. Role yang Diuji

Project ini memiliki 5 role:

```text
super_admin > admin > operator > viewer > user
```

Blackbox testing memastikan setiap role hanya dapat melakukan aksi yang sesuai.

| Role | Hak Akses yang Diuji |
|------|----------------------|
| `super_admin` | Register device, delete device, melihat semua device, assign user ke device manapun, cleanup logs |
| `admin` | Claim device, melihat device miliknya, rename device miliknya, assign operator/viewer, unclaim device |
| `operator` | Melihat dan mengontrol device yang di-assign |
| `viewer` | Melihat device/log yang di-assign, tidak boleh kontrol |
| `user` | Tidak punya akses device sampai dipromosikan atau di-assign |

---

## 8. Detail Skenario Testing

### 7.1 Device Claim

Endpoint:

```text
POST /api/devices/claim
```

Tujuan:

Memastikan device hanya dapat diklaim oleh admin atau super_admin, dan hanya jika MAC address sudah terdaftar serta belum dimiliki user lain.

Skenario:

| No | Kondisi Input | Expected Output |
|---:|---------------|-----------------|
| 1 | Admin claim device unclaimed dengan MAC valid | `200 OK`, response berisi `mac_address`, `name`, dan `user_id` |
| 2 | Admin claim MAC yang tidak terdaftar | `404 Not Found` |
| 3 | Admin claim device yang sudah diklaim | `400 Bad Request` |
| 4 | User biasa mencoba claim device | `403 Forbidden` |
| 5 | Request claim tanpa token | `401 Unauthorized` |

Kesimpulan:

Fitur claim device sudah diuji dari sisi success path, data tidak ditemukan, conflict kepemilikan, role yang tidak berwenang, dan request tanpa autentikasi.

---

### 7.2 List Device Berdasarkan Role

Endpoint:

```text
GET /api/devices/
```

Tujuan:

Memastikan daftar device yang dikembalikan sesuai role user.

Skenario:

| No | Role/Kondisi | Expected Output |
|---:|--------------|-----------------|
| 1 | Admin meminta list device | `200 OK`, hanya melihat device miliknya |
| 2 | User biasa meminta list device | `200 OK`, `data` kosong dan `total` 0 |
| 3 | Operator dengan assignment | `200 OK`, melihat device yang di-assign |
| 4 | Super admin | `200 OK`, melihat semua device |
| 5 | Tanpa token | `401 Unauthorized` |

Kesimpulan:

Endpoint list device telah diuji berdasarkan pembatasan akses per role.

---

### 7.3 Sensor Logs

Endpoint:

```text
GET /api/devices/{device_id}/logs
```

Tujuan:

Memastikan log sensor hanya bisa dibaca oleh user yang memiliki akses ke device.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Admin membaca log device miliknya | `200 OK`, `total > 0` |
| 2 | Operator membaca log device assigned | `200 OK`, `total > 0` |
| 3 | Viewer membaca log device assigned | `200 OK` |
| 4 | User biasa membaca log | `403 Forbidden` |
| 5 | Operator tanpa assignment membaca log | `404 Not Found` |
| 6 | Request dengan `limit=3` | `200 OK`, jumlah data maksimal 3 |

Kesimpulan:

Pengujian memastikan access control dan pagination limit berjalan dari sisi output API.

---

### 7.4 Device Control

Endpoint:

```text
POST /api/devices/{device_id}/control
```

Tujuan:

Memastikan hanya role yang berhak dapat mengirim perintah kontrol ke device.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Admin mengontrol device miliknya | `200 OK` atau `500` jika MQTT tidak tersedia di test |
| 2 | Operator mengontrol device assigned | `200 OK` atau `500` jika MQTT tidak tersedia di test |
| 3 | Viewer mencoba kontrol device | `403 Forbidden` |
| 4 | User biasa mencoba kontrol device | `403 Forbidden` |
| 5 | Tanpa token | `401 Unauthorized` |

Catatan:

Pada environment test, MQTT broker tidak menjadi bagian dari test end-to-end. Karena itu response `500` masih diterima untuk skenario admin/operator selama bukan error authorization seperti `403` atau `404`.

Kesimpulan:

Test ini memvalidasi izin kontrol device berdasarkan role.

---

### 7.5 Device Alerts

Endpoint:

```text
GET /api/devices/{device_id}/alerts
```

Tujuan:

Memastikan endpoint alert hanya mengembalikan sensor log yang memiliki `is_alert = true`.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Admin membaca alert device miliknya | `200 OK`, semua item memiliki `is_alert = true` |
| 2 | User biasa membaca alert | `403 Forbidden` |

Kesimpulan:

Endpoint alert diuji dari sisi filtering data dan access control.

---

### 7.6 Unclaim Device

Endpoint:

```text
POST /api/devices/{device_id}/unclaim
```

Tujuan:

Memastikan device dapat dilepas kepemilikannya hanya oleh role yang berwenang.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Admin unclaim device miliknya | `200 OK`, response `status = success` |
| 2 | User biasa mencoba unclaim | `403 Forbidden` |
| 3 | Tanpa token | `401 Unauthorized` |

Kesimpulan:

Unclaim device telah diuji untuk success path dan penolakan akses.

---

### 7.7 Device Assignment

Endpoint:

```text
POST /api/devices/{device_id}/assign
DELETE /api/devices/{device_id}/assign/{user_id}
GET /api/devices/{device_id}/assignments
```

Tujuan:

Memastikan admin/super_admin dapat memberi dan mencabut akses operator/viewer pada device.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Admin assign user sebagai operator | `200 OK`, response `role = operator` |
| 2 | Admin assign user sebagai viewer | `200 OK`, response `role = viewer` |
| 3 | Admin assign user ke device milik admin lain | `404 Not Found` |
| 4 | User biasa mencoba assign | `403 Forbidden` |
| 5 | Assign user yang sudah assigned | `400 Bad Request` |
| 6 | Admin unassign user | `200 OK` |
| 7 | Admin melihat daftar assignments | `200 OK`, response array berisi assignment |
| 8 | Super admin assign ke device manapun | `200 OK` |

Kesimpulan:

Assignment diuji untuk create, duplicate rejection, read, delete, dan batasan ownership.

---

### 7.8 Get All Devices

Endpoint:

```text
GET /api/devices/all
```

Tujuan:

Memastikan endpoint daftar semua device hanya dapat diakses admin ke atas, dengan scope sesuai role.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Super admin membuka `/all` | `200 OK`, melihat semua device |
| 2 | Admin membuka `/all` | `200 OK`, melihat device miliknya dan unclaimed |
| 3 | User biasa membuka `/all` | `403 Forbidden` |
| 4 | Tanpa token | `401 Unauthorized` |

Kesimpulan:

Endpoint ini sudah diuji untuk role admin, super_admin, user, dan unauthenticated request.

---

### 7.9 Update/Rename Device

Endpoint:

```text
PATCH /api/devices/{device_id}
```

Tujuan:

Memastikan rename device hanya bisa dilakukan oleh pemilik device atau super_admin, serta nama harus valid.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Admin rename device miliknya | `200 OK`, response `name` berubah |
| 2 | Super admin rename device manapun | `200 OK`, response `name` berubah |
| 3 | Admin rename device milik user lain | `404 Not Found` |
| 4 | User biasa mencoba rename | `403 Forbidden` |
| 5 | Rename dengan nama kosong/spasi | `422 Validation Error` |
| 6 | Rename dengan nama lebih dari 100 karakter | `422 Validation Error` |

Kesimpulan:

Test mencakup success path, ownership denial, role denial, dan validasi field.

---

### 7.10 Delete Device

Endpoint:

```text
DELETE /api/devices/{device_id}
```

Tujuan:

Memastikan hanya super_admin yang dapat menghapus device, dan data terkait ikut hilang.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Super admin delete device | `200 OK`, response `status = success` |
| 2 | Admin biasa delete device | `403 Forbidden` |
| 3 | User biasa delete device | `403 Forbidden` |
| 4 | Super admin delete device tidak ada | `404 Not Found` |
| 5 | Delete device yang punya sensor logs | `200 OK`, device tidak muncul lagi di list |

Kesimpulan:

Delete device diuji dari sisi authorization, not found, dan efek penghapusan resource.

---

### 7.11 Current User Profile

Endpoint:

```text
GET /api/users/me
```

Tujuan:

Memastikan user dapat mengambil profilnya sendiri jika token valid.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Token valid | `200 OK`, response berisi email dan role user |
| 2 | Tanpa token | `401 Unauthorized` |
| 3 | Token invalid | `401 Unauthorized` |
| 4 | Token expired | `401 Unauthorized` |
| 5 | Token malformed | `401 Unauthorized` |
| 6 | Authorization tanpa prefix Bearer | `401 Unauthorized` |

Kesimpulan:

Autentikasi endpoint profile diuji untuk token valid dan berbagai bentuk token tidak valid.

---

### 7.12 Role Field di Response User

Endpoint:

```text
GET /api/users/me
```

Tujuan:

Memastikan field `role` selalu muncul dan sesuai dengan role user.

Skenario:

| No | Role | Expected Output |
|---:|------|-----------------|
| 1 | user | `role = user` |
| 2 | admin | `role = admin` |
| 3 | super_admin | `role = super_admin` |
| 4 | operator | `role = operator` |
| 5 | viewer | `role = viewer` |

Kesimpulan:

Response profile diuji untuk seluruh role utama.

---

### 7.13 Update User Role

Endpoint:

```text
PATCH /api/users/{user_id}/role
```

Tujuan:

Memastikan perubahan role mengikuti hierarchy dan tidak bisa disalahgunakan.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Super admin mengubah role user ke admin/operator/viewer/user | `200 OK` |
| 2 | Admin mengubah role user ke operator/viewer/user | `200 OK` |
| 3 | Admin promote user ke admin | `403 Forbidden` |
| 4 | Admin promote user ke super_admin | `403 Forbidden` |
| 5 | Admin mengubah role super_admin | `403 Forbidden` |
| 6 | Admin mengubah role diri sendiri | `400 Bad Request` |
| 7 | User biasa mengubah role | `403 Forbidden` |
| 8 | Operator mengubah role | `403 Forbidden` |
| 9 | Role invalid | `422 Validation Error` |
| 10 | Target user tidak ditemukan | `404 Not Found` |
| 11 | Tanpa token | `401 Unauthorized` |

Kesimpulan:

Role hierarchy dan aturan keamanan perubahan role diuji cukup lengkap.

---

### 7.14 Admin Endpoint Access

Endpoint terkait:

```text
POST /api/devices/register
GET /api/devices/unclaimed
```

Tujuan:

Memastikan endpoint administratif hanya bisa diakses role yang sesuai.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | User biasa register device | `403 Forbidden` |
| 2 | Super admin register device | `201 Created` |
| 3 | Admin biasa register device | `403 Forbidden` |
| 4 | User biasa melihat unclaimed device | `403 Forbidden` |
| 5 | Admin melihat unclaimed device | `200 OK` |

Kesimpulan:

Access control endpoint admin diuji untuk role super_admin, admin, dan user.

---

### 7.15 FCM Token

Endpoint:

```text
POST /api/users/me/fcm-token
DELETE /api/users/me/fcm-token
```

Tujuan:

Memastikan user dapat mendaftarkan dan menghapus token FCM untuk push notification.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | User register FCM token | `200 OK`, `status = success` |
| 2 | Register token yang sama dua kali | `200 OK`, tidak error |
| 3 | User unregister FCM token | `200 OK` |
| 4 | Register tanpa token autentikasi | `401 Unauthorized` |

Kesimpulan:

FCM token diuji untuk register, duplicate handling, unregister, dan unauthorized request.

---

### 7.16 Cleanup Logs

Endpoint:

```text
POST /api/admin/cleanup-logs
```

Tujuan:

Memastikan cleanup sensor logs hanya dapat dijalankan oleh super_admin.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Super admin menjalankan cleanup | `200 OK`, response berisi `deleted_count` |
| 2 | Admin biasa menjalankan cleanup | `403 Forbidden` |
| 3 | User biasa menjalankan cleanup | `403 Forbidden` |
| 4 | Cleanup saat tidak ada data lama | `200 OK`, `deleted_count = 0` |
| 5 | Tanpa token | `401 Unauthorized` |

Kesimpulan:

Cleanup logs diuji dari sisi authorization dan kondisi data kosong.

---

### 7.17 Health Check

Endpoint:

```text
GET /api/health
```

Tujuan:

Memastikan endpoint health check dapat memberi status aplikasi dan database.

Skenario:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Health check normal | `200 OK`, `status = healthy`, `database_alive = true` |

Kesimpulan:

Endpoint health check diuji untuk memastikan aplikasi dan database test berjalan.

---

### 7.18 Daily Statistics

Endpoint:

```text
GET /api/devices/{device_id}/stats/daily
```

Tujuan:

Memastikan API statistik harian mengembalikan agregasi sensor sesuai format yang dibutuhkan dashboard/mobile app.

Skenario success path:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Ambil statistik dengan default `days=7` | `200 OK`, response wrapper lengkap |
| 2 | Ambil statistik dengan custom `days=30` | `200 OK` |
| 3 | Validasi struktur item statistik | Field `date`, `avg_temperature`, `min_temperature`, `max_temperature`, `avg_humidity`, `avg_ammonia`, `data_points`, `alert_count`, `status` ada |
| 4 | Validasi nilai `status` | Hanya `Normal`, `Waspada`, atau `Bahaya` |
| 5 | Validasi `data_points` | Nilai positif jika ada data |
| 6 | Validasi suhu minimum dan maksimum | `min_temperature <= max_temperature` |
| 7 | Validasi periode tanggal | `period_start` dan `period_end` sesuai parameter `days` |
| 8 | Validasi urutan statistik | Data terurut ascending berdasarkan tanggal |

Skenario validasi parameter:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | `days=1` | `200 OK`, `period_start = period_end` |
| 2 | `days=90` | `200 OK` |
| 3 | `days=0` | `422 Validation Error` |
| 4 | `days=91` | `422 Validation Error` |
| 5 | `days=-5` | `422 Validation Error` |
| 6 | `days=abc` | `422 Validation Error` |

Skenario access dan data:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Device ID tidak ada | `404 Not Found` |
| 2 | Device ID bukan UUID valid | `422 Validation Error` |
| 3 | Admin akses device unclaimed | `404 Not Found` |
| 4 | Admin akses device milik user lain | `404 Not Found` |
| 5 | Tanpa token | `401 Unauthorized` |
| 6 | Token invalid | `401 Unauthorized` |
| 7 | Device tidak punya sensor log | `200 OK`, `statistics = []`, `total_days = 0` |
| 8 | Sensor log ada tapi di luar range tanggal | `200 OK`, `statistics = []`, `total_days = 0` |

Kesimpulan:

Endpoint statistik diuji dari sisi format response, logika agregasi dasar, validasi query parameter, authorization, dan kondisi data kosong.

---

### 7.19 Security Token

Fungsi terkait:

```text
create_access_token()
verify_token()
```

Tujuan:

Memastikan JWT dapat dibuat dan diverifikasi dengan benar.

Skenario pembuatan token:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Membuat token dengan data valid | Token berupa string tidak kosong |
| 2 | Membuat token dengan custom expiry | Token valid dan payload dapat dibaca |
| 3 | Membuat token dengan field tambahan | Payload tetap menyimpan data yang diberikan |

Skenario verifikasi token:

| No | Kondisi | Expected Output |
|---:|---------|-----------------|
| 1 | Verify token valid | Payload tidak `None`, berisi `sub`, `email`, dan `exp` |
| 2 | Verify token invalid | `None` |
| 3 | Verify token kosong | `None` |
| 4 | Verify token malformed | `None` |
| 5 | Verify token expired | `None` |

Catatan:

Bagian ini lebih dekat ke unit test fungsi security, bukan blackbox API murni. Namun tetap penting karena hasilnya memengaruhi semua endpoint yang menggunakan JWT.

---

## 9. Jenis Kasus Uji yang Tercakup

Testing saat ini mencakup beberapa kategori umum blackbox testing:

| Kategori | Contoh |
|----------|--------|
| Positive testing | Admin berhasil claim device, super_admin berhasil delete device |
| Negative testing | User biasa tidak bisa control/delete/assign device |
| Boundary testing | `days=1`, `days=90`, nama device 101 karakter |
| Validation testing | UUID invalid, role invalid, days bukan integer |
| Authorization testing | Perbedaan akses super_admin, admin, operator, viewer, user |
| Authentication testing | Token missing, invalid, expired, malformed |
| Data filtering testing | Alert hanya `is_alert = true`, logs dengan limit |
| Empty state testing | Statistik tanpa sensor log, cleanup tanpa data lama |
| Not found testing | Device/user tidak ditemukan |

---

## 10. Analisis Metode Blackbox Testing yang Digunakan

Analisis lengkap metode blackbox testing yang diterapkan pada test suite ini (EP, BVA, DTT, State Transition, Error Guessing) didokumentasikan secara terpisah di:

> 📄 **[BLACKBOX_TESTING_METHODS.md](BLACKBOX_TESTING_METHODS.md)**

---

## 11. Status Code yang Diuji

| Status Code | Arti | Contoh Pengujian |
|------------:|------|------------------|
| `200` | Request sukses | List device, get logs, get stats, assign, unclaim |
| `201` | Resource berhasil dibuat | Register device oleh super_admin |
| `400` | Business rule invalid | Claim device yang sudah diklaim, duplicate assignment, ubah role sendiri |
| `401` | Tidak terautentikasi | Tanpa token, token invalid, token expired |
| `403` | Tidak punya izin | User delete device, admin register device, viewer control device |
| `404` | Resource tidak ditemukan atau akses disamarkan | Device tidak ada, device milik user lain |
| `422` | Validasi input gagal | UUID invalid, role invalid, `days=0`, nama kosong |
| `500` | Kegagalan external service di test | MQTT tidak tersedia saat control command |

---

## 12. Data Uji

Data uji dibuat melalui fixture agar setiap test memiliki kondisi awal yang terkontrol.

Jenis fixture utama:

| Fixture | Fungsi |
|---------|--------|
| `test_user` | User default role `user` |
| `test_super_admin` | User role `super_admin` |
| `test_admin_user` | User role `admin` |
| `test_operator` | User role `operator` |
| `test_viewer` | User role `viewer` |
| `test_device_unclaimed` | Device yang belum diklaim |
| `test_device_claimed` | Device milik admin |
| `test_device_other_user` | Device milik admin lain |
| `test_sensor_logs` | Log sensor normal dan alert |
| `test_operator_assignment` | Assignment operator ke device |
| `test_viewer_assignment` | Assignment viewer ke device |

Sebagian besar unit test menggunakan database SQLite in-memory dan data dibersihkan setelah test selesai, sehingga hasil test tidak bergantung pada urutan eksekusi. Project juga menyediakan fixture PostgreSQL integration test untuk skenario yang perlu divalidasi terhadap database production-like.

### Fixture PostgreSQL Integration Test

Fixture PostgreSQL digunakan untuk menjalankan test yang membutuhkan database PostgreSQL asli. Test ini ditandai dengan marker:

```text
postgres
```

Cara menjalankan PostgreSQL test database:

```bash
docker compose -f docker-compose.test.yml up -d postgres_test
```

Cara menjalankan integration test PostgreSQL:

```bash
TEST_DATABASE_URL=postgresql://test:test@localhost:5433/pcb_test \
.venv/bin/python -m pytest -m postgres
```

Skenario awal yang sudah tersedia:

| Test | Tujuan |
|------|--------|
| Statistik harian PostgreSQL | Memastikan agregasi tanggal, average, min, max, count, dan status berjalan di PostgreSQL |
| Delete cascade PostgreSQL | Memastikan penghapusan device juga menghapus sensor logs terkait |
| Claim device PostgreSQL | Memastikan UUID primary key dan proses claim berjalan di PostgreSQL |

---

## 13. Kelebihan Testing Saat Ini

Kelebihan blackbox testing yang sudah ada:

1. Mencakup banyak endpoint utama backend.
2. Menguji semua role penting.
3. Menguji autentikasi dan authorization secara konsisten.
4. Menguji input invalid dan edge case parameter.
5. Menguji response JSON penting, bukan hanya status code.
6. Memiliki isolasi data antar test.
7. Cepat dijalankan karena memakai SQLite in-memory.
8. Cocok untuk regression test saat ada perubahan backend.

---

## 14. Keterbatasan Testing Saat Ini

Beberapa hal yang belum sepenuhnya tercakup:

1. MQTT broker tidak diuji secara end-to-end.
2. Firebase Auth tidak diuji secara end-to-end dengan service asli.
3. FCM push notification tidak diuji sampai benar-benar terkirim.
4. WebSocket realtime belum terlihat tercakup dalam test suite saat ini.
5. PostgreSQL integration test baru mencakup skenario awal, belum seluruh endpoint.
6. Load test, stress test, dan concurrency test belum menjadi bagian dari test suite.
7. Endpoint login Firebase belum diuji sebagai integrasi real Firebase.
8. Nginx routing dan Docker production stack tidak diuji oleh pytest ini.

---

## 15. Rekomendasi Pengembangan Testing

Untuk membuat testing lebih lengkap, disarankan menambahkan:

1. Perluasan integration test PostgreSQL untuk endpoint dan query lain yang rawan berbeda dari SQLite.
2. Test WebSocket `/api/ws/devices/{device_id}`.
3. Test MQTT worker dengan broker test atau mock MQTT client.
4. Test Firebase login dengan mock Firebase Admin SDK.
5. Test FCM notification sender dengan mock Firebase Messaging.
6. Test race condition device claim.
7. Test pagination untuk semua endpoint paginated.
8. Test rate limit untuk endpoint sensitif.
9. Test production-like Docker health check.
10. Test API contract snapshot untuk memastikan response tidak berubah tanpa sengaja.

---

## 16. Kesimpulan

Blackbox testing pada project Smart Chicken Box sudah mencakup bagian penting dari backend API. Total terdapat 117 test yang berhasil lulus, dengan fokus pada input/output endpoint, autentikasi, otorisasi role, validasi input, dan response JSON.

Secara praktis, test suite ini sudah cukup kuat untuk memastikan fitur utama backend tidak rusak saat ada perubahan kode. Untuk kualitas production yang lebih tinggi, coverage perlu diperluas ke integrasi PostgreSQL, MQTT, WebSocket, Firebase, dan FCM.

Ringkasan hasil:

```text
Total test: 117
Status: Passed
Command: .venv/bin/python -m pytest -q
Hasil: 117 passed in 1.92s
```
