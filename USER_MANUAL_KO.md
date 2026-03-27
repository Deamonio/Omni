# Omni 실습 서버 사용 매뉴얼

최종 업데이트: 2026-03-27

---

> 이 매뉴얼은 **학생용**과 **교수/관리자용** 섹션으로 구성되어 있습니다.
> - 학생은 1~8절을 참고하세요.
> - 교수/관리자는 9~13절을 추가로 참고하세요.

---

## 1. 개요
- 이 환경은 학번별로 분리된 컨테이너 실습 서버입니다.
- 학생 29명 각각이 독립된 컨테이너(Flask + MySQL + SSH)를 할당받습니다.
- 기본 작업 위치는 각 사용자 홈 디렉토리입니다.
- 공용 자료는 shared 디렉토리에서 읽기 전용으로 제공됩니다.

---

# 학생용

## 2. 접속 정보

### 2.1 학생 계정
- SSH 접속 형식
  ```
  ssh s학번@robotandi.deamon.io
  ```
- 웹 접속 형식
  ```
  https://학번.robotandi.deamon.io
  ```
- 초기 비밀번호는 배포 시 개별 안내된 값을 사용하세요.

## 3. 기본 작업 순서
1. 현재 위치 확인
   ```
   pwd
   ```
2. 홈 디렉토리로 이동
   ```
   cd ~
   ```
3. 일반 실행 (권장)
   ```
   python3 app.py
   ```
4. 브라우저에서 본인 주소 접속
   ```
   https://학번.robotandi.deamon.io
   ```

참고:
- 웹 앱 실행 가능합니다.
  ```
  runapp
  ```
- `runapp` 명령은 앱 로그를 홈 디렉토리 외부 경로에 저장하므로 권장합니다.

## 4. DB 사용
- 별칭으로 접속
  ```
  mysql
  ```
- 직접 접속(권장)
  ```
  mysql -u s학번 -p
  ```
- 본인 학번과 동일한 이름의 데이터베이스가 미리 생성되어 있습니다.

## 5. 공용 자료 사용
- 공용 자료 위치
  ```
  ~/shared
  ```
- 복사 예시
  ```
  cp ~/shared/파일명 ~/파일명
  ```

주의:
- `shared` 디렉토리는 읽기 전용입니다.
- 수정이 필요하면 반드시 홈 디렉토리로 복사 후 진행하세요.

## 6. 파일 보존/백업
- 중요한 결과물은 개인 PC에도 수시 백업하세요.
- 대시보드에서 학번별 홈 디렉토리 전체를 ZIP으로 다운로드할 수 있습니다.
  ```
  https://robotandi.deamon.io
  ```
  다운로드 시 본인 비밀번호(SSH 비밀번호와 동일)가 필요합니다.

## 7. 로그 정책
- 학생 홈 디렉토리에는 `app.log`가 생성되지 않도록 분리되어 있습니다.
- 앱 로그는 컨테이너 내부 별도 경로에 저장됩니다.
- 홈 디렉토리에서 로그 파일이 보이는 경우 운영자에게 알려주세요.

## 8. 자주 발생하는 문제

### 8.1 SSH 비밀번호 거부 (Permission denied)
확인 순서:
1. 계정명 오타 확인 — `s학번` 형식인지 확인 (예: `s2501125`)
2. 비밀번호 오타 / 키보드 입력 방식 확인
3. 반복 실패 시 교수/운영자에게 문의

전달하면 좋은 정보:
- 계정명
- 시도 시각
- 입력한 명령
- 오류 메시지 전체

### 8.2 웹이 안 열릴 때
확인 순서:
1. 앱 실행 여부 확인
   ```
   ps -ef | grep app.py
   ```
2. 앱 재실행
   ```
   runapp
   ```
3. 주소 오타 확인
   ```
   https://학번.robotandi.deamon.io
   ```

### 8.3 DB 접속 실패
확인 순서:
1. 별칭 사용
   ```
   mysql
   ```
2. 직접 접속으로 재확인
   ```
   mysql -u s학번 -p
   ```
3. 비밀번호 확인 후 재시도

---

# 교수/관리자용

## 9. 관리자 계정 및 접속

