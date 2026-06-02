# Rancangan Slide Blackbox Testing

> Project: Smart Chicken Box (PCB)  
> Tujuan: Bahan penyusunan slide presentasi bagian blackbox testing  
> Total test otomatis: 120  
> Total blackbox API-level: 112  
> Unit test security: 8

---

## Cara Menampilkan di Slide

Jumlah blackbox API-level pada project ini cukup banyak, yaitu 112 test case. Agar slide tetap terbaca, hasil pengujian sebaiknya ditampilkan dalam dua bagian:

1. Slide utama berisi ringkasan, distribusi, dan hasil per modul.
2. Slide lampiran berisi detail seluruh skenario test case.

Kalimat penjelasan yang bisa digunakan saat presentasi:

```text
Karena jumlah test case blackbox cukup banyak, yaitu 112 test case, hasil pengujian saya kelompokkan berdasarkan modul agar lebih mudah dibaca. Slide utama menampilkan ringkasan hasil pengujian, sedangkan detail seluruh test case ditampilkan pada slide lampiran.
```

---

## Slide 1 - Judul

**Judul slide:**

```text
Blackbox Testing Backend API
Smart Chicken Box (PCB)
```

**Isi slide:**

```text
Pengujian dilakukan pada level API dengan memberi input request ke endpoint dan memeriksa output berupa status code serta JSON response.
```

---

## Slide 2 - Metode Pengujian

**Judul slide:**

```text
Metode Blackbox Testing
```

**Isi slide:**

| Aspek | Keterangan |
|---|---|
| Pendekatan | API-level blackbox testing |
| Tools | pytest, FastAPI TestClient |
| Input yang diuji | Method, endpoint, header auth, request body, query parameter |
| Output yang diperiksa | Status code dan JSON response |
| Database utama test | SQLite in-memory |
| Integration test | PostgreSQL test database |

**Catatan presenter:**

```text
Pengujian disebut blackbox karena fokus pada input dan output endpoint, bukan pada detail implementasi internal route handler.
```

---

## Slide 3 - Ringkasan Jumlah Test

**Judul slide:**

```text
Ringkasan Jumlah Test
```

**Isi slide:**

| Klasifikasi | Jumlah | Keterangan |
|---|---:|---|
| Blackbox API-level | 109 | Endpoint API dengan SQLite in-memory |
| Blackbox API integration | 3 | Endpoint API dengan PostgreSQL |
| Unit test security | 8 | Test fungsi JWT secara langsung |
| Total blackbox API-level | 112 | Dipakai untuk laporan blackbox |
| Total test otomatis | 120 | Keseluruhan test backend |

**Catatan presenter:**

```text
Untuk bagian blackbox, jumlah yang digunakan adalah 112 test case. Delapan test security dipisahkan karena menguji fungsi internal JWT secara langsung.
```

---

## Slide 4 - Distribusi Test Case Blackbox

**Judul slide:**

```text
Distribusi Test Case Blackbox
```

**Isi slide:**

| Modul Test | Jumlah | Fokus Pengujian |
|---|---:|---|
| `test_device.py` | 49 | Device, claim, logs, control, assignment |
| `test_user.py` | 37 | User, role, admin access, FCM, cleanup |
| `test_stats.py` | 23 | Statistik harian dan validasi parameter |
| `test_postgres_integration.py` | 3 | Integrasi endpoint dengan PostgreSQL |
| **Total** | **112** | Blackbox API-level |

---

## Slide 5 - Hasil Per Modul

**Judul slide:**

```text
Hasil Blackbox Testing Per Modul
```

**Isi slide:**

| Modul | Jumlah Test | Hasil |
|---|---:|---|
| Device API | 49 | Berhasil |
| User API | 37 | Berhasil |
| Daily Stats API | 23 | Berhasil |
| PostgreSQL Integration API | 3 | Berhasil |
| **Total** | **112** | **Berhasil** |

