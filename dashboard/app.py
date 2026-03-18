import subprocess, threading, time
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = "kbu_sql_lab_secret_key_2026" # 세션 암호화 키
socketio = SocketIO(app, cors_allowed_origins="*")

# 학생 데이터 (원본 유지)
STUDENT_DATA = [
    ("Baltukov Nomto", "2501125", "nomto"), ("CONTRERAS RIVERA MAURO JEISON", "2501111", "maurocontrerasrivera"),
    ("Dorzhieva Aiana", "2201901", "2201901aia"), ("UYANIK ILSU SUZAN", "2501115", "ilsusuzanuyanik26"),
    ("강문성", "2301301", "moonsung121200"), ("강성우", "2501003", "sjwwa951"),
    ("김광호", "2301104", "kkm9514269"), ("김준석", "2201403", "baby3565"),
    ("김진형", "2301112", "rlawlsgud2438"), ("김찬민", "2301113", "chanmin9689"),
    ("문초연", "2501080", "choyeon-mun"), ("박성준", "2301206", "goldbong74"),
    ("박준성", "2301306", "pjspjs04"), ("박지혜", "2501089", "star88222"),
    ("배정환", "2501090", "hwanarchive"), ("석민재", "2301209", "0425seok"),
    ("신윤호", "2301123", "younhnoo0325"), ("엄태영", "2501045", "sjdisjsjs90"),
    ("이순주", "2301129", "l90670847"), ("이어진", "2501058", "a46750309"),
    ("이웅재", "2501059", "kyalkwlww1"), ("이현재", "2401061", "goxodpdltm"),
    ("이희성", "2201130", "dlgmltjd3353"), ("장한별", "2501092", "hanbyul0623"),
    ("정구진", "2301136", "koojin0708"), ("정서윤", "2501085", "snsynu"),
    ("최민혁", "2501073", "minb55"), ("황연준", "2501076", "yeonjun0103"),
    ("System Admin", "0000000", "test1234")
]

def get_status():
    try:
        output = subprocess.check_output("docker ps --format '{{.Names}}'", shell=True).decode()
    except:
        output = ""
    
    students = []
    for i, (name, s_id, _) in enumerate(STUDENT_DATA, 1):
        container_name = f"student{i:02d}"
        linux_user = f"s{s_id}"
        
        # 실제 프로세스 체크 (SSH/ttyd 접속 여부)
        try:
            check_cmd = f"docker exec {container_name} ps aux | grep '^{linux_user}'"
            is_active = subprocess.run(check_cmd, shell=True, capture_output=True).returncode == 0
            status = "🟢 실습 중" if is_active else "⚪ 오프라인"
        except:
            status = "⚪ 오프라인"
            
        if s_id == "0000000": status = "🟢 관리 중"
        
        last_4 = s_id[-4:]
        students.append({
            "name": name, "id": s_id, "ssh": f"2{last_4}",
            "web": f"3{last_4}", "terminal": f"5{last_4}", "status": status
        })
    return students

@app.route('/')
def index():
    return render_template('index.html')

# --- 로그인 라우트 ---
@app.route('/login/<student_id>', methods=['GET', 'POST'])
def login(student_id):
    # 해당 학생 데이터 찾기
    student = next((s for s in STUDENT_DATA if s[1] == student_id), None)
    if not student:
        return "Student not found", 404

    if request.method == 'POST':
        input_pw = request.form.get('password')
        if input_pw == student[2]: # 비밀번호 일치 확인
            session[f'auth_{student_id}'] = True # 세션에 인증 기록
            host = request.host.split(':')[0]
            port = f"5{student_id[-4:]}"
            return redirect(f"http://{host}:{port}")
        else:
            flash("비밀번호가 틀렸습니다.")
    
    return render_template('login.html', student_name=student[0], student_id=student_id)

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
