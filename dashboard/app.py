
import io
import json
import subprocess
import tarfile
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO

import os

# Load student map from students.json and generate container_name
def _get_student_map():
    students_path = os.path.join(os.path.dirname(__file__), 'students.json')
    with open(students_path, encoding='utf-8') as f:
        students = json.load(f)
    student_map = {}
    for s in students:
        sid = s.get('id')
        name = s.get('name')
        slot = s.get('slot')
        # Container name convention: student{slot:02d}
        container_name = f"student{int(slot):02d}" if slot is not None else None
        student_map[sid] = {
            'name': name,
            'container_name': container_name
        }
    return student_map

REACT_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'react-dashboard', 'dist')

app = Flask(__name__)
app.secret_key = "kbu_sql_lab_secret_key_2026" # 세션 암호화 키
socketio = SocketIO(app, cors_allowed_origins="*")
APP_GUARD_LOG_ROOT = Path(__file__).resolve().parent.parent / "student_logs"

# 메인 대시보드: 템플릿 기반
@app.route('/')
def dashboard():
    return render_template('index.html')

# 상태 API
@app.route('/api/status')
def api_status():
    return jsonify({"students": get_status(), "app_guard_alerts": get_app_guard_alerts()})


@app.route('/api/alerts/app-guard')
def api_app_guard_alerts():
    return jsonify({"alerts": get_app_guard_alerts()})

# 학생별 컨테이너 상태 반환
def get_status():
    students = _get_student_map()
    result = []
    for sid, info in students.items():
        try:
            ps = subprocess.run([
                "docker", "inspect", "-f", "{{.State.Running}}", info["container_name"]
            ], capture_output=True, text=True, timeout=3)
            running = (ps.stdout.strip() == "true")
        except Exception:
            running = False
        # SSH 세션 체크 (who 명령)
        online = False
        if running:
            # login_id는 s학번 형식, 없으면 sid 사용
            login_id = f"s{sid}"
            try:
                who_cmd = [
                    "docker", "exec", info["container_name"],
                    "sh", "-c", f"who | grep {login_id} || true"
                ]
                who_ps = subprocess.run(who_cmd, capture_output=True, text=True, timeout=3)
                online = bool(who_ps.stdout.strip())
            except Exception:
                online = False
        status = "온라인" if online else "오프라인"
        result.append({
            "id": sid,
            "name": info["name"],
            "container_name": info["container_name"],
            "running": running,
            "status": status
        })
    return result


def get_app_guard_alerts(limit=20):
    alerts = []
    if not APP_GUARD_LOG_ROOT.exists():
        return alerts

    for sid_dir in APP_GUARD_LOG_ROOT.iterdir():
        if not sid_dir.is_dir():
            continue

        log_file = sid_dir / "app_guard.log"
        if not log_file.exists():
            continue

        try:
            lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for line in lines[-30:]:
            text = line.strip()
            if not text:
                continue

            ts = None
            msg = text
            if text.startswith("[") and "]" in text:
                raw_ts = text[1:text.find("]")]
                try:
                    ts = datetime.strptime(raw_ts, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ts = None
                msg = text[text.find("]") + 1:].strip()

            alerts.append({
                "student_id": sid_dir.name,
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S") if ts else "",
                "message": msg,
                "sort_key": ts.timestamp() if ts else 0,
            })

    alerts.sort(key=lambda item: item["sort_key"], reverse=True)
    for item in alerts:
        item.pop("sort_key", None)
    return alerts[:limit]

@socketio.on('connect')
def handle_connect(auth=None):
    socketio.emit('update', {'students': get_status(), 'app_guard_alerts': get_app_guard_alerts()})

def status_refresher():
    while True:
        socketio.emit('update', {'students': get_status(), 'app_guard_alerts': get_app_guard_alerts()})
        time.sleep(2)

if __name__ == '__main__':
    threading.Thread(target=status_refresher, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=8081, allow_unsafe_werkzeug=True)