**Catatan presenter:**

```text
Seluruh skenario blackbox yang didokumentasikan berstatus berhasil karena output aktual sesuai dengan expected output.
```

---

## Slide 6 - Jenis Kasus Uji

**Judul slide:**

```text
Jenis Kasus Uji yang Dicakup
```

**Isi slide:**

| Jenis Testing | Contoh |
|---|---|
| Positive testing | Admin berhasil claim device |
| Negative testing | User biasa tidak bisa delete device |
| Authentication testing | Request tanpa token ditolak |
| Authorization testing | Role viewer tidak bisa control device |
| Validation testing | UUID invalid dan role invalid ditolak |
| Boundary testing | `days=1`, `days=90`, `days=0`, `days=91` |
| Empty state testing | Statistik tanpa sensor log |
| Not found testing | Device tidak ditemukan |

---

## Slide 7 - Status Code yang Diuji

**Judul slide:**

```text
Status Code yang Diuji
```

**Isi slide:**

| Status Code | Arti | Contoh |
|---:|---|---|
| 200 | Request sukses | List device, get logs, get stats |
| 201 | Resource dibuat | Register device oleh super admin |
| 400 | Business rule invalid | Claim device yang sudah diklaim |
| 401 | Tidak terautentikasi | Request tanpa token |
| 403 | Tidak punya izin | User biasa delete device |
| 404 | Resource tidak ditemukan atau akses disamarkan | Device milik user lain |
| 422 | Validasi input gagal | UUID invalid, `days=0` |
| 500 | External service tidak tersedia saat test | MQTT tidak tersedia saat control command |

---

## Slide 8 - Contoh Detail Device API

**Judul slide:**

```text
Contoh Hasil Blackbox Device API
```

**Isi slide:**

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Admin claim device valid | `200 OK` | Berhasil |
| 2 | Claim MAC tidak terdaftar | `404 Not Found` | Berhasil |
| 3 | Claim device sudah diklaim | `400 Bad Request` | Berhasil |
| 4 | User biasa claim device | `403 Forbidden` | Berhasil |
| 5 | Claim tanpa token | `401 Unauthorized` | Berhasil |

---

## Slide 9 - Contoh Detail User API

**Judul slide:**

```text
Contoh Hasil Blackbox User API
```

**Isi slide:**

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | User mengambil profil dengan token valid | `200 OK` | Berhasil |
| 2 | Profil tanpa token | `401 Unauthorized` | Berhasil |
| 3 | Admin promote user ke admin | `403 Forbidden` | Berhasil |
| 4 | Super admin ubah role user | `200 OK` | Berhasil |
| 5 | Role invalid | `422 Validation Error` | Berhasil |

---

## Slide 10 - Contoh Detail Daily Stats API

**Judul slide:**

```text
Contoh Hasil Blackbox Daily Stats API
```

**Isi slide:**

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Statistik default `days=7` | `200 OK` | Berhasil |
| 2 | Statistik `days=90` | `200 OK` | Berhasil |
| 3 | Statistik `days=0` | `422 Validation Error` | Berhasil |
| 4 | Device tidak ditemukan | `404 Not Found` | Berhasil |
| 5 | Statistik tanpa sensor log | `200 OK`, data kosong | Berhasil |

---

## Slide 11 - Kesimpulan

**Judul slide:**

```text
Kesimpulan Blackbox Testing
```

**Isi slide:**

```text
Berdasarkan pengujian blackbox API-level, seluruh skenario utama backend berhasil diuji. Total terdapat 112 test case blackbox yang mencakup autentikasi, otorisasi role, validasi input, CRUD device, assignment, FCM token, cleanup logs, statistik harian, dan integrasi PostgreSQL.
```

**Ringkasan akhir:**

| Keterangan | Hasil |
|---|---:|
| Total blackbox API-level | 112 |
| Total modul utama | 4 |
| Status hasil | Berhasil |

---