### 9.1 관리자(omni) SSH 계정
- SSH 접속
  ```
  ssh omni@robotandi.deamon.io
  ```
- 계정 정보

  | 항목 | 값 |
  |------|----|
  | 계정명 | `omni` |
  | 비밀번호 | `rai1235` |
  | SSH 포트 | `20000` |
  | Web 포트 | `30000` |

- 관리자 계정은 SSHPiper를 통해 내부 관리 컨테이너(student29)로 자동 중계됩니다.
- `omni` 계정으로 접속하면 관리 컨테이너 내부 셸이 열립니다.
- 관리자 컨테이너에서는 MySQL 계정 `omni` 도 동일 비밀번호로 생성/동기화됩니다.

### 9.2 관리 대시보드 (웹)
- 접속 주소
  ```
  https://robotandi.deamon.io
  ```
- 기능
  - 학생 29명의 실습 서버 접속 상태 실시간 모니터링
  - 학번별 홈 디렉토리 ZIP 다운로드 (비밀번호 확인 후 제공)
  - 화면 자동 갱신 (2초 주기)

### 9.3 Nginx Proxy Manager (NPM) 관리 페이지
- 접속 주소 (서버 내 로컬)
  ```
  http://localhost:81
  ```
- 도메인별 SSL 인증서 관리, 프록시 호스트 추가/삭제를 담당합니다.

## 10. 컨테이너 관리

모든 명령은 서버에서 아래 경로로 이동한 뒤 실행합니다.

```
cd /home/rai/deamon/Omni
```

### 10.1 전체 컨테이너 제어

| 목적 | 명령 |
|------|------|
| 모든 컨테이너 상태 확인 | `docker compose ps` |
| 모든 컨테이너 시작 (백그라운드) | `docker compose up -d` |
| 모든 컨테이너 중지 및 제거 | `docker compose down` |
| 모든 컨테이너 재시작 | `docker compose restart` |
| 특정 학생 컨테이너만 재시작 | `docker compose restart student01` |
| 특정 컨테이너 로그 확인 (최근 50줄) | `docker logs student01 --tail=50` |
| 특정 컨테이너 실시간 로그 스트림 | `docker logs -f student01` |

> **주의**: `docker compose down` 은 컨테이너를 **삭제**합니다. 학생 파일은 `students/학번/` 폴더에 보존되지만, 실행 중인 작업은 모두 종료됩니다. 단순 재시작은 `restart`를 사용하세요.

### 10.2 컨테이너 내부 직접 접속

- 관리자 셸로 접속 (root 권한)
  ```
  docker exec -it student01 bash
  ```
- 특정 학생 계정으로 명령 실행 (학생 환경 그대로 재현)
  ```
  docker exec -it --user s2501125 student01 bash
  ```
- 단발성 명령 실행 (접속 없이)
  ```
  docker exec student01 sh -lc 'runapp'
  ```

> `--user` 옵션 없이 exec하면 root 계정으로 진입합니다. 학생 환경을 그대로 테스트하려면 반드시 `--user s학번` 을 붙이세요.

### 10.3 학생 계정 및 상태 확인

- 특정 학생 계정 존재 여부
  ```
  docker exec student01 id s2501125
  ```
- 특정 학생이 앱을 실행 중인지 확인
  ```
  docker exec student01 sh -c 'ps aux | grep app.py'
  ```
- 학생 홈 디렉토리 파일 목록
  ```
  docker exec student01 ls -la /home/s2501125/
  ```
- 학생 MySQL DB 접속 확인
  ```
  docker exec student01 mysql -u s2501125 -p비밀번호 -e 'show databases;'
  ```

### 10.4 컨테이너별 포트 구성

각 컨테이너는 학번 끝 4자리를 포트 번호 뒷자리로 사용합니다.

| 용도 | 호스트 포트 형식 | 예시 (학번 2501125, 끝 4자리 1125) |
|------|-----------------|------------------------------------|
| SSH  | `2XXXX`         | `21125`                            |
| Web (Flask 5000) | `3XXXX` | `31125`                      |
| MySQL (3306) | `4XXXX`  | `41125`                        |
| ttyd 웹터미널 (7681) | `5XXXX` | `51125`               |

