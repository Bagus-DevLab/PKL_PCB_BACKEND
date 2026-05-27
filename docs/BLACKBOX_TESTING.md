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

## 4. Environment Testing

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

## 5. Pendekatan Blackbox Testing

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

## 6. Role yang Diuji

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

## 7. Detail Skenario Testing

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

## 8. Jenis Kasus Uji yang Tercakup

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

## 9. Status Code yang Diuji

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

## 10. Data Uji

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

Setiap test menggunakan database SQLite in-memory dan data dibersihkan setelah test selesai, sehingga hasil test tidak bergantung pada urutan eksekusi.

---

## 11. Kelebihan Testing Saat Ini

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

## 12. Keterbatasan Testing Saat Ini

Beberapa hal yang belum sepenuhnya tercakup:

1. MQTT broker tidak diuji secara end-to-end.
2. Firebase Auth tidak diuji secara end-to-end dengan service asli.
3. FCM push notification tidak diuji sampai benar-benar terkirim.
4. WebSocket realtime belum terlihat tercakup dalam test suite saat ini.
5. Perbedaan perilaku SQLite dan PostgreSQL masih mungkin terjadi.
6. Load test, stress test, dan concurrency test belum menjadi bagian dari test suite.
7. Endpoint login Firebase belum diuji sebagai integrasi real Firebase.
8. Nginx routing dan Docker production stack tidak diuji oleh pytest ini.

---

## 13. Rekomendasi Pengembangan Testing

Untuk membuat testing lebih lengkap, disarankan menambahkan:

1. Integration test PostgreSQL menggunakan container test database.
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

## 14. Kesimpulan

Blackbox testing pada project Smart Chicken Box sudah mencakup bagian penting dari backend API. Total terdapat 117 test yang berhasil lulus, dengan fokus pada input/output endpoint, autentikasi, otorisasi role, validasi input, dan response JSON.

Secara praktis, test suite ini sudah cukup kuat untuk memastikan fitur utama backend tidak rusak saat ada perubahan kode. Untuk kualitas production yang lebih tinggi, coverage perlu diperluas ke integrasi PostgreSQL, MQTT, WebSocket, Firebase, dan FCM.

Ringkasan hasil:

```text
Total test: 117
Status: Passed
Command: .venv/bin/python -m pytest -q
Hasil: 117 passed in 1.92s
```
