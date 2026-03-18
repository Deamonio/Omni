# 1. 베이스 이미지
FROM python:3.11-slim

# 2. 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    openssh-server default-mysql-server vim procps curl gnupg locales \
    docker.io libjson-c-dev libwebsockets-dev cmake g++ pkg-config git \
    && rm -rf /var/lib/apt/lists/*

# 3. ttyd 바이너리 직접 설치 (Debian 패키지 부재 해결)
RUN curl -LO https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 && \
    chmod +x ttyd.x86_64 && \
    mv ttyd.x86_64 /usr/bin/ttyd

# 4. Node.js & PM2 설치
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && npm install pm2 -g

# 5. 로케일 설정
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# 6. Python 라이브러리 (필요 패키지 통합 설치)
RUN pip install --no-cache-dir flask flask-socketio eventlet pymysql flask-sqlalchemy

# 7. SSH 및 시스템 설정
RUN mkdir -p /var/run/sshd /run/mysqld && \
    chown -R mysql:mysql /run/mysqld /var/lib/mysql && \
    sed -i 's/#PrintMotd yes/PrintMotd yes/' /etc/ssh/sshd_config && \
    sed -i 's/session    optional     pam_motd.so/session    optional     pam_motd.so/' /etc/pam.d/sshd && \
    echo "session    required     pam_unix.so" >> /etc/pam.d/sshd && \
    echo "session    optional     pam_loginuid.so" >> /etc/pam.d/sshd

WORKDIR /var/www/html

# 8. Kyungbok ASCII ART (MOTD)
# 'EOF' 방식을 사용하여 백슬래시(\) 등 특수 문자 에러를 원천 차단합니다.
RUN cat <<'EOF' > /etc/motd
================================================================================
   _  __                                _                 _
  | |/ / _   _  _   _  _ __    __ _  | |__    ___   | | __
  | ' / | | | || | | || '_ \  / _` | | '_ \  / _ \  | |/ /
  | . \ | |_| || |_| || | | || (_| | | |_) || (_) | | <
  |_|\_\ \__, | \__,_||_| |_| \__, | |_.__/  \___/  |_|\_\
         |___/                |___/
  --------------------------------------------------------------------------
   경복대학교 소프트웨어융합학과 [SQL 활용] 실습 서버
   지도교수: 고철영 교수님
  --------------------------------------------------------------------------
   Welcome! 본 서버는 실습을 위해 독립적으로 할당된 가상 환경입니다.
   Managed by Deamon.io
================================================================================
EOF
RUN chmod 644 /etc/motd

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

# 학생 환경 설정 (.bashrc)
echo "clear && cat /etc/motd" >> /home/$STUDENT_ID/.bashrc
echo "cd /var/www/html" >> /home/$STUDENT_ID/.bashrc
echo "alias mysql='mysql -h 127.0.0.1 -u $STUDENT_ID -p'" >> /home/$STUDENT_ID/.bashrc

# DB 권한 및 데이터베이스 생성
mysql -u root <<SQL_EOF
ALTER USER "root"@"localhost" IDENTIFIED BY "$DB_ROOT_PASS";
CREATE DATABASE IF NOT EXISTS student_db;
GRANT ALL PRIVILEGES ON *.* TO "$STUDENT_ID"@"%" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO "$STUDENT_ID"@"127.0.0.1" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO "$STUDENT_ID"@"localhost" IDENTIFIED BY "$USER_PASS" WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL_EOF

chown -R "$STUDENT_ID":"$STUDENT_ID" /var/www/html

# Web Terminal 실행 (커스텀 로그인을 사용하므로 자체 인증 제거)
/usr/bin/ttyd -p 7681 -t disableLeaveAlert=true login &

# 컨테이너 유지
tail -f /dev/null
EOF

RUN chmod +x /start.sh
CMD ["/start.sh"]