- 특정 학생의 SSH 포트로 직접 접속 (테스트용)
  ```
  ssh -p 21125 s2501125@localhost
  ```

### 10.5 리소스 제한

- CPU: 컨테이너당 **0.5 코어**
- 메모리: 컨테이너당 **512MB**
- 변경이 필요하면 `docker-compose.yml` 의 `deploy.resources.limits` 항목을 수정 후 해당 컨테이너를 재시작합니다.
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
  ```
- 특정 컨테이너의 현재 리소스 사용량 실시간 확인
  ```
  docker stats student01 --no-stream
  ```
- 전체 컨테이너 리소스 사용량 한 번에 확인
  ```
  docker stats --no-stream
  ```

### 10.6 유지보수 스크립트

`scripts/` 폴더에 두 가지 유틸리티 스크립트가 있습니다.

**학생 홈의 app.log를 외부 경로로 이동**
```
# 실제 이동
bash scripts/move_student_app_logs.sh

# 이동 전 대상 파일 목록만 확인 (실행 안 함)
bash scripts/move_student_app_logs.sh --dry-run
```
- 학생 홈에 남아 있는 `app.log` 파일을 `student_logs/학번/app.log` 경로로 통합합니다.
- 이미 같은 경로에 파일이 있으면 내용이 **이어쓰기**됩니다.

**학생 홈의 기본 index.html 일괄 삭제**
```
# 실제 삭제
bash scripts/cleanup_student_indexes.sh

# 삭제 대상 목록만 확인 (실행 안 함)
bash scripts/cleanup_student_indexes.sh --dry-run
```
- 학생들이 아직 수정하지 않은 기본 `index.html` 파일을 정리할 때 사용합니다.
- 실수를 방지하려면 반드시 `--dry-run` 으로 먼저 확인하세요.

### 10.7 omni 관리자 CLI 명령어 (중요)

`omni` 계정으로 SSH 접속하면 아래 명령을 바로 사용할 수 있습니다.

```
omni --help
```

지원 명령:

| 명령 | 설명 | 예시 |
|------|------|------|
| `omni list` | 전체 슬롯(학생+관리자) 목록/상태 조회 | `omni list` |
| `omni ps` | student 컨테이너 실행 상태 조회 | `omni ps` |
| `omni create <name> <s학번> <password>` | 새 슬롯 추가 + 컨테이너/도메인/파이프 자동 생성 | `omni create 홍길동 s2601001 pass1234` |
| `omni assign <slot> <name> <s학번> <password>` | 기존 슬롯을 다른 학생 정보로 재할당 | `omni assign 3 김학생 s2501999 newpass` |
| `omni id <slot\|학번\|s학번> <s학번>` | 대상 슬롯의 로그인 ID만 변경 | `omni id 3 s2501888` |
| `omni passwd <slot\|학번\|s학번> <newpass>` | 학생 비밀번호 변경 | `omni passwd s2501125 newpass` |
| `omni del <slot\|학번\|s학번>` | 슬롯 초기화(계정 정보 비우기) | `omni del 3` |
| `omni destroy <slot\|학번\|s학번>` | 슬롯 완전 삭제(컨테이너/파이프/학생폴더/도메인 삭제) | `omni destroy s2501888` |

`omni create`, `omni assign`, `omni id` 실행 시 자동 동기화 항목:
- `dashboard/students.json`
- `docker-compose.yml` (포트/환경변수/볼륨)
- `sshpiper/pipes/`
- NPM 프록시 도메인 + SSL
- 컨테이너 내부 DB 계정(MySQL 사용자/비밀번호)

`omni passwd` 실행 시 자동 반영 항목:
- Linux 로그인 비밀번호
- 컨테이너 내부 DB 계정 비밀번호(MySQL)

주의:
- 학생 로그인 ID는 반드시 `s` + 7자리 학번 형식이어야 합니다. (예: `s2501125`)
- `omni destroy`는 학생 홈 폴더까지 삭제하므로 실행 전 백업 여부를 반드시 확인하세요.
- 관리자 슬롯(29, `omni`)은 `assign/del/destroy` 대상이 아닙니다.

### 10.8 omni 명령 실패 사례와 해결 방법

아래 표는 운영 중 자주 만나는 오류를 기준으로 작성했습니다.

| 오류 메시지 예시 | 주된 원인 | 해결 방법 |
|------------------|-----------|-----------|
| `omni: command not found` | `omni` 실행 파일이 PATH에 없음 또는 student29 재기동 후 링크 누락 | `docker exec student29 ls -l /usr/local/bin/omni` 확인 후, 없으면 `docker compose up -d --force-recreate student29` 실행 |
| `학생 ID는 s학번 형식이어야 합니다` | `s2501125` 형식이 아닌 ID 입력 | `omni create/assign/id` 실행 시 반드시 `s` + 7자리 숫자 사용 |
| `이미 다른 슬롯에서 사용 중인 학번입니다` | 같은 학번을 다른 슬롯에서 이미 사용 중 | 먼저 `omni list`로 기존 슬롯 확인 후, 기존 슬롯 `omni del` 또는 `omni destroy` 후 재시도 |
| `포트 충돌이 발생합니다` | 학번 끝 4자리 기반 포트(`2/3/4/5XXXX`)가 기존 서비스와 충돌 | 충돌 학번을 변경하거나 기존 충돌 슬롯 정리 후 다시 실행 |
| `관리자 슬롯(29)은 assign 대상이 아닙니다` | slot 29에 `assign/id/del/destroy` 실행 | 관리자 슬롯은 고정 슬롯이므로 학생 슬롯(1~28)만 대상으로 작업 |
| `학생을 찾을 수 없습니다` | slot/학번/s학번 식별자가 잘못됨 | `omni list`에서 정확한 slot/ID 확인 후 재입력 |
| `NPM 동기화 건너뜀: ...` | NPM 토큰 발급 실패 또는 NPM 접근 불가 | `NPM_PASS` 환경변수 확인 후 다시 실행. 임시로는 NPM UI(`http://localhost:81`)에서 수동 반영 |
| `compose 파일이 없습니다: /omni_root/docker-compose.yml` | student29에 `/omni_root` 마운트 누락 | `docker-compose.yml`의 `student29` 볼륨에 `./:/omni_root`가 있는지 확인 후 재생성 |
| `Cannot connect to the Docker daemon ...` | `docker.sock` 미마운트 또는 권한 문제 | `student29` 볼륨에 `/var/run/docker.sock:/var/run/docker.sock` 추가, `docker compose up -d --force-recreate student29` 실행 |