# Lampiran Slide Detail

Bagian ini digunakan jika dosen meminta semua hasil blackbox ditampilkan. Agar slide tidak terlalu penuh, pecah tabel lampiran ini menjadi beberapa slide.

---

## Lampiran A - Device Claim

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Admin claim device unclaimed dengan MAC valid | `200 OK`, response berisi `mac_address`, `name`, dan `user_id` | Berhasil |
| 2 | Admin claim MAC yang tidak terdaftar | `404 Not Found` | Berhasil |
| 3 | Admin claim device yang sudah diklaim | `400 Bad Request` | Berhasil |
| 4 | User biasa mencoba claim device | `403 Forbidden` | Berhasil |
| 5 | Request claim tanpa token | `401 Unauthorized` | Berhasil |

---

## Lampiran B - List Device

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Admin meminta list device | `200 OK`, hanya melihat device miliknya | Berhasil |
| 2 | User biasa meminta list device | `200 OK`, `data` kosong dan `total = 0` | Berhasil |
| 3 | Operator dengan assignment meminta list device | `200 OK`, melihat device yang di-assign | Berhasil |
| 4 | Super admin meminta list device | `200 OK`, melihat semua device | Berhasil |
| 5 | Request list device tanpa token | `401 Unauthorized` | Berhasil |

---

## Lampiran C - Sensor Logs

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Admin membaca log device miliknya | `200 OK`, `total > 0` | Berhasil |
| 2 | Operator membaca log device assigned | `200 OK`, `total > 0` | Berhasil |
| 3 | Viewer membaca log device assigned | `200 OK` | Berhasil |
| 4 | User biasa membaca log | `403 Forbidden` | Berhasil |
| 5 | Operator tanpa assignment membaca log | `404 Not Found` | Berhasil |
| 6 | Request logs dengan `limit=3` | `200 OK`, jumlah data maksimal 3 | Berhasil |

---

## Lampiran D - Device Control dan Alert

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Admin mengontrol device miliknya | `200 OK` atau `500` jika MQTT tidak tersedia di test | Berhasil |
| 2 | Operator mengontrol device assigned | `200 OK` atau `500` jika MQTT tidak tersedia di test | Berhasil |
| 3 | Viewer mencoba kontrol device | `403 Forbidden` | Berhasil |
| 4 | User biasa mencoba kontrol device | `403 Forbidden` | Berhasil |
| 5 | Request kontrol tanpa token | `401 Unauthorized` | Berhasil |
| 6 | Admin membaca alert device miliknya | `200 OK`, semua item memiliki `is_alert = true` | Berhasil |
| 7 | User biasa membaca alert | `403 Forbidden` | Berhasil |

---

## Lampiran E - Unclaim dan Assignment

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Admin unclaim device miliknya | `200 OK`, response `status = success` | Berhasil |
| 2 | User biasa mencoba unclaim | `403 Forbidden` | Berhasil |
| 3 | Request unclaim tanpa token | `401 Unauthorized` | Berhasil |
| 4 | Admin assign user sebagai operator | `200 OK`, response `role = operator` | Berhasil |
| 5 | Admin assign user sebagai viewer | `200 OK`, response `role = viewer` | Berhasil |
| 6 | Admin assign user ke device milik admin lain | `404 Not Found` | Berhasil |
| 7 | User biasa mencoba assign | `403 Forbidden` | Berhasil |
| 8 | Assign user yang sudah assigned | `400 Bad Request` | Berhasil |
| 9 | Admin unassign user | `200 OK` | Berhasil |
| 10 | Admin melihat daftar assignments | `200 OK`, response array assignment | Berhasil |
| 11 | Super admin assign ke device manapun | `200 OK` | Berhasil |

---

