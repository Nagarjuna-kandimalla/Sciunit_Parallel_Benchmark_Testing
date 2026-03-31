#!/bin/bash

set -euo pipefail

BATCH_FILE_INPUT=$1
MODE=$2
SIZE=$3
PROCESS_SCRIPT=$4
ENABLE_MONITOR=${5:-false}
MONITOR_SCRIPT=${6:-scripts/execution/monitor.py}
RUN_LABEL=${7:-adhoc_$(date +%Y%m%d_%H%M%S)}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
source "$REPO_ROOT/execution/common/env_setup.sh"

resolve_path() {
    local path=$1
    if [[ "$path" = /* ]]; then
        printf '%s\n' "$path"
    else
        printf '%s/%s\n' "$REPO_ROOT" "$path"
    fi
}

cleanup_monitor() {
    local pid=${MONITOR_PID:-}

    if [[ -z "$pid" ]]; then
        return
    fi

    if kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null || true

        for _ in $(seq 1 20); do
            if ! kill -0 "$pid" 2>/dev/null; then
                MONITOR_PID=""
                return
            fi
            sleep 0.1
        done

        kill -KILL "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    fi

    MONITOR_PID=""
}

BATCH_FILE=$(resolve_path "$BATCH_FILE_INPUT")
BATCH_ID=$(basename "$BATCH_FILE" .txt)
RUN_RESULTS_ROOT="$REPO_ROOT/results/${RUN_LABEL}"
RUN_METRICS_ROOT="$REPO_ROOT/metrics/${RUN_LABEL}"
RUN_LOG_ROOT="$REPO_ROOT/logs/${RUN_LABEL}"

LOG_FILE="$RUN_LOG_ROOT/batch/${MODE}/${SIZE}/${BATCH_ID}_${RUN_LABEL}.log"
MONITOR_FILE="$RUN_LOG_ROOT/monitor/${MODE}_${SIZE}_${BATCH_ID}_${RUN_LABEL}.csv"

mkdir -p "$(dirname "$LOG_FILE")"
cd "$REPO_ROOT"

if [[ ! -f "$BATCH_FILE" ]]; then
    echo "[ERROR] Batch file not found: $BATCH_FILE" | tee "$LOG_FILE"
    exit 1
fi

if [[ ! -f "$PROCESS_SCRIPT" ]]; then
    echo "[ERROR] Process script not found: $PROCESS_SCRIPT" | tee "$LOG_FILE"
    exit 1
fi

echo "[START] Batch: $BATCH_ID" | tee "$LOG_FILE"
echo "[INFO] Mode: $MODE | Size: $SIZE" | tee -a "$LOG_FILE"
echo "[INFO] Run label: $RUN_LABEL" | tee -a "$LOG_FILE"
echo "[INFO] Batch file: $BATCH_FILE" | tee -a "$LOG_FILE"
echo "[INFO] Process script: $PROCESS_SCRIPT" | tee -a "$LOG_FILE"

if [[ "$ENABLE_MONITOR" == "true" ]]; then
    mkdir -p "$(dirname "$MONITOR_FILE")"
    echo "[INFO] Starting monitor: $MONITOR_FILE" | tee -a "$LOG_FILE"
    python "$MONITOR_SCRIPT" "$MONITOR_FILE" >> "$LOG_FILE" 2>&1 &
    MONITOR_PID=$!
    trap cleanup_monitor EXIT
fi

START_TIME=$(date +%s)
PIDS=()

while IFS= read -r SPLIT_PATH || [[ -n "$SPLIT_PATH" ]]; do
    [[ -z "$SPLIT_PATH" ]] && continue

    INPUT_PATH=$(resolve_path "$SPLIT_PATH")
    SPLIT_NAME=$(basename "$INPUT_PATH" .txt)

    OUTPUT_FILE="$RUN_RESULTS_ROOT/${MODE}/${SIZE}/processed/${SPLIT_NAME}_${RUN_LABEL}.out"
    METRICS_FILE="$RUN_METRICS_ROOT/raw/${MODE}/${SIZE}/${SPLIT_NAME}_${RUN_LABEL}.json"
    RULE_LOG="$RUN_LOG_ROOT/rules/${MODE}/${SIZE}/${SPLIT_NAME}_${RUN_LABEL}.log"

    mkdir -p "$(dirname "$OUTPUT_FILE")"
    mkdir -p "$(dirname "$METRICS_FILE")"
    mkdir -p "$(dirname "$RULE_LOG")"

    echo "[INFO] Launching split: $SPLIT_NAME" | tee -a "$LOG_FILE"

    python "$PROCESS_SCRIPT" \
        "$INPUT_PATH" \
        "$OUTPUT_FILE" \
        "$METRICS_FILE" \
        "$RULE_LOG" &

    PIDS+=($!)
done < "$BATCH_FILE"

FAIL=0

for PID in "${PIDS[@]}"; do
    wait "$PID" || FAIL=1
done

cleanup_monitor
trap - EXIT

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$FAIL" -ne 0 ]; then
    echo "[ERROR] Batch $BATCH_ID failed!" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[END] Batch: $BATCH_ID completed successfully" | tee -a "$LOG_FILE"
echo "[INFO] Duration: ${DURATION}s" | tee -a "$LOG_FILE"
