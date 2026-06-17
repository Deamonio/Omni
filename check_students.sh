#!/bin/bash
printf "%-10s | %-10s | %-15s | %-15s | %-15s\n" "Container" "Count" "Ports" "Resp5000" "Resp5001"
printf "%-10s-|-%-10s-|-%-15s-|-%-15s-|-%-15s\n" "----------" "----------" "---------------" "---------------" "---------------"

suspicious=""

for i in $(seq -f "%02g" 1 29); do
  container="student$i"
  # Check if container is running
  if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
    continue
  fi

  # 1) count app.py processes
  count=$(docker exec "$container" bash -c "pgrep -af 'python.*app.py' | wc -l")
  
  # 2) list listening ports among 5000-5010
  ports=$(docker exec "$container" bash -c "ss -ltn | awk 'NR>1{print \$4}' | sed 's/.*://' | grep -E '^(500[0-9]|5010)$' | sort -n | uniq | tr '\n' ',' | sed 's/,$//'")
  
  # 3) capture first line response from 5000 and 5001
  resp5000=""
  if [[ $ports == *"5000"* ]]; then
    resp5000=$(docker exec "$container" bash -c "curl -s --max-time 2 http://127.0.0.1:5000 | head -n1" | tr -d '\r\n' | cut -c1-15)
  fi
  
  resp5001=""
  if [[ $ports == *"5001"* ]]; then
    resp5001=$(docker exec "$container" bash -c "curl -s --max-time 2 http://127.0.0.1:5001 | head -n1" | tr -d '\r\n' | cut -c1-15)
  fi

  printf "%-10s | %-10s | %-15s | %-15s | %-15s\n" "$container" "$count" "$ports" "$resp5000" "$resp5001"

  # Suspicious check
  if [[ $count -gt 1 ]] || [[ $ports == *"5000"* && $ports == *"5001"* ]]; then
    suspicious="$suspicious $container"
  fi
done

echo ""
echo "Suspicious containers:$suspicious"