## Lampiran F - Get All, Rename, dan Delete Device

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Super admin membuka `/api/devices/all` | `200 OK`, melihat semua device | Berhasil |
| 2 | Admin membuka `/api/devices/all` | `200 OK`, melihat device miliknya dan unclaimed | Berhasil |
| 3 | User biasa membuka `/api/devices/all` | `403 Forbidden` | Berhasil |
| 4 | Request `/api/devices/all` tanpa token | `401 Unauthorized` | Berhasil |
| 5 | Admin rename device miliknya | `200 OK`, response `name` berubah | Berhasil |
| 6 | Super admin rename device manapun | `200 OK`, response `name` berubah | Berhasil |
| 7 | Admin rename device milik user lain | `404 Not Found` | Berhasil |
| 8 | User biasa mencoba rename | `403 Forbidden` | Berhasil |
| 9 | Rename dengan nama kosong/spasi | `422 Validation Error` | Berhasil |
| 10 | Rename dengan nama lebih dari 100 karakter | `422 Validation Error` | Berhasil |
| 11 | Super admin delete device | `200 OK`, response `status = success` | Berhasil |
| 12 | Admin biasa delete device | `403 Forbidden` | Berhasil |
| 13 | User biasa delete device | `403 Forbidden` | Berhasil |
| 14 | Super admin delete device tidak ada | `404 Not Found` | Berhasil |
| 15 | Delete device yang punya sensor logs | `200 OK`, device tidak muncul lagi pada list | Berhasil |

---

## Lampiran G - Profile dan Role User

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Token valid mengambil profil | `200 OK`, response berisi email dan role user | Berhasil |
| 2 | Profil tanpa token | `401 Unauthorized` | Berhasil |
| 3 | Profil dengan token invalid | `401 Unauthorized` | Berhasil |
| 4 | Profil dengan token expired | `401 Unauthorized` | Berhasil |
| 5 | Profil dengan token malformed | `401 Unauthorized` | Berhasil |
| 6 | Authorization tanpa prefix Bearer | `401 Unauthorized` | Berhasil |
| 7 | Profile role `user` | `role = user` | Berhasil |
| 8 | Profile role `admin` | `role = admin` | Berhasil |
| 9 | Profile role `super_admin` | `role = super_admin` | Berhasil |
| 10 | Profile role `operator` | `role = operator` | Berhasil |
| 11 | Profile role `viewer` | `role = viewer` | Berhasil |

---

## Lampiran H - Update User Role

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Super admin mengubah role user | `200 OK` | Berhasil |
| 2 | Admin mengubah user ke operator/viewer/user | `200 OK` | Berhasil |
| 3 | Admin promote user ke admin | `403 Forbidden` | Berhasil |
| 4 | Admin promote user ke super admin | `403 Forbidden` | Berhasil |
| 5 | Admin mengubah role super admin | `403 Forbidden` | Berhasil |
| 6 | Admin mengubah role diri sendiri | `400 Bad Request` | Berhasil |
| 7 | User biasa mengubah role | `403 Forbidden` | Berhasil |
| 8 | Operator mengubah role | `403 Forbidden` | Berhasil |
| 9 | Role invalid | `422 Validation Error` | Berhasil |
| 10 | Target user tidak ditemukan | `404 Not Found` | Berhasil |
| 11 | Update role tanpa token | `401 Unauthorized` | Berhasil |

---

## Lampiran I - Admin Endpoint, FCM, Cleanup, dan Health Check

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | User biasa register device | `403 Forbidden` | Berhasil |
| 2 | Super admin register device | `201 Created` | Berhasil |
| 3 | Admin biasa register device | `403 Forbidden` | Berhasil |
| 4 | User biasa melihat unclaimed device | `403 Forbidden` | Berhasil |
| 5 | Admin melihat unclaimed device | `200 OK` | Berhasil |
| 6 | User register FCM token | `200 OK`, `status = success` | Berhasil |
| 7 | Register duplicate FCM token | `200 OK`, tidak error | Berhasil |
| 8 | User unregister FCM token | `200 OK` | Berhasil |
| 9 | Register FCM tanpa token | `401 Unauthorized` | Berhasil |
| 10 | Super admin menjalankan cleanup logs | `200 OK`, response berisi `deleted_count` | Berhasil |
| 11 | Admin biasa menjalankan cleanup logs | `403 Forbidden` | Berhasil |
| 12 | User biasa menjalankan cleanup logs | `403 Forbidden` | Berhasil |
| 13 | Cleanup saat tidak ada data lama | `200 OK`, `deleted_count = 0` | Berhasil |
| 14 | Cleanup tanpa token | `401 Unauthorized` | Berhasil |
| 15 | Health check normal | `200 OK`, `status = healthy`, `database_alive = true` | Berhasil |

