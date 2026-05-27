# Analisis Metode Blackbox Testing — Smart Chicken Box (PCB)

> Versi: 1.0.0
> Terakhir diperbarui: 2026-05-27
> Project: PKL PCB Smart Kandang / Smart Chicken Box
> Referensi: [BLACKBOX_TESTING.md](BLACKBOX_TESTING.md)

Dokumen ini menganalisis metode blackbox testing formal yang diterapkan pada test suite PCB, beserta contoh test case konkret dari masing-masing metode.

---

## Daftar Isi

1. [Equivalence Partitioning (EP)](#1-equivalence-partitioning-ep)
2. [Boundary Value Analysis (BVA)](#2-boundary-value-analysis-bva)
3. [Decision Table Testing (DTT)](#3-decision-table-testing-dtt)
4. [State Transition Testing](#4-state-transition-testing)
5. [Error Guessing](#5-error-guessing)
6. [Ringkasan Penggunaan Metode](#6-ringkasan-penggunaan-metode)

---

## 1. Equivalence Partitioning (EP)

Metode yang paling dominan digunakan. Input dibagi menjadi partisi valid dan invalid, lalu satu representatif dari tiap partisi diuji — tidak perlu menguji semua nilai dalam satu partisi karena diasumsikan berperilaku sama.

### EP pada Role-Based Access Control (RBAC)

| Partisi | Nilai Representatif | Test Case | Expected Output |
|---------|--------------------|-----------|-----------------| 
| Role boleh register device | `super_admin` | Test 65 | `201 Created` |
| Role tidak boleh register device | `admin`, `user` | Test 66, 67 | `403 Forbidden` |
| Role boleh claim device | `admin`, `super_admin` | Test 1 | `200 OK` |
| Role tidak boleh claim device | `user` | Test 4 | `403 Forbidden` |
| Role boleh kontrol device | `admin`, `operator` | Test 17, 18 | `200 OK` / `500` |
| Role tidak boleh kontrol device | `viewer`, `user` | Test 19, 20 | `403 Forbidden` |
| Role boleh delete device | `super_admin` | Test 44 | `200 OK` |
| Role tidak boleh delete device | `admin`, `user` | Test 45, 46 | `403 Forbidden` |
| Role boleh ubah role | `super_admin`, `admin` | Test 55, 56 | `200 OK` |
| Role tidak boleh ubah role | `operator`, `user` | Test 61, 62 | `403 Forbidden` |

### EP pada Status Autentikasi Token

| Partisi | Nilai Representatif | Test Case | Expected Output |
|---------|--------------------|-----------|-----------------| 
| Token valid | Token aktif dan benar | Test 49 | `200 OK` |
| Token tidak ada | Header kosong | Test 50 | `401 Unauthorized` |
| Token tidak valid | String acak | Test 51 | `401 Unauthorized` |
| Token expired | Token kadaluarsa | Test 52 | `401 Unauthorized` |
| Token malformed | Token rusak/tidak lengkap | Test 53 | `401 Unauthorized` |

### EP pada Kepemilikan Device

| Partisi | Nilai Representatif | Test Case | Expected Output |
|---------|--------------------|-----------|-----------------| 
| Device milik sendiri | `device_claimed` milik admin | Test 6, 11 | `200 OK` |
| Device milik user lain | `device_other_user` | Test 29, 40, 96 | `404 Not Found` |
| Device belum diklaim | `device_unclaimed` | Test 95 | `404 Not Found` |
| Device tidak ada | UUID tidak terdaftar | Test 47, 93 | `404 Not Found` |

---

## 2. Boundary Value Analysis (BVA)

Menguji nilai tepat di batas minimum, tepat di batas maksimum, satu di bawah minimum, dan satu di atas maksimum. Diterapkan pada parameter numerik dan panjang string.

### BVA pada parameter `days` (range valid: 1–90)

| Nilai | Posisi Batas | Test Case | Expected Output |
|------:|-------------|-----------|-----------------|
| `-5` | Jauh di bawah minimum | Test 91 | `422 Validation Error` |
| `0` | Tepat di bawah minimum (min − 1) | Test 89 | `422 Validation Error` |
| `1` | Tepat minimum | Test 87 | `200 OK` |
| `7` | Nilai normal (default) | Test 79 | `200 OK` |
| `30` | Nilai tengah | Test 80 | `200 OK` |
| `90` | Tepat maksimum | Test 88 | `200 OK` |
| `91` | Tepat di atas maksimum (max + 1) | Test 90 | `422 Validation Error` |

### BVA pada panjang nama device (range valid: 1–100 karakter)

| Nilai | Posisi Batas | Test Case | Expected Output |
|-------|-------------|-----------|-----------------|
| `""` / `"   "` | Di bawah minimum (0 char setelah trim) | Test 42 | `422 Validation Error` |
| Nama valid (1–100 char) | Dalam range | Test 38 | `200 OK` |
| Nama > 100 karakter | Di atas maksimum | Test 43 | `422 Validation Error` |

### BVA yang belum diterapkan (gap)

Field-field berikut memiliki batas yang terdefinisi di API contract namun belum diuji secara eksplisit:

| Field | Range | Status |
|-------|-------|--------|
| `full_name` | 1–100 karakter | Batas tidak diuji eksplisit |
| `limit` (pagination) | 1–100 | Batas tidak diuji eksplisit |
| `page` | ≥ 1 | Batas bawah tidak diuji |
| FCM `token` | 10–500 karakter | Batas tidak diuji eksplisit |

---

## 3. Decision Table Testing (DTT)

Tidak diterapkan secara formal, namun pola kombinasi kondisi muncul secara implisit pada skenario assignment dan akses device. DTT formal mensyaratkan semua kombinasi kondisi diuji secara exhaustive.

### Pola mendekati DTT: akses device (role × kepemilikan)

| Role | Kepemilikan Device | Expected Output |
|------|--------------------|-----------------|
| `super_admin` | Device manapun | `200 OK` |
| `admin` | Device miliknya | `200 OK` |
| `admin` | Device milik admin lain | `404 Not Found` |
| `operator` | Device yang di-assign | `200 OK` |
| `operator` | Device tanpa assignment | `404 Not Found` |
| `viewer` | Device yang di-assign | `200 OK` (read-only) |
| `user` | Device manapun | `403 Forbidden` |

### Pola mendekati DTT: update role (role aktor × role target)

| Role Aktor | Role Target | Expected Output |
|------------|-------------|-----------------|
| `super_admin` | `admin` / `operator` / `viewer` / `user` | `200 OK` |
| `super_admin` | `super_admin` lain | `400 Bad Request` |
| `admin` | `operator` / `viewer` / `user` | `200 OK` |
| `admin` | `admin` / `super_admin` | `403 Forbidden` |
| `admin` | Diri sendiri | `400 Bad Request` |
| `operator` / `user` | Siapapun | `403 Forbidden` |

> Catatan: Kombinasi di atas tidak diuji secara exhaustive — tidak semua sel kombinasi memiliki test case tersendiri, sehingga ini bukan DTT formal.

---

## 4. State Transition Testing

Diterapkan secara implisit pada lifecycle device. Device memiliki state yang berpindah berdasarkan aksi tertentu.

### Diagram state device

```
[Unregistered] --register--> [Unclaimed] --claim--> [Claimed] --delete--> [Deleted]
                                                         |
                                                     unclaim
                                                         |
                                                         v
                                                    [Unclaimed]
```

### Tabel transisi yang diuji

| State Awal | Aksi | State Akhir | Test Case | Expected Output |
|------------|------|-------------|-----------|-----------------|
| Unregistered | Register (super_admin) | Unclaimed | Test 65 | `201 Created` |
| Unclaimed | Claim (admin) | Claimed | Test 1 | `200 OK` |
| Claimed | Unclaim (admin) | Unclaimed | Test 24 | `200 OK` |
| Claimed | Delete (super_admin) | Deleted | Test 44 | `200 OK` |
| Claimed | Claim lagi (admin lain) | — (ditolak) | Test 3 | `400 Bad Request` |
| Claimed | Delete → cek list | — (tidak ada) | Test 48 | Device tidak muncul di list |

### Transisi yang belum diuji

| State Awal | Aksi | Keterangan |
|------------|------|------------|
| Unclaimed | Delete | Belum ada test delete device unclaimed |
| Claimed | Claim oleh pemilik yang sama | Belum diuji |

---

## 5. Error Guessing

Berdasarkan intuisi dan pengalaman tentang kondisi yang sering menyebabkan bug. Tidak sistematis, tetapi melengkapi metode lain untuk menangkap edge case yang tidak tercakup EP/BVA/DTT.

| Skenario Error yang Ditebak | Test Case | Expected Output |
|-----------------------------|-----------|-----------------|
| Input tipe salah: `days=abc` (string bukan integer) | Test 92 | `422 Validation Error` |
| Format UUID tidak valid sebagai path parameter | Test 94 | `422 Validation Error` |
| Admin assign diri sendiri ke device | Test 60 | `400 Bad Request` |
| Duplicate assignment user yang sama ke device yang sama | Test 31 | `400 Bad Request` |
| Register MAC address yang sudah terdaftar | Test 65 (implisit) | `400 Bad Request` |
| Token tanpa prefix `Bearer` | Test 53 | `401 Unauthorized` |
| Cleanup logs saat tidak ada data lama | Test 77 | `200 OK`, `deleted_count = 0` |
| Statistik device yang tidak punya sensor log | Test 99 | `200 OK`, `statistics = []` |
| Sensor log ada tapi di luar range tanggal yang diminta | Test 100 | `200 OK`, `statistics = []` |

---

## 6. Ringkasan Penggunaan Metode

| Metode | Digunakan | Kualitas Penerapan | Jumlah Test Terkait |
|--------|:---------:|-------------------|:-------------------:|
| **Equivalence Partitioning (EP)** | ✅ Ya | Dominan dan konsisten — semua role dan state auth dipartisi dengan baik | ~70 test |
| **Boundary Value Analysis (BVA)** | ⚠️ Sebagian | Diterapkan pada `days` dan nama device; field lain (FCM token, limit, page) tidak diuji batasnya | ~9 test |
| **Decision Table Testing (DTT)** | ⚠️ Implisit | Pola kombinasi kondisi ada tapi tidak exhaustive dan tidak formal | ~15 test |
| **State Transition Testing** | ⚠️ Implisit | Lifecycle device diuji tapi tidak semua transisi tercakup | ~6 test |
| **Error Guessing** | ✅ Ya | Melengkapi metode lain untuk skenario edge case berbasis intuisi | ~9 test |
