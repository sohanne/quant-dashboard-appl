#!/usr/bin/env bash
set -euo pipefail

DATA_FILE="data/aapl_prices.csv"
REPORT_DIR="reports"

TODAY="$(date +%F)"
REPORT_FILE="${REPORT_DIR}/report_${TODAY}.txt"

mkdir -p "${REPORT_DIR}"

if [ ! -f "${DATA_FILE}" ]; then
  echo "[ERROR] Data file not found: ${DATA_FILE}" > "${REPORT_FILE}"
  exit 1
fi

LINES_COUNT="$(tail -n +2 "${DATA_FILE}" | wc -l | tr -d ' ')"

if [ "${LINES_COUNT}" -eq 0 ]; then
  echo "[ERROR] No data in ${DATA_FILE}" > "${REPORT_FILE}"
  exit 1
fi

FIRST_PRICE="$(tail -n +2 "${DATA_FILE}" | head -n 1 | cut -d',' -f2)"
LAST_PRICE="$(tail -n 1 "${DATA_FILE}" | cut -d',' -f2)"

MIN_PRICE="$(tail -n +2 "${DATA_FILE}" | cut -d',' -f2 | sort -n | head -n 1)"
MAX_PRICE="$(tail -n +2 "${DATA_FILE}" | cut -d',' -f2 | sort -n | tail -n 1)"

CHANGE_PCT="$(awk -v first="${FIRST_PRICE}" -v last="${LAST_PRICE}" 'BEGIN {
  if (first == 0) { print "NA"; exit }
  printf "%.4f", ((last - first) / first) * 100
}')"

{
  echo "Daily report - AAPL"
  echo "Date: ${TODAY}"
  echo ""
  echo "Data source file: ${DATA_FILE}"
  echo "Number of points: ${LINES_COUNT}"
  echo ""
  echo "First price: ${FIRST_PRICE}"
  echo "Last price:  ${LAST_PRICE}"
  echo "Min price:   ${MIN_PRICE}"
  echo "Max price:   ${MAX_PRICE}"
  echo ""
  echo "Change (%):  ${CHANGE_PCT}"
} > "${REPORT_FILE}"

echo "[OK] Report written to ${REPORT_FILE}"