---

## Lampiran J - Daily Statistics Success Path

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Ambil statistik dengan default `days=7` | `200 OK`, response wrapper lengkap | Berhasil |
| 2 | Ambil statistik dengan custom `days=30` | `200 OK` | Berhasil |
| 3 | Validasi struktur item statistik | Field statistik lengkap tersedia | Berhasil |
| 4 | Validasi nilai `status` | Hanya `Normal`, `Waspada`, atau `Bahaya` | Berhasil |
| 5 | Validasi `data_points` | Nilai positif jika ada data | Berhasil |
| 6 | Validasi suhu minimum dan maksimum | `min_temperature <= max_temperature` | Berhasil |
| 7 | Validasi periode tanggal | `period_start` dan `period_end` sesuai parameter `days` | Berhasil |
| 8 | Validasi urutan statistik | Data terurut ascending berdasarkan tanggal | Berhasil |

---

## Lampiran K - Daily Statistics Validation, Access, dan Empty State

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Statistik `days=1` | `200 OK`, `period_start = period_end` | Berhasil |
| 2 | Statistik `days=90` | `200 OK` | Berhasil |
| 3 | Statistik `days=0` | `422 Validation Error` | Berhasil |
| 4 | Statistik `days=91` | `422 Validation Error` | Berhasil |
| 5 | Statistik `days=-5` | `422 Validation Error` | Berhasil |
| 6 | Statistik `days=abc` | `422 Validation Error` | Berhasil |
| 7 | Device ID tidak ada | `404 Not Found` | Berhasil |
| 8 | Device ID bukan UUID valid | `422 Validation Error` | Berhasil |
| 9 | Admin akses device unclaimed | `404 Not Found` | Berhasil |
| 10 | Admin akses device milik user lain | `404 Not Found` | Berhasil |
| 11 | Statistik tanpa token | `401 Unauthorized` | Berhasil |
| 12 | Statistik token invalid | `401 Unauthorized` | Berhasil |
| 13 | Device tidak punya sensor log | `200 OK`, `statistics = []`, `total_days = 0` | Berhasil |
| 14 | Sensor log ada tapi di luar range tanggal | `200 OK`, `statistics = []`, `total_days = 0` | Berhasil |

---

## Lampiran L - PostgreSQL Integration

| No | Skenario | Expected Output | Hasil |
|---:|---|---|---|
| 1 | Statistik harian PostgreSQL | `200 OK`, agregasi tanggal dan nilai statistik valid | Berhasil |
| 2 | Delete cascade PostgreSQL | Device terhapus dan sensor logs terkait ikut terhapus | Berhasil |
| 3 | Claim device PostgreSQL | `200 OK`, `id`, `user_id`, dan nama device sesuai | Berhasil |

---

## Catatan Penting untuk Slide

1. Jangan tampilkan semua lampiran detail pada slide utama.
2. Gunakan slide utama untuk menjelaskan ringkasan hasil.
3. Gunakan lampiran jika dosen meminta bukti semua hasil pengujian.
4. Pisahkan unit test security dari blackbox API-level agar klasifikasinya tidak rancu.
5. Jika tabel terlalu lebar, gunakan kolom: `No`, `Skenario`, `Expected`, `Hasil`.

