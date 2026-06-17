#!/bin/bash
printf "%-10s %-12s %-10s %-8s %-12s %-8s\n" "CONTAINER" "STUDENT_ID" "PROCS" "PORT" "STATUS" "RESULT"
echo "-------------------------------------------------------------------------------"

flagged=""
total=0
flag_count=0

for i in $(seq -w 01 29); do
    service="student$i"
    cid=$(docker compose ps -q "$service" 2>/dev/null)
    if [ -z "$cid" ]; then continue; fi
    
    total=$((total+1))
    student_id=$(docker exec "$cid" env | grep STUDENT_ID | cut -d= -f2)
    port=$(docker port "$cid" 5000 | head -n1 | cut -d: -f2)
    
    # Count processes carefully to avoid grep itself
    proc_count=$(docker exec "$cid" ps -ef | grep 'python3 app.py' | grep -v grep | wc -l)
    
    # Check HTTP status
    status=$(curl -sS -I --max-time 4 "http://127.0.0.1:$port" 2>/dev/null | head -n 1 | cut -d' ' -f2)
    [ -z "$status" ] && status="FAIL"
    
    # Determine result
    res="OK"
    if [ "$proc_count" -gt 1 ] || [ "$status" = "FAIL" ]; then
        res="FLAG"
        flag_count=$((flag_count+1))
        flagged+="$service ($student_id): procs=$proc_count, port=$port, status=$status\n"
    fi
    
    printf "%-10s %-12s %-10s %-8s %-12s %-8s\n" "$service" "$student_id" "$proc_count" "$port" "$status" "$res"
done

echo "-------------------------------------------------------------------------------"
echo "Total: $total, Flagged: $flag_count"
if [ $flag_count -gt 0 ]; then
    echo -e "\nFlagged Rows Summary:"
    echo -e "$flagged"
    
    echo "Suggested Fix Commands for Flagged Rows (Multiple Processes):"
    for i in $(seq -w 01 29); do
        service="student$i"
        cid=$(docker compose ps -q "$service" 2>/dev/null)
        if [ -z "$cid" ]; then continue; fi
        proc_count=$(docker exec "$cid" ps -ef | grep 'python3 app.py' | grep -v grep | wc -l)
        student_id=$(docker exec "$cid" env | grep STUDENT_ID | cut -d= -f2)
        if [ "$proc_count" -gt 1 ]; then
             echo "docker exec $cid sh -lc \"pkill -f 'python3 app.py' || true; su - $student_id -c 'cd /home/$student_id && nohup python3 app.py </dev/null >/var/log/student-apps/$student_id/app.log 2>&1 &'\""
        fi
    done
fi
