#!/bin/bash
# ===========================================
# Script Restore Database PostgreSQL
# ===========================================
# Penggunaan:
#   ./scripts/restore_db.sh backups/backup_2026-04-24_12-00-00.sql.gz
#
# PERINGATAN: Script ini akan MENGHAPUS semua data yang ada
# dan menggantinya dengan data dari backup!

set -euo pipefail

# Konfigurasi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTAINER_NAME="pcb_pkl_postgres"

# Load .env (tr -d '\r' untuk handle Windows line endings)
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -E '^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB)=' "$PROJECT_DIR/.env" | tr -d '\r' | xargs)
fi

# Validasi argument
if [ -z "${1:-}" ]; then
    echo "Penggunaan: $0 <path-ke-backup.sql.gz>"
    echo ""
    echo "Backup yang tersedia:"
    ls -lh "$PROJECT_DIR/backups"/backup_*.sql.gz 2>/dev/null || echo "  (tidak ada backup)"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: File backup tidak ditemukan: $BACKUP_FILE"
    exit 1
fi

# Validasi
if [ -z "${POSTGRES_USER:-}" ] || [ -z "${POSTGRES_DB:-}" ]; then
    echo "ERROR: POSTGRES_USER atau POSTGRES_DB tidak ditemukan di .env"
    exit 1
fi

# Cek container
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container $CONTAINER_NAME tidak sedang running"
    exit 1
fi

echo "=== Restore Database PostgreSQL ==="
echo "Waktu    : $(date)"
echo "Database : $POSTGRES_DB"
echo "Backup   : $BACKUP_FILE"
echo ""
echo "PERINGATAN: Semua data di database '$POSTGRES_DB' akan DIHAPUS"
echo "dan diganti dengan data dari backup!"
echo ""
read -p "Lanjutkan? (ketik 'ya' untuk konfirmasi): " CONFIRM

if [ "$CONFIRM" != "ya" ]; then
    echo "Dibatalkan."
    exit 0
fi

echo ""
echo "Menghapus data lama..."

# Drop dan recreate semua tabel
docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO $POSTGRES_USER;
"

echo "Merestore data dari backup..."

# Restore dari backup
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --quiet

echo ""
echo "SUKSES: Database berhasil di-restore dari $BACKUP_FILE"
echo ""

# Tampilkan ringkasan data
echo "=== Ringkasan Data ==="
docker exec "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT 'users' as tabel, COUNT(*) as jumlah FROM users
    UNION ALL
    SELECT 'devices', COUNT(*) FROM devices
    UNION ALL
    SELECT 'sensor_logs', COUNT(*) FROM sensor_logs;
"

echo "=== Selesai ==="
