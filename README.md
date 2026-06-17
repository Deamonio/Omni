# Omni 실습 인프라 운영 저장소

Omni는 학번별 Docker 컨테이너를 기반으로 Flask + MariaDB + SSH 실습 환경을 제공하는 운영 저장소입니다.
이 저장소는 다음을 한 번에 관리합니다.

- 학생별 컨테이너 오케스트레이션 (29명)
- 학생 웹 앱 배포 경로와 공용 자료 마운트
- SSH 중계 및 접속 정책
- 도메인 프록시 및 SSL 자동화 스크립트
- 상태 점검/복구/검증 자동화 스크립트
- 대시보드 기반 모니터링 및 백업 다운로드

## 1. 저장소 목적

이 프로젝트의 핵심 목적은 "수업용 실습 환경을 짧은 시간에 안정적으로 배포/복구/검증"하는 것입니다.
단순 앱 코드 저장소가 아니라 운영형 인프라 저장소 성격이 강합니다.

## 2. 주요 구성

### 상위 디렉터리

- `docker-compose.yml`: 학생 컨테이너 전체 정의
- `Dockerfile`: 공통 베이스 이미지(SSH, MariaDB, Node/PM2, Python 런타임)
- `students/`: 학생별 홈 디렉터리 바인드 마운트 대상
- `student_logs/`: 학생 앱 운영 로그 저장
- `shared/`: 공용 배포 자료(읽기 전용 마운트)
- `dashboard/`: 관리자 대시보드 앱
- `npm/`: Nginx Proxy Manager 데이터 및 인증서 관련 파일
- `sshpiper/`: SSH 중계(파이프) 관련 설정
- 운영 스크립트: `healthcheck.py`, `check_students.py`, `verify_students.py` 등

### 학생 컨테이너 특성

- 서비스명: `student01` ~ `student29`
- 컨테이너 내부 기본 구성: SSH(22), Flask(5000), MariaDB(3306)
- 학생 홈 디렉터리: `/home/s학번`
- 공용 자료: `/home/s학번/shared` (읽기 전용)

## 3. 빠른 시작

### 3.1 요구 사항

- Linux 호스트
- Docker / Docker Compose 사용 가능 상태
- 도메인 및 DNS 권한(프록시/SSL 운영 시)

### 3.2 최초 실행

```bash
cd /home/rai/deamon/Omni
docker compose build
docker compose up -d
docker compose ps
```

### 3.3 재배포/재시작

```bash
cd /home/rai/deamon/Omni
docker compose up -d --force-recreate
```

충돌 또는 이름 꼬임이 있으면 아래 순서를 사용합니다.

```bash
cd /home/rai/deamon/Omni
docker compose down
docker compose up -d
```

## 4. 운영 스크립트

### 핵심 점검

- `healthcheck.py`: 전체 학생 서비스 종합 헬스체크
  - SSH 포트/로그인
  - 웹 포트 및 내부 5000 응답
  - DB 포트 및 내부 계정 접속

예시:

```bash
cd /home/rai/deamon/Omni
python3 healthcheck.py --once
```

### 계정/상태 확인

- `check_students.py`, `check_students.sh`
- `verify_students.py`
- `scan_students.sh`

### 복구/보정

- `fix_script.sh`
- `fix_and_scan.sh`
- `full_reset.sh`

### 부가 자동화

- `npm_register.py`: NPM 프록시 호스트 자동 등록
- `npm_ssl.py`: NPM SSL 자동 발급/연결
- `generator.py`: 학생 구성 생성/갱신 계열 자동화(운영 절차에 맞춰 사용)

## 5. 대시보드

`dashboard/` 디렉터리의 앱은 운영자가 다음을 수행할 때 사용합니다.

- 학생별 상태 시각 확인
- 학번별 다운로드/아카이브 제공
- 실시간 운영 모니터링

## 6. 프록시/SSL 운영

Nginx Proxy Manager 설정/자동화는 아래 문서를 기준으로 진행합니다.

- `NPM_SETUP_GUIDE.md`
- `npm_register.py`
- `npm_ssl.py`

학생 주소 체계는 일반적으로 아래 형태를 사용합니다.

- `https://학번.rai.cortie.io`

## 7. 사용자 매뉴얼

- 학생/관리자 실사용 절차: `USER_MANUAL_KO.md`
- 주소/가입 흐름 안내: `ADDRESS_SIGNUP_MANUAL_KO.md`

## 8. 문제 해결 가이드

### 웹이 비정상 응답일 때

1. 컨테이너 상태 확인
2. 학생 앱 프로세스 확인
3. 학생 홈의 `app.py` 문법 확인
4. 필요 시 컨테이너 재시작 후 앱 재기동

권장 점검:

```bash
cd /home/rai/deamon/Omni
docker compose ps
python3 healthcheck.py --once
```

### SSH가 전원 실패할 때

- 호스트의 sshpiper 상태/포트 22 바인딩 여부를 우선 점검
- 파이프 설정(`sshpiper/pipes/`) 유효성 확인

### DB 접속 실패 시

- 컨테이너 내부 MariaDB 프로세스 유무 확인
- 학생 계정/권한 상태 확인
- 필요 시 해당 서비스 재시작

## 9. 로그 및 데이터 관리 정책

운영 산출물(로그/캐시/가상환경)은 저장소 용량과 원격 푸시 제한을 쉽게 초과합니다.
GitHub 업로드 실패를 방지하려면 아래 경로를 버전 관리에서 제외해야 합니다.

- `.venv/`, `**/.venv/`
- `**/.pm2/`
- `**/.cache/`
- `**/.vscode/`
- `**/.dotnet/`
- `**/__pycache__/`, `**/*.pyc`
- `student_logs/`
- `npm/data/logs/`

현재 `.gitignore`에 반영되어 있으며, 대용량 로그가 재추가되지 않도록 주의합니다.

## 10. 보안 주의 사항

- 비밀번호/토큰/키는 문서나 코드에 하드코딩하지 않습니다.
- 계정 정보는 `.mail_env` 또는 별도 보안 채널로 관리합니다.
- 외부 공유 시 `students/`, `student_logs/`, `npm/` 내부 민감 데이터를 반드시 점검합니다.

## 11. 권장 운영 순서(요약)

1. `docker compose ps`로 전체 상태 확인
2. `python3 healthcheck.py --once` 실행
3. 실패 서비스만 선별 복구
4. 필요 시 NPM 프록시/SSL 재동기화
5. 대시보드에서 최종 사용자 관점 검증

## 12. 기여/변경 반영

### 변경 반영 절차

```bash
cd /home/rai/deamon/Omni
git status
git add -A
git commit -m "chore: update ops docs or scripts"
git push origin master
```

### 커밋 전 체크

- 대용량 파일 포함 여부
- 런타임 산출물 포함 여부
- 민감 정보 포함 여부

## 13. 참고 문서

- `USER_MANUAL_KO.md`
- `ADDRESS_SIGNUP_MANUAL_KO.md`
- `NPM_SETUP_GUIDE.md`
- `docker-compose.yml`
- `Dockerfile`

---

문의/운영 이슈 대응 시에는 증상, 발생 시각, 대상 학번(또는 서비스명), 재현 명령을 함께 기록하면 복구 속도가 빨라집니다.
