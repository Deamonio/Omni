#!/bin/bash
container=$1
student_id=$(docker exec "$container" env | grep STUDENT_ID | cut -d= -f2)
[[ -z "$student_id" ]] && student_id="unknown"
docker exec "$container" pkill -f "python.*app.py" || true
docker exec -u "$student_id" -w "/home/$student_id" "$container" /bin/bash -c "PYTHONPATH=. nohup /usr/local/bin/python3 app.py > app.log 2>&1 &"
sleep 2
proc_count=$(docker exec "$container" pgrep -f "python.*app.py" | wc -l)
host_port=$(docker port "$container" 5000 | grep -oE "[0-9]+$" | head -n1)
[[ -n "$host_port" ]] && http_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:$host_port") || http_status="no_port"
echo "$container|$student_id|$proc_count|$http_status"
if [[ "$proc_count" -eq 0 ]] || [[ "$http_status" != "200" ]]; then
  echo "--- ERROR LOG for $container ($student_id) ---"
  docker exec "$container" tail -n 20 "/home/$student_id/app.log" 2>/dev/null || echo "Log file not found"
  echo "--- END LOG ---"
fi
