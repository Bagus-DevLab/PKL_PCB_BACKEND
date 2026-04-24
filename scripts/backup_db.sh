#!/bin/bash
# ===========================================
# Script Backup Database PostgreSQL
# ===========================================
# Penggunaan:
#   ./scripts/backup_db.sh              # backup manual
#   ./scripts/backup_db.sh --auto       # backup otomatis (untuk cron)
#
# Backup disimpan di folder ./backups/ dengan format:
#   backup_YYYY-MM-DD_HH-MM-SS.sql.gz
#
# Restore:
#   gunzip -c backups/backup_xxx.sql.gz | docker exec -i pcb_pkl_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

set -euo pipefail

# Konfigurasi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
CONTAINER_NAME="pcb_pkl_postgres"
MAX_BACKUPS=30  # Simpan maksimal 30 backup terakhir

# Load .env untuk mendapatkan credentials
# tr -d '\r' untuk handle Windows line endings (CRLF)
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -E '^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB)=' "$PROJECT_DIR/.env" | tr -d '\r' | xargs)
fi

# Validasi
if [ -z "${POSTGRES_USER:-}" ] || [ -z "${POSTGRES_DB:-}" ]; then
    echo "ERROR: POSTGRES_USER atau POSTGRES_DB tidak ditemukan di .env"
    exit 1
fi

# Cek apakah container postgres sedang running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container $CONTAINER_NAME tidak sedang running"
    exit 1
fi

# Buat folder backup jika belum ada
mkdir -p "$BACKUP_DIR"

# Generate nama file backup
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql.gz"

echo "=== Backup Database PostgreSQL ==="
echo "Waktu    : $(date)"
echo "Database : $POSTGRES_DB"
echo "User     : $POSTGRES_USER"
echo "Output   : $BACKUP_FILE"
echo ""

# Jalankan pg_dump di dalam container, compress dengan gzip
# Jalankan pg_dump sebagai OS user 'postgres' di dalam container
# agar peer authentication via Unix socket berhasil
docker exec -u postgres "$CONTAINER_NAME" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
    --format=plain \
    | gzip > "$BACKUP_FILE"

# Cek apakah backup berhasil
if [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "SUKSES: Backup selesai ($SIZE)"
else
    echo "ERROR: Backup gagal — file kosong"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Hapus backup lama (simpan hanya MAX_BACKUPS terakhir)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    DELETE_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    echo "Menghapus $DELETE_COUNT backup lama..."
    ls -1t "$BACKUP_DIR"/backup_*.sql.gz | tail -n "$DELETE_COUNT" | xargs rm -f
fi

echo "Total backup tersimpan: $(ls -1 "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | wc -l)"
echo "=== Selesai ==="
