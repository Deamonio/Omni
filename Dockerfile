# 1. 베이스 이미지
FROM python:3.11-slim

# 2. 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    openssh-server default-mysql-server vim procps curl gnupg locales zip sudo \
    docker.io libjson-c-dev libwebsockets-dev cmake g++ pkg-config git \
    && rm -rf /var/lib/apt/lists/*

# ttyd 정적 바이너리 설치 (Debian 저장소 미포함 대응)
RUN curl -fsSL -o /usr/local/bin/ttyd \
    https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 \
    && chmod +x /usr/local/bin/ttyd

# 3. Node.js & PM2 설치
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && npm install pm2 -g

# 5. 로케일 설정
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# 6. Python 라이브러리 (필요 패키지 통합 설치)
RUN pip install --no-cache-dir flask flask-socketio eventlet pymysql flask-sqlalchemy gunicorn

# 7. SSH 및 시스템 설정
RUN mkdir -p /var/run/sshd /run/mysqld && \
    chown -R mysql:mysql /run/mysqld /var/lib/mysql && \
    sed -i 's/#PrintMotd yes/PrintMotd no/' /etc/ssh/sshd_config && \
    sed -i 's/^PrintMotd yes/PrintMotd no/' /etc/ssh/sshd_config && \
    grep -q '^PrintLastLog no' /etc/ssh/sshd_config || echo 'PrintLastLog no' >> /etc/ssh/sshd_config && \
    sed -i 's/^session\s\+optional\s\+pam_motd.so/#&/' /etc/pam.d/sshd && \
    echo "session    required     pam_unix.so" >> /etc/pam.d/sshd && \
    echo "session    optional     pam_loginuid.so" >> /etc/pam.d/sshd

WORKDIR /home
# 8. Kyungbok ASCII ART (MOTD)
# ASCII art 색상 + NOTICE 통합 (Python으로 ANSI 코드 생성)
RUN cat <<'PYEOF' > /tmp/gen_motd.py
E = '\033'
BC = E+'[1;36m'
C  = E+'[0;36m'
Y  = E+'[1;33m'
R  = E+'[1;31m'
W  = E+'[1;37m'
RS = E+'[0m'
SEP = C + '\u2500'*80 + RS

aa = [
        '   _  __                              _              _   ',
        '  | |/ / _   _  _   _  _ __    __ _  | |__    ___   | | __',
        "  | ' / | | | || | | || '_ \\  / _` | | '_ \\  / _ \\  | |/ /",
        '  | . \\ | |_| || |_| || | | || (_| | | |_) || (_) | | <',
        '  |_|\\_\\ \\__, | \\__,_||_| |_| \\__, | |_.__/  \\___/  |_|\\_\\',
        '         |___/                |___/',
]

rows = [
    BC + '='*80 + RS,
    *[BC + l + RS for l in aa],
    C + '  ' + '\u2500'*76 + RS,
    '  경복대학교 소프트웨어융합학과  ·  SQL 활용 실습 서버  ·  지도교수: 고철영 교수님',
    '  Managed by Deamon.io',
    SEP,
    '',
    ' ' + Y + '◆ 실습 환경 안내' + RS,
    '   작업 경로 │ /home/s[학번]',
    '   웹 실행   │ python3 app.py',
    '   웹 주소   │ https://[본인학번].rai.cortie.io',
    '   DB 접속   │ mysql  (터미널에서 바로 실행)',
    '   공용 자료 │ ~/shared  (읽기 전용)  →  cp ~/shared/파일명 ~/',
    '   파일 백업 │ https://rai.cortie.io  대시보드 › 학번별 다운로드',
    '',
    SEP,
    ' ' + R + '◆ 보안 및 이용 수칙' + RS,
    '   🛡  CPU/MEM 자원 점유율 실시간 감시 중',
    '   📝  모든 접속 및 주요 명령어 실행 로그 저장',
    '   🚫  비정상 접근 · 과도한 부하 유발 시 즉시 세션 차단',
    '   ✉  문의 시 ' + W + '학번 + 상황' + RS + '을 포함하여 관리자에게 전달',
    BC + '='*80 + RS,
]
open('/etc/motd', 'w').write('\n'.join(rows) + '\n')
PYEOF
RUN python3 /tmp/gen_motd.py && rm /tmp/gen_motd.py && chmod 644 /etc/motd

# 9. 진입 스크립트 작성 (HEREDOC 방식을 사용하여 Syntax Error 방지)
RUN cat <<'EOF' > /start.sh
#!/bin/bash
service ssh start

# MariaDB 실행 확인 및 대기
if ! pgrep -x "mariadbd" > /dev/null; then
    mariadbd --user=mysql --bind-address=0.0.0.0 --port=3306 --skip-name-resolve &
    sleep 5
fi

# 학생 계정 생성 및 비밀번호 설정
if ! id -u "$STUDENT_ID" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$STUDENT_ID"
fi
echo "$STUDENT_ID:$USER_PASS" | chpasswd

# 관리자 컨테이너에서는 omni 로그인 계정을 함께 유지
if [ "$STUDENT_ID" = "s0000000" ]; then
    if ! id -u "omni" >/dev/null 2>&1; then
        useradd -m -s /bin/bash "omni"
    fi
    echo "omni:$USER_PASS" | chpasswd
fi

# 컨테이너 내부 전체 sudo 권한 부여 (호스트와 격리된 환경이므로 안전)
usermod -aG sudo "$STUDENT_ID"
echo "$STUDENT_ID ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$STUDENT_ID"
chmod 440 "/etc/sudoers.d/$STUDENT_ID"

if [ "$STUDENT_ID" = "s0000000" ]; then
    usermod -aG sudo "omni"
    echo "omni ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/omni"
    chmod 440 "/etc/sudoers.d/omni"
fi

# docker.sock 이 마운트된 경우 현재 학생 계정을 해당 그룹에 포함
if [ -S /var/run/docker.sock ]; then
    SOCK_GID=$(stat -c %g /var/run/docker.sock)
    SOCK_GROUP=$(getent group "$SOCK_GID" | cut -d: -f1)
    if [ -z "$SOCK_GROUP" ]; then
        SOCK_GROUP=dockersock
        groupadd -for -g "$SOCK_GID" "$SOCK_GROUP"
    fi
    usermod -aG "$SOCK_GROUP" "$STUDENT_ID"
fi

# 앱 중복 실행 방지 런처: 이미 실행 중이면 재실행하지 않음
cat <<'RUNAPP_EOF' >/usr/local/bin/runapp-safe
#!/bin/bash
set -euo pipefail

user_name="$(id -un)"
home_dir="${HOME:-/home/$user_name}"
app_file="$home_dir/app.py"
log_dir="${APP_LOG_DIR:-/var/log/student-apps/$user_name}"

if [ ! -f "$app_file" ]; then
    echo "[runapp] app.py not found: $app_file"
    exit 1
fi

mkdir -p "$log_dir"

# 기존 실행 중인 app.py 프로세스가 있으면 종료 후 재시작
running_pids="$(pgrep -u "$user_name" -f 'python3 .*app.py' || true)"
if [ -n "$running_pids" ]; then
    echo "[runapp] 기존 프로세스 종료 중... (pid: $(echo "$running_pids" | tr '\n' ' ' | xargs))"
    echo "$running_pids" | xargs kill 2>/dev/null || true
    sleep 1
    echo "$running_pids" | xargs kill -9 2>/dev/null || true
    sleep 0.5
fi

cd "$home_dir"
nohup python3 app.py >> "$log_dir/app.log" 2>&1 < /dev/null &
new_pid=$!
sleep 0.5
if kill -0 $new_pid 2>/dev/null; then
    echo "[runapp] 시작됨 (pid: $new_pid)"
else
    echo "[runapp] 오류: 시작 실패. 로그 확인: $log_dir/app.log"
    exit 1
fi
RUNAPP_EOF
chmod +x /usr/local/bin/runapp-safe

# 앱 중복 실행 감시: 동일 사용자의 app.py 프로세스를 1개만 유지
cat <<'APP_GUARD_EOF' >/usr/local/bin/app-dup-guard
#!/bin/bash
set -euo pipefail

target_user="$1"
guard_log="/var/log/student-apps/$target_user/app_guard.log"

while true; do
    pids="$(pgrep -u "$target_user" -f 'python3 .*app.py' || true)"
    count="$(echo "$pids" | awk 'NF{c++} END{print c+0}')"

    if [ "$count" -gt 1 ]; then
        # 가장 새로운(높은 PID) 프로세스를 유지 - 수동 재시작 시 새 버전이 살아남도록
        keep_pid="$(echo "$pids" | sort -n | tail -n 1)"
        kill_pids="$(echo "$pids" | grep -v "^$keep_pid$" || true)"
        if [ -n "$kill_pids" ]; then
            while IFS= read -r pid; do
                [ -n "$pid" ] || continue
                kill "$pid" 2>/dev/null || true
            done <<< "$kill_pids"
            sleep 0.5
            while IFS= read -r pid; do
                [ -n "$pid" ] || continue
                kill -9 "$pid" 2>/dev/null || true
            done <<< "$kill_pids"
            echo "[$(date '+%F %T')] deduplicated app.py for $target_user (keep: $keep_pid, removed: $(echo "$kill_pids" | tr '\n' ' ' | xargs))" >> "$guard_log"
        fi
    fi

    sleep 2
done
APP_GUARD_EOF
chmod +x /usr/local/bin/app-dup-guard

# 학생 환경 설정 (.bashrc)
# Remote-SSH 비대화형 셸 출력 충돌 방지를 위해 MOTD는 인터랙티브 셸에서만 출력
sed -i '/cat \/etc\/motd/d' /home/$STUDENT_ID/.bashrc
sed -i '/shared\/NOTICE.txt/d' /home/$STUDENT_ID/.bashrc
sed -i '/alias runapp=/d' /home/$STUDENT_ID/.bashrc
grep -qxF '[[ $- == *i* ]] && clear && cat /etc/motd' /home/$STUDENT_ID/.bashrc || echo '[[ $- == *i* ]] && clear && cat /etc/motd' >> /home/$STUDENT_ID/.bashrc
grep -qxF '[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"' /home/$STUDENT_ID/.bashrc || echo '[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"' >> /home/$STUDENT_ID/.bashrc
grep -qxF "alias mysql='mysql -h 127.0.0.1 -u $STUDENT_ID -p'" /home/$STUDENT_ID/.bashrc || echo "alias mysql='mysql -h 127.0.0.1 -u $STUDENT_ID -p'" >> /home/$STUDENT_ID/.bashrc
grep -qxF 'cd "$HOME"' /home/$STUDENT_ID/.bashrc || echo 'cd "$HOME"' >> /home/$STUDENT_ID/.bashrc
grep -qxF 'export APP_LOG_DIR="/var/log/student-apps/$STUDENT_ID"' /home/$STUDENT_ID/.bashrc || echo 'export APP_LOG_DIR="/var/log/student-apps/$STUDENT_ID"' >> /home/$STUDENT_ID/.bashrc
grep -qxF 'alias runapp="/usr/local/bin/runapp-safe"' /home/$STUDENT_ID/.bashrc || echo 'alias runapp="/usr/local/bin/runapp-safe"' >> /home/$STUDENT_ID/.bashrc
grep -qxF "PS1='\\[\\e[01;32m\\]\\u@\\h\\[\\e[00m\\]:\\[\\e[01;34m\\]\\w\\[\\e[00m\\]\\$ '" /home/$STUDENT_ID/.bashrc || echo "PS1='\\[\\e[01;32m\\]\\u@\\h\\[\\e[00m\\]:\\[\\e[01;34m\\]\\w\\[\\e[00m\\]\\$ '" >> /home/$STUDENT_ID/.bashrc
# python3 app.py 실행 시 기존 프로세스 자동 종료 후 재시작
sed -i '/^python3()/,/^}/d' /home/$STUDENT_ID/.bashrc
cat >> /home/$STUDENT_ID/.bashrc <<'PYTHON3_FUNC_EOF'
python3() {
    if [ "$#" -eq 1 ] && [ "$1" = "app.py" ] || [ "$#" -eq 1 ] && [ "$1" = "$HOME/app.py" ]; then
        /usr/local/bin/runapp-safe
    else
        command python3 "$@"
    fi
}
PYTHON3_FUNC_EOF

if [ "$STUDENT_ID" = "s0000000" ]; then
    sed -i '/cat \/etc\/motd/d' /home/omni/.bashrc
    sed -i '/shared\/NOTICE.txt/d' /home/omni/.bashrc
    sed -i '/alias runapp=/d' /home/omni/.bashrc
    grep -qxF '[[ $- == *i* ]] && clear && cat /etc/motd' /home/omni/.bashrc || echo '[[ $- == *i* ]] && clear && cat /etc/motd' >> /home/omni/.bashrc
    grep -qxF '[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"' /home/omni/.bashrc || echo '[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"' >> /home/omni/.bashrc
    grep -qxF 'alias mysql="mysql -h 127.0.0.1 -u omni -p"' /home/omni/.bashrc || echo 'alias mysql="mysql -h 127.0.0.1 -u omni -p"' >> /home/omni/.bashrc
    grep -qxF 'cd "$HOME"' /home/omni/.bashrc || echo 'cd "$HOME"' >> /home/omni/.bashrc
    grep -qxF 'export APP_LOG_DIR="/var/log/student-apps/omni"' /home/omni/.bashrc || echo 'export APP_LOG_DIR="/var/log/student-apps/omni"' >> /home/omni/.bashrc
    grep -qxF 'alias runapp="/usr/local/bin/runapp-safe"' /home/omni/.bashrc || echo 'alias runapp="/usr/local/bin/runapp-safe"' >> /home/omni/.bashrc
    # python3 app.py 실행 시 기존 프로세스 자동 종료 후 재시작
    sed -i '/^python3()/,/^}/d' /home/omni/.bashrc
    cat >> /home/omni/.bashrc <<'PYTHON3_FUNC_EOF'
python3() {
    if [ "$#" -eq 1 ] && [ "$1" = "app.py" ] || [ "$#" -eq 1 ] && [ "$1" = "$HOME/app.py" ]; then
        /usr/local/bin/runapp-safe
    else
        command python3 "$@"
    fi
}
PYTHON3_FUNC_EOF
fi

# 로그인 셸에서도 .bashrc가 적용되도록 .profile 보장
touch /home/$STUDENT_ID/.profile
grep -qxF 'if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then' /home/$STUDENT_ID/.profile || cat <<'PROFILE_EOF' >> /home/$STUDENT_ID/.profile
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
PROFILE_EOF

if [ "$STUDENT_ID" = "s0000000" ]; then
touch /home/omni/.profile
grep -qxF 'if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then' /home/omni/.profile || cat <<'PROFILE_EOF' >> /home/omni/.profile
if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
    . "$HOME/.bashrc"
fi
PROFILE_EOF
fi

# 로그인 직후 기본 작업 경로를 학생 홈으로 보장
usermod -d "/home/$STUDENT_ID" "$STUDENT_ID"
chown -R "$STUDENT_ID":"$STUDENT_ID" "/home/$STUDENT_ID"

if [ "$STUDENT_ID" = "s0000000" ]; then
    usermod -d "/home/omni" "omni"
    chown -R "omni":"omni" "/home/omni"
fi

# 학생 홈 바깥 로그 디렉터리 준비
mkdir -p "/var/log/student-apps/$STUDENT_ID"
chown -R "$STUDENT_ID":"$STUDENT_ID" "/var/log/student-apps/$STUDENT_ID"
chmod 700 "/var/log/student-apps/$STUDENT_ID"

if [ "$STUDENT_ID" = "s0000000" ]; then
    mkdir -p "/var/log/student-apps/omni"
    chown -R "omni":"omni" "/var/log/student-apps/omni"
    chmod 700 "/var/log/student-apps/omni"

    # 관리자 계정에서도 공용 자료 폴더를 동일 경로(~/shared)로 사용
    if [ -d "/home/s0000000/shared" ]; then
        ln -sfn /home/s0000000/shared /home/omni/shared
        chown -h "omni":"omni" /home/omni/shared
    fi

    # omni CLI를 omni 계정 PATH에서 항상 실행 가능하도록 등록
    if [ -f "/home/s0000000/omni" ]; then
        chmod +x /home/s0000000/omni
        ln -sf /home/s0000000/omni /usr/local/bin/omni
    fi
fi

# VS Code 탐색기에서 실습과 무관한 잡파일 숨김 (shared/.venv는 유지)
mkdir -p "/home/$STUDENT_ID/.vscode"
cat <<'VSCODE_EOF' > "/home/$STUDENT_ID/.vscode/settings.json"
{
    "files.exclude": {
        "**/__pycache__": true,
        "**/.cache": true,
        "**/.copilot": true,
        "**/.dotnet": true,
        "**/.pm2": true,
        "**/.vscode": true,
        "**/.vscode-server": true,
        "**/.bash_history": true,
        "**/.bashrc": true,
        "**/.profile": true,
        "**/.mariadb_history": true,
        "**/.sudo_as_admin_successful": true,
        "**/.viminfo": true,
        "**/stderr.log": true,
        "**/stdout.log": true
    },
    "search.exclude": {
        "**/__pycache__": true,
        "**/.cache": true,
        "**/.copilot": true,
        "**/.dotnet": true,
        "**/.pm2": true,
        "**/.vscode-server": true
    }
}
VSCODE_EOF
chown -R "$STUDENT_ID":"$STUDENT_ID" "/home/$STUDENT_ID/.vscode"

