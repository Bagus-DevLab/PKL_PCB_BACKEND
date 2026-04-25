#!/bin/bash
# ===========================================
# Script Cleanup Sensor Logs Lama
# ===========================================
# Penggunaan:
#   ./scripts/cleanup_logs.sh              # cleanup dengan retention default dari .env
#   ./scripts/cleanup_logs.sh 180          # cleanup logs lebih lama dari 180 hari
#
# Untuk cron job (setiap Minggu jam 4 pagi):
#   0 4 * * 0 /opt/api-pcb/scripts/cleanup_logs.sh >> /opt/api-pcb/logs/cleanup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTAINER_NAME="pcb_pkl_postgres"

# Load .env (tr -d '\r' untuk handle Windows line endings)
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -E '^(POSTGRES_USER|POSTGRES_DB|SENSOR_LOG_RETENTION_DAYS)=' "$PROJECT_DIR/.env" | tr -d '\r' | xargs)
fi

# Tentukan retention days
DAYS="${1:-${SENSOR_LOG_RETENTION_DAYS:-365}}"

# Validasi: DAYS harus integer positif (mencegah SQL injection)
if ! echo "$DAYS" | grep -qE '^[0-9]+$'; then
    echo "$(date): ERROR - DAYS harus berupa angka positif, bukan '$DAYS'"
    exit 1
fi

if [ "$DAYS" -eq 0 ]; then
    echo "$(date): Cleanup di-disable (SENSOR_LOG_RETENTION_DAYS=0). Skip."
    exit 0
fi

# Cek container running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "$(date): ERROR - Container $CONTAINER_NAME tidak running"
    exit 1
fi

echo "$(date): Memulai cleanup sensor logs lebih lama dari $DAYS hari..."

# Hitung jumlah yang akan dihapus
COUNT=$(docker exec -u postgres "$CONTAINER_NAME" psql \
    -U "${POSTGRES_USER:-iot_user}" \
    -d "${POSTGRES_DB:-iot_db}" \
    -t -c "SELECT COUNT(*) FROM sensor_logs WHERE timestamp < NOW() - INTERVAL '${DAYS} days';" \
    | tr -d ' ')

if [ "$COUNT" -eq 0 ] 2>/dev/null; then
    echo "$(date): Tidak ada logs yang perlu dihapus."
    exit 0
fi

echo "$(date): Akan menghapus $COUNT sensor logs..."

# Hapus data lama
docker exec -u postgres "$CONTAINER_NAME" psql \
    -U "${POSTGRES_USER:-iot_user}" \
    -d "${POSTGRES_DB:-iot_db}" \
    -c "DELETE FROM sensor_logs WHERE timestamp < NOW() - INTERVAL '${DAYS} days';"

echo "$(date): Cleanup selesai. $COUNT sensor logs dihapus."