빠른 점검 명령:
```bash
# 1) omni 실행 파일 확인
docker exec student29 ls -l /usr/local/bin/omni

# 2) 필수 마운트 확인
docker exec student29 sh -lc 'ls -ld /omni_root /dashboard_data /sshpiper_pipes /var/run/docker.sock'

# 3) 명령 정상 동작 확인
docker exec -u omni student29 omni list | head -10
```

## 11. 공용 자료 배포 (shared 폴더)

### 11.1 구조 및 동작 원리

- 호스트 경로
  ```
  /home/rai/deamon/Omni/shared/
  ```
- 이 경로는 모든 학생 컨테이너에 `~/shared` 로 **읽기 전용(ro)** 으로 마운트됩니다.
- 파일을 추가하거나 수정하면 **컨테이너 재시작 없이** 즉시 모든 학생에게 반영됩니다.
- 학생은 이 폴더에서 **읽기와 복사만** 가능합니다. 쓰기/삭제는 불가합니다.

### 11.2 실습 자료 배포

**파일 1개 업로드**
```
cp /내PC에서가져온파일.zip /home/rai/deamon/Omni/shared/
```

**여러 파일을 한 번에 업로드 (scp로 외부에서 전송 시)**
```
scp -r 로컬경로/* 서버계정@서버주소:/home/rai/deamon/Omni/shared/
```

**현재 shared에 있는 파일 목록 확인**
```
ls -lh /home/rai/deamon/Omni/shared/
```

**파일 삭제 (학생에게 즉시 사라짐)**
```
rm /home/rai/deamon/Omni/shared/이전자료.zip
```