if [ "$STUDENT_ID" = "s0000000" ]; then
        mkdir -p "/home/omni/.vscode"
        cp "/home/$STUDENT_ID/.vscode/settings.json" "/home/omni/.vscode/settings.json"
        chown -R "omni":"omni" "/home/omni/.vscode"
fi

# 사용자별 홈 디렉터리는 계정 기본값을 사용 (Remote-SSH/다중계정 호환)
sed -i '/^SetEnv HOME=/d' /etc/ssh/sshd_config
service ssh reload


# DB 권한 및 데이터베이스 생성
mysql -u root <<SQL_EOF
ALTER USER "root"@"localhost" IDENTIFIED BY "$DB_ROOT_PASS";
CREATE DATABASE IF NOT EXISTS student_db;
GRANT ALL PRIVILEGES ON *.* TO "$STUDENT_ID"@"%" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO "$STUDENT_ID"@"127.0.0.1" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO "$STUDENT_ID"@"localhost" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL_EOF

# 관리자 컨테이너(s0000000)에서는 omni DB 계정도 동일 비밀번호로 생성
if [ "$STUDENT_ID" = "s0000000" ]; then
mysql -u root -p"$DB_ROOT_PASS" <<SQL_OMNI_EOF
GRANT ALL PRIVILEGES ON *.* TO "omni"@"%" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO "omni"@"127.0.0.1" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO "omni"@"localhost" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL_OMNI_EOF
fi

