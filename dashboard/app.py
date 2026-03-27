import io
import json
import subprocess
import tarfile
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = "kbu_sql_lab_secret_key_2026" # 세션 암호화 키
socketio = SocketIO(app, cors_allowed_origins="*")

STUDENTS_JSON = Path("/app/students.json")

def _load_students():
    with open(STUDENTS_JSON, encoding="utf-8") as f:
        return json.load(f)

def _get_student_map():
    return {
        s["id"]: {
            "name": s["name"],
            "password": s["password"],
            "container_name": f"student{s['slot']:02d}",
            "linux_user": s.get("linux_user") or f"s{s['id']}",
        }
        for s in _load_students() if s.get("id")
    }

def get_status():
    students = []
    for s in _load_students():
        if not s.get("id"):
            continue
        container_name = f"student{s['slot']:02d}"
        linux_user = f"s{s['id']}"
        try:
            r = subprocess.run(
                f"docker exec {container_name} ps aux | grep '^{linux_user}'",
                shell=True, capture_output=True
            )
            status = "🟢 실습 중" if r.returncode == 0 else "⚪ 오프라인"
        except Exception:
            status = "⚪ 오프라인"
        if s["id"] == "0000000":
            status = "🟢 관리 중"
        students.append({"name": s["name"], "id": s["id"], "status": status})
    return students


def build_home_archive(student_id):
    student = _get_student_map()[student_id]
    container_name = student["container_name"]
    linux_user = student["linux_user"]
    tar_command = (
        "docker exec "
        f"{container_name} "
        "sh -lc "
        f"'tar -cf - -C /home/{linux_user} .'"
    )
    tar_result = subprocess.run(tar_command, shell=True, capture_output=True)
    if tar_result.returncode != 0:
        raise RuntimeError(tar_result.stderr.decode(errors="ignore") or "archive failed")

    zip_buffer = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(tar_result.stdout), mode='r:') as tar:
        with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for member in tar.getmembers():
                # Skip device nodes and unsupported special files in zip.
                if not (member.isfile() or member.isdir() or member.issym()):
                    continue

                arcname = member.name.lstrip('./')
                if not arcname:
                    continue

                if member.isdir():
                    zf.writestr(arcname.rstrip('/') + '/', b'')
                elif member.issym():
                    info = zipfile.ZipInfo(arcname)
                    info.create_system = 3
                    info.external_attr = 0o120777 << 16
                    zf.writestr(info, member.linkname)
                else:
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        continue
                    zf.writestr(arcname, extracted.read())

    return zip_buffer.getvalue()

@app.route('/')
def index():
    return render_template('index.html', students=get_status())


@app.route('/download/<student_id>', methods=['GET', 'POST'])
def download(student_id):
    student = _get_student_map().get(student_id)
    if student is None:
        return Response('학생 정보를 찾을 수 없습니다.', status=404, mimetype='text/plain; charset=utf-8')

    if request.method == 'POST':
        if request.form.get('password') != student['password']:
            flash('비밀번호가 올바르지 않습니다.')
            return redirect(url_for('download', student_id=student_id))

        session[f'download_auth_{student_id}'] = True
        return redirect(url_for('download_file', student_id=student_id))

    return render_template('login.html', student_name=student['name'])


@app.route('/download/<student_id>/file')
def download_file(student_id):
    student = _get_student_map().get(student_id)
    if student is None:
        return Response('학생 정보를 찾을 수 없습니다.', status=404, mimetype='text/plain; charset=utf-8')

    if not session.get(f'download_auth_{student_id}'):
        return redirect(url_for('download', student_id=student_id))

    session.pop(f'download_auth_{student_id}', None)

    archive_bytes = build_home_archive(student_id)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"s{student_id}_home_{timestamp}.zip"
    return Response(
        archive_bytes,
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )

@socketio.on('connect')
def handle_connect():
    socketio.emit('update', {'students': get_status()})

def status_refresher():
    while True:
        socketio.emit('update', {'students': get_status()})
        time.sleep(2)

if __name__ == '__main__':
    threading.Thread(target=status_refresher, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=80, allow_unsafe_werkzeug=True)
