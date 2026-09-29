#!/bin/bash
set -euo pipefail

touch "${POSTIDS_FILE:-/data/postids.txt}"

python reddit_response.py &
pid_response=$!
python msg_monitor.py &
pid_monitor=$!

shutdown() {
    kill -TERM "${pid_response}" "${pid_monitor}" 2>/dev/null || true
    wait "${pid_response}" "${pid_monitor}" 2>/dev/null || true
}

trap shutdown INT TERM

wait -n "${pid_response}" "${pid_monitor}"
exit_code=$?
shutdown
exit "${exit_code}"