# ttyd 웹터미널(7681) 실행: 학생 계정 비밀번호와 동일한 Basic Auth 사용
if command -v ttyd >/dev/null 2>&1; then
    pkill -x ttyd >/dev/null 2>&1 || true
    if [ "${TTYD_NO_AUTH:-0}" = "1" ]; then
        nohup ttyd -i 0.0.0.0 -p 7681 /bin/bash >/tmp/ttyd.log 2>&1 &
    else
        nohup ttyd -i 0.0.0.0 -p 7681 -c "$STUDENT_ID:$USER_PASS" /bin/bash >/tmp/ttyd.log 2>&1 &
    fi
fi

# 앱 중복 방지 가드를 백그라운드로 유지
pkill -f "app-dup-guard $STUDENT_ID" >/dev/null 2>&1 || true
nohup /usr/local/bin/app-dup-guard "$STUDENT_ID" >/dev/null 2>&1 &

# 학생 앱 자동 실행 (아직 실행 중이지 않은 경우에만, 학생 유저 권한으로)
APP_HOME="/home/$STUDENT_ID"
APP_LOG="/var/log/student-apps/$STUDENT_ID/app.log"
PYTHON3_BIN="$(which python3)"
mkdir -p "/var/log/student-apps/$STUDENT_ID"
if [ -f "$APP_HOME/app.py" ]; then
    if ! pgrep -u "$STUDENT_ID" -f 'python3 .*app.py' >/dev/null 2>&1; then
        start-stop-daemon --start --quiet --background \
            --chuid "$STUDENT_ID" --chdir "$APP_HOME" \
            --exec "$PYTHON3_BIN" -- "$APP_HOME/app.py" \
            >> "$APP_LOG" 2>&1 || true
    fi
fi

# 컨테이너 유지
tail -f /dev/null
EOF

RUN chmod +x /start.sh
CMD ["/start.sh"]