> 학생 입장에서는 SSH 접속 후 `ls ~/shared` 로 목록을 확인하고, `cp ~/shared/파일명 ~/` 으로 홈에 복사해서 사용합니다.

### 11.3 공지사항 (NOTICE.txt) 관리

`shared/NOTICE.txt` 는 학생이 SSH로 로그인할 때 바로 볼 수 있는 공지사항 파일입니다.

**공지 내용 수정**
```
nano /home/rai/deamon/Omni/shared/NOTICE.txt
```
수정 후 저장(`Ctrl+O` → `Enter`) 하고 종료(`Ctrl+X`)합니다.  
저장 즉시 모든 학생의 `~/shared/NOTICE.txt` 에 반영됩니다.

공지사항 파일은 관리자 계정에서도 직접 확인할 수 있습니다.

**현재 공지 내용 확인**
```
cat /home/rai/deamon/Omni/shared/NOTICE.txt
```

**공지 내용 예시 (형식 참고)**
```
============================================================
 [ROBOT & AI] 실습 공지
============================================================

오늘 실습 주제: Flask + MySQL 연동

[과제 안내]
- ~/shared/lab03.zip 파일을 홈에 복사 후 진행하세요.
  cp ~/shared/lab03.zip ~/
  cd ~ && unzip lab03.zip

[제출 방법]
- 완성된 app.py를 홈 디렉토리에 저장하면 됩니다.
- 대시보드(https://robotandi.deamon.io)에서 다운로드 가능합니다.

============================================================
```

> NOTICE.txt 는 학생이 직접 확인하는 파일입니다. 중요한 안내는 이 파일에 명확하게 작성하세요.

## 12. 학생 파일 수거

### 12.1 대시보드를 통한 다운로드 (권장)

1. `https://robotandi.deamon.io` 접속
2. 학생 목록에서 수거할 학생의 **다운로드** 버튼 클릭
3. 해당 학생의 비밀번호 입력 (SSH 비밀번호와 동일)
4. 확인 후 홈 디렉토리 전체가 ZIP 파일로 자동 다운로드됨

> 파일명 형식: `s학번_home_YYYYMMDD_HHMMSS.zip`  
> ZIP 내부 구조는 학생 홈 디렉토리(`/home/s학번/`) 하위 구조 그대로입니다.

### 12.2 명령줄을 통한 직접 수거

**특정 학생 1명 수거**
```bash
# 수거 폴더 생성 후 압축 추출
mkdir -p ./수거/2501125
docker exec student01 tar -cf - -C /home/s2501125 . \
  | tar -xf - -C ./수거/2501125/
```

**전체 학생 일괄 수거 (스크립트 예시)**
```bash
# /home/rai/deamon/Omni 에서 실행
mkdir -p ./수거_$(date +%Y%m%d)

for cid in $(seq -f "%02g" 1 29); do
  container="student${cid}"
  # 컨테이너에서 STUDENT_ID 환경변수 읽기
  uid=$(docker exec $container sh -c 'echo $STUDENT_ID' 2>/dev/null)
  if [[ -z "$uid" ]]; then continue; fi
  outdir="./수거_$(date +%Y%m%d)/${uid#s}"
  mkdir -p "$outdir"
  docker exec "$container" tar -cf - -C /home/$uid . | tar -xf - -C "$outdir/"
  echo "수거 완료: $uid -> $outdir"
done
```

**학생 로그(app.log) 수거**
```bash
# student_logs/ 폴더에 컨테이너별 앱 로그가 저장되어 있음
ls /home/rai/deamon/Omni/student_logs/

# 특정 학생 로그 확인
cat /home/rai/deamon/Omni/student_logs/2501125/app.log
```

## 13. 점검 및 트러블슈팅

### 13.1 정기 점검 체크리스트

- [ ] 전체 컨테이너 실행 상태 확인
  ```
  cd /home/rai/deamon/Omni && docker compose ps
  ```
  → 모든 컨테이너 `Status`가 `Up`이어야 합니다. `Exited` 가 있으면 해당 컨테이너 재시작 필요.

- [ ] 대시보드 접속 및 학생 상태 확인
  ```
  https://robotandi.deamon.io
  ```
  → 실습 중인 학생은 초록 점(🟢), 오프라인은 흰 점(⚪)으로 표시됩니다.

