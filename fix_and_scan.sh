#!/bin/bash
# Refined check to only count the actual python process, not the bash wrapper.
echo "CONTAINER  STUDENT_ID   PROCS   FIXED?"
echo "--------------------------------------"
for i in $(seq -w 01 29); do
    service="student$i"
    cid=$(docker compose ps -q "$service" 2>/dev/null)
    [ -z "$cid" ] && continue

    student_id=$(docker exec "$cid" env | grep STUDENT_ID | cut -d= -f2)
    [ -z "$student_id" ] && student_id="unknown"
    
    # Use grep to specifically match 'python3 app.py' but avoid the wrapper shell
    count=$(docker exec "$cid" ps -eo comm,args | grep '^python3.* app.py$' | wc -l)
    
    fixed="No"
    if [ "$count" -gt 1 ]; then
        docker exec "$cid" pkill -9 -f 'python3 app.py'
        docker exec -t "$cid" su - "$student_id" -c "cd /home/$student_id && nohup python3 app.py > /var/log/student-apps/$student_id/app.log 2>&1 &"
        fixed="Yes"
    fi
    printf "%-10s %-12s %-5s %-6s\n" "$service" "$student_id" "$count" "$fixed"
done

echo ""
echo "Rescanning for duplicates..."
echo "CONTAINER  STUDENT_ID   PROCS"
echo "----------------------------"
for i in $(seq -w 01 29); do
    service="student$i"
    cid=$(docker compose ps -q "$service" 2>/dev/null)
    [ -z "$cid" ] && continue
    student_id=$(docker exec "$cid" env | grep STUDENT_ID | cut -d= -f2)
    count=$(docker exec "$cid" ps -eo comm,args | grep '^python3.* app.py$' | wc -l)
    [ "$count" -gt 1 ] && printf "%-10s %-12s %-5s\n" "$service" "$student_id" "$count"
done

echo ""
echo "Student29 Web Check (Port 30000):"
curl -Is http://127.0.0.1:30000 | head -n 1
