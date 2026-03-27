# NPM (Nginx Proxy Manager) 자동 설정 가이드

> **작성일**: 2026년 3월 26일  
> **목적**: 학생 29명의 프록시 호스트 + HTTPS SSL 자동 등록  
> **소요 시간**: ~50분 (DNS 전파 포함)

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [NPM 로그인 및 토큰 발급](#npm-로그인-및-토큰-발급)
3. [DNS 설정 (Spaceship)](#dns-설정-spaceship)
4. [프록시 호스트 자동 등록](#프록시-호스트-자동-등록)
5. [SSL 인증서 자동 발급](#ssl-인증서-자동-발급)
6. [검증 및 접속 테스트](#검증-및-접속-테스트)
7. [유지보수](#유지보수)

---

## 사전 요구사항

### 인프라
- Docker & Docker Compose 실행 중
- 학생 컨테이너 29개 실행 중
  - 포트: SSH 2xxxx, Web 3xxxx
  - 예: `student01` → SSH 21125, Web 31125

### NPM 정보
- **NPM 관리 페이지**: `http://localhost:81`
- **NPM DB 경로**: `./npm/data/database.sqlite`
- **계정 이메일**: `hyun0810d@gmail.com` (고정)
- **계정 비밀번호**: [NPM 관리 페이지에서 확인]

### 도메인 정보
- **메인 도메인**: `robotandi.deamon.io`
- **학생 도메인**: `{학번}.robotandi.deamon.io` (예: `2501125.robotandi.deamon.io`)
- **DNS 관제사**: Spaceship (네임서버: `launch1.spaceship.net`)

---

## NPM 로그인 및 토큰 발급

### 1단계: NPM 계정 이메일 확인

```bash
cd /home/rai/deamon/Omni
python3 -c "
import sqlite3
conn = sqlite3.connect('./npm/data/database.sqlite')
email = conn.execute('SELECT email FROM user').fetchone()[0]
print(f'NPM 계정: {email}')
conn.close()
"
```

**출력**: `NPM 계정: hyun0810d@gmail.com`

### 2단계: JWT 토큰 발급

```bash
read -s -p "NPM 비밀번호 입력: " PW && echo && \
curl -s -X POST http://localhost:81/api/tokens \
  -H "Content-Type: application/json" \
  -d '{"identity":"hyun0810d@gmail.com","secret":"'$PW'"}' \
  | python3 -m json.tool
```

**응답 예시:**
```json
{
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires": "2026-03-27T XX:XX:XX.XXXX"
}
```

💡 **팁**: 토큰은 발급일로부터 1일 유효. 필요시 재발급.

---

## DNS 설정 (Spaceship)

### 필요한 레코드

학생 서브도메인(`2501125.robotandi.deamon.io` 등)이 서버로 연결되려면 **와일드카드 CNAME**.

### Spaceship 관리 콘솔에서 수행

1. https://www.spaceship.com 로그인
2. `deamon.io` 도메인 관리
3. DNS 레코드 추가:

| 항목 | 값 |
|------|---|
| **Type** | CNAME |
| **Name/Host** | `*.robotandi` |
| **Target/Value** | `robotandi.ddns.net` |
| **TTL** | 300 (또는 기본값) |

4. 저장

### 전파 확인 (최대 30분)

```bash
# 전파된 IP 확인
dig +short 2501125.robotandi.deamon.io

# 출력 예시: 119.192.101.236
```

✅ **IP가 나올 때까지 다음 단계 진행 불가**

---

## 프록시 호스트 자동 등록

### 스크립트 확인

[npm_register.py](npm_register.py) 가 이미 생성되어 있음.

### 실행

```bash
cd /home/rai/deamon/Omni
python3 npm_register.py
```

**입력**: NPM 비밀번호

**출력 예시:**
```
NPM 프록시 호스트 자동 등록 [HTTP only]
대상: 29명 → {s_id}.robotandi.deamon.io

NPM 비밀번호: 
토큰 발급 성공

기존 등록된 도메인 2개 확인

  OK    2501125.robotandi.deamon.io -> student01:5000
  OK    2501111.robotandi.deamon.io -> student02:5000
  ...
  OK    0000000.robotandi.deamon.io -> student29:5000

완료: 등록 29개 / 스킵 0개 / 실패 0개
```

✅ **29개 모두 OK 나올 때까지 진행**

---

## SSL 인증서 자동 발급

### 사전 확인

**DNS 전파 검증** (필수)

```bash
dig +short 2501125.robotandi.deamon.io @8.8.8.8
# 출력: 119.192.101.236 (IP가 나와야 함)
```

### 스크립트 실행

[npm_ssl.py](npm_ssl.py) 가 이미 생성되어 있음.

```bash
cd /home/rai/deamon/Omni
python3 npm_ssl.py
```

**입력**: NPM 비밀번호

**처리 시간**: 호스트당 5초 × 29개 = ~2.5분

**출력 예시:**
```
NPM SSL 자동 발급 스크립트
대상: *.robotandi.deamon.io (학생 도메인만)

NPM 비밀번호: 
토큰 발급 성공

SSL 미적용 학생 도메인: 29개

[01/29] 0000000.robotandi.deamon.io ... OK ✓
[02/29] 2201130.robotandi.deamon.io ... OK ✓
...
[29/29] 2501076.robotandi.deamon.io ... OK ✓

완료: 성공 29개 / 실패 0개
```

✅ **29개 모두 OK 확인**

---

## 검증 및 접속 테스트

### 1단계: NPM DB 확인

```bash
python3 -c "
import sqlite3, json
conn = sqlite3.connect('./npm/data/database.sqlite')
rows = conn.execute('SELECT id, domain_names, certificate_id, ssl_forced FROM proxy_host ORDER BY id').fetchall()
ok = sum(1 for r in rows if r[2] and r[2] != 0)
total = len(rows)
print(f'SSL 발급 완료: {ok}/{total}')
for r in rows[:5]:
    cert = '✓ SSL' if (r[2] and r[2] != 0) else '✗ HTTP'
    print(f'  ID:{r[0]} {cert} {r[1]}')
print('  ...')
conn.close()
"
```

**예상 출력:**
```
SSL 발급 완료: 31/32
  ID:1 ✓ SSL ["robotandi.deamon.io"]
  ID:2 ✓ SSL ["admin.robotandi.deamon.io"]
  ID:3 ✗ HTTP ["*.robotandi.deamon.io"]
  ID:4 ✓ SSL ["2501125.robotandi.deamon.io"]
  ID:5 ✓ SSL ["2501111.robotandi.deamon.io"]
  ...
```

### 2단계: NPM 관리 페이지 확인

브라우저: `http://localhost:81`

1. 로그인
2. 좌측 메뉴 → **Proxy Hosts**
3. 학생 도메인 29개 + 와일드카드 목록 확인
4. 각각의 상태: **Online** ✓

### 3단계: 브라우저에서 접속 테스트

```
https://2501125.robotandi.deamon.io  (Baltukov Nomto)
https://2301104.robotandi.deamon.io  (김광호)
```

✅ **SSL 인증서 경고 없이 HTTPS 정상 로드**

---

## 유지보수

### 정기 점검 (월 1회 권장)

```bash
# 프록시 호스트 상태 확인
curl -s http://localhost:81/api/nginx/proxy-hosts \
  -H "Authorization: Bearer [TOKEN]" \
  | python3 -c "
import sys, json
hosts = json.load(sys.stdin)
online = sum(1 for h in hosts if h.get('meta', {}).get('nginx_online'))
print(f'온라인: {online}/{len(hosts)}')
"
```

### SSL 갱신 (자동)

- Let's Encrypt: 90일마다 자동 갱신
- 갱신 로그: `./npm/data/logs/letsencrypt.log*`
- 수동 갱신: NPM 관리 페이지 > Proxy Host > 우클릭 > Renew SSL

### 학생 추가 시

1. `docker-compose.yml`에 새 학생 컨테이너 추가
2. `./students/{학번}/` 폴더 생성
3. `python3 npm_register.py` 재실행 (기존 호스트는 스킵)
4. DNS 확인 후 `python3 npm_ssl.py` 재실행

### 문제 해결

#### 프록시 호스트 등록 실패

```bash
# 기존 호스트 목록 확인
sqlite3 ./npm/data/database.sqlite \
  "SELECT id, domain_names FROM proxy_host;"
```

#### SSL 발급 실패

```bash
# Let's Encrypt 로그 확인
cat ./npm/data/logs/letsencrypt.log.1 | tail -50
```

#### DNS 전파 확인

```bash
# Google DNS로 확인
dig +short {학번}.robotandi.deamon.io @8.8.8.8

# 권위 네임서버로 확인
dig +short {학번}.robotandi.deamon.io @launch1.spaceship.net
```

---

## 📁 생성된 파일

| 파일 | 목적 |
|------|------|
| `npm_register.py` | 프록시 호스트 자동 등록 (토큰 발급 후 29개 호스트 생성) |
| `npm_ssl.py` | SSL 자동 발급 (HTTP-01 Challenge, Let's Encrypt) |
| `NPM_SETUP_GUIDE.md` | 이 문서 |

---

## 🎯 최종 상태

| 항목 | 개수 | 상태 |
|------|------|------|
| 학생 컨테이너 | 29개 | ✅ 실행 중 |
| 프록시 호스트 | 29개 | ✅ 등록됨 |
| SSL 인증서 | 31개 | ✅ 발급됨 |
| DNS 레코드 | 1개 (와일드카드) | ✅ 설정됨 |

---

## 빠른 명령어 (재설정 시)

```bash
# 1. DNS 전파 확인
dig +short 2501125.robotandi.deamon.io @8.8.8.8

# 2. 프록시 호스트 등록
cd /home/rai/deamon/Omni
python3 npm_register.py

# 3. SSL 발급
python3 npm_ssl.py

# 4. 상태 확인
python3 -c "import sqlite3; conn=sqlite3.connect('./npm/data/database.sqlite'); rows=conn.execute('SELECT COUNT(*) FROM proxy_host WHERE certificate_id!=0').fetchone(); print(f'SSL 발급: {rows[0]}/29'); conn.close()"
```

---

## 🔒 호스트 서버 SSH 자동 터널링

### 목적

학생이 `ssh s2501125@robotandi.deamon.io` 로 접속하면 자동으로 해당 학번의 Docker 컨테이너 SSH 포트(`localhost:21125`)로 연결

### 설정 스크립트

[ssh_tunnel_setup.py](../ssh_tunnel_setup.py) - 이미 설정 완료됨

### 수행된 작업

- ✅ 학생 29명 SSH 계정 생성 (`s2501125`, `s2501111` 등)
- ✅ `/etc/ssh/sshd_config` 에 Match User 블록 29개 추가
- ✅ SSH 서비스 재시작
- ✅ 설정 백업: `/etc/ssh/sshd_config.backup.*`
- ✅ 각 학생 계정 비밀번호 = Docker 컨테이너 비밀번호 (final_accounts.txt 참조)

### 학생 접속 방법 (비밀번호)

```bash
# 일반적인 SSH 접속
ssh s2501125@robotandi.deamon.io

# 비밀번호 입력 (nomto)
Password: nomto
```

**자동 라우팅:**
```
ssh s2501125@robotandi.deamon.io → localhost:21125 (student01:SSH)
ssh s2501111@robotandi.deamon.io → localhost:21111 (student02:SSH)
ssh s2301104@robotandi.deamon.io → localhost:21104 (student07:SSH)
```

### sshd_config 설정 구조

```
Match User s2501125
    ForceCommand ssh -q -p 21125 -o StrictHostKeyChecking=no localhost
    X11Forwarding no
    AllowTcpForwarding yes
    PermitOpen localhost:21125
```

- **ForceCommand**: 항상 localhost:포트로 자동 연결
- **StrictHostKeyChecking=no**: 처음 접속 시 host key 확인 스킵
- **PermitOpen**: 특정 포트만 허용

### 복원 방법 (필요시)

```bash
sudo cp /etc/ssh/sshd_config.backup.TIMESTAMP /etc/ssh/sshd_config
sudo systemctl restart ssh
```

---

## 🔑 Docker 컨테이너 SSH Key 전송 (선택사항)

**목적**: 학생이 호스트 서버에 공개키 할당 후, Docker 컨테이너가 그 키를 인식하게 함.  
→ 호스트 `ssh s2501125@...` → 컨테이너 비밀번호 없이 자동 로그인 가능

### 1단계: 호스트에서 SSH 공개키 생성

```bash
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
# 출력: /home/rai/.ssh/id_rsa (이미 생성되었으면 스킵)
```

### 2단계: 각 학생 컨테이너로 공개키 복사

```bash
# 예시 1: student01 (학번 2501125, SSH 포트 21125)
ssh-copy-id -p 21003 s2501125@localhost

# 필요시 비밀번호 입력 (nomto)
```

**학생별 포트 대응:**
| 학번 | 컨테이너 | SSH 포트 | 명령어 |
|------|---------|---------|--------|
| 2501125 | student01 | 21125 | `ssh-copy-id -p 21125 s2501125@localhost` |
| 2501111 | student02 | 21111 | `ssh-copy-id -p 21111 s2501111@localhost` |
| 2301104 | student07 | 21104 | `ssh-copy-id -p 21104 s2301104@localhost` |

### 3단계: 자동 로그인 확인

```bash
ssh -p 21125 s2501125@localhost
# 비밀번호 입력 없이 바로 로그인되어야 함
```

### 일괄 처리 (모든 학생)

```bash
# 모든 29명에게 공개키 복사
while read line; do
    s_id=$(echo "$line" | grep -oP '(?<=ID: s)\d+')
    port=$(echo "$line" | grep -oP '(?<=SSH: )\d+')
    echo "Copying key to s$s_id (port $port)..."
    echo "[Password]" | sshpass -p "$(echo "$line" | grep -oP '(?<=PW: )\S+')" \
      ssh-copy-id -p "$port" "s$s_id@localhost"
done < final_accounts.txt
```

---

**최종 완성도**: 100% ✅
- Docker 컨테이너 29개 → SSH/Web 포트 자동 할당
- NPM 프록시 호스트 29개 → HTTPS 자동 생성
- SSH 자동 터널링 29개 → 학생이 도메인으로 직접 접속

---

**다음 단계** (필요시):
- SSL 갱신 자동화 (Let's Encrypt 90일 주기)
- 모니터링 대시보드 (학생 접속 통계)
- 자동 백업 스크립트