- [ ] omni 계정 SSH 접속 테스트
  ```
  ssh omni@robotandi.deamon.io
  ```

- [ ] shared 파일 정상 마운트 여부
  ```
  docker exec student01 ls ~/shared/
  ```

- [ ] 학생 홈에 app.log 미노출 여부
  ```
  docker exec student01 sh -c 'ls /home/s2501125/' | grep app.log
  ```
  → 출력이 없어야 정상. 있으면 아래 로그 이동 스크립트를 실행하세요.
  ```
  bash /home/rai/deamon/Omni/scripts/move_student_app_logs.sh
  ```

- [ ] runapp 별칭 정상 동작 여부
  ```
  docker exec student01 sh -lc 'alias | grep runapp'
  ```

### 13.2 컨테이너 재생성 후 필수 확인

1. omni 계정 존재 여부 (student29 컨테이너)
   ```
   docker exec student29 id omni
   ```
2. SSHPiper 중계 경로 확인
   ```
   ls -la /home/rai/deamon/Omni/sshpiper/pipes/omni/
   ```
   → `sshd_config` 또는 `authorized_keys` 파일이 있어야 하며, 중계 대상이 `student29:22`인지 확인
3. 각 학생 계정 정상 생성 여부 (1~3번 대표 확인)
   ```
   docker exec student01 id s2501125
   docker exec student02 id s2501111
   docker exec student03 id s2201901
   ```
4. 전체 컨테이너 상태 한 번에 확인
   ```
   docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'
   ```

### 13.3 자주 발생하는 관리자 문제

---

**omni SSH 접속 불가**

원인 1) SSHPiper 컨테이너 미실행
```
docker compose ps | grep piper
```
→ `sshpiper` 컨테이너가 `Up` 상태인지 확인. 아니면 재시작:
```
docker compose restart sshpiper
```

원인 2) omni 파이프 설정 파일 문제
```
ls -la /home/rai/deamon/Omni/sshpiper/pipes/omni/
```
→ `authorized_keys` 파일 권한이 600이어야 합니다.
```
chmod 600 /home/rai/deamon/Omni/sshpiper/pipes/omni/authorized_keys
```

---

**특정 학생 컨테이너 응답 없음**

```
# 1. 상태 확인
docker compose ps student01

# 2. 최근 로그 확인
docker logs student01 --tail=50

# 3. 재시작
docker compose restart student01

# 4. 재시작 후 프로세스 확인
docker exec student01 ps aux
```

---

**대시보드 접속 불가**

```
# 대시보드 컨테이너 상태 확인
docker compose ps | grep dashboard

# 대시보드 로그 확인
docker logs dashboard --tail=50

# 재시작
docker compose restart dashboard
```

---

**학생이 DB에 접속 못함**

해당 학생 컨테이너에서 MySQL 프로세스 확인:
```
docker exec student01 sh -c 'ps aux | grep mysql'
```
→ mysqld 프로세스가 없으면 컨테이너 재시작:
```
docker compose restart student01
```

---

**학생 홈에 파일이 사라졌다고 함**

```
# 호스트에서 직접 학생 폴더 확인
ls -la /home/rai/deamon/Omni/students/2501125/
```
→ 학생 파일은 호스트 볼륨에 저장되므로 컨테이너 재시작/삭제 후에도 유지됩니다.  
  파일이 없으면 직접 백업에서 복구해야 합니다.

---

## 14. 보안/운영 수칙

**공통**
- 타인의 환경 접근 시도 금지
- 과도한 부하 유발 작업 금지
- 계정 정보는 개인별로만 관리

**관리자**
- 관리자 비밀번호(omni)는 외부에 노출하지 않도록 주의하세요.
- SSH 접속 기록 및 비정상 접근은 탐지/차단됩니다.
- docker-compose.yml 및 accounts 파일은 접근 권한을 제한하여 관리하세요.

---

## 15. 문의 템플릿
아래 형식으로 전달하면 처리 속도가 빨라집니다.

```
학번(또는 계정):
발생 시각:
실행 명령:
오류 메시지:
재현 여부:
```
