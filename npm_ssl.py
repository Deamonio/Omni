#!/usr/bin/env python3
"""
기존 NPM 프록시 호스트에 Let's Encrypt SSL 자동 발급
- 이미 등록된 {학번}.robotandi.deamon.io 29개에 SSL 적용
- HTTP-01 Challenge 방식 (DNS 이전 불필요)
- Le't Encrypt rate limit 대비 호스트당 5초 간격
"""
import requests, getpass, sys, time, os

NPM_URL = "http://localhost:81"
NPM_EMAIL = "hyun0810d@gmail.com"
DOMAIN_SUFFIX = "robotandi.deamon.io"

def get_token(password):
    r = requests.post(f"{NPM_URL}/api/tokens", json={
        "identity": NPM_EMAIL, "secret": password
    })
    r.raise_for_status()
    return r.json()["token"]

def get_all_proxy_hosts(headers):
    r = requests.get(f"{NPM_URL}/api/nginx/proxy-hosts", headers=headers)
    r.raise_for_status()
    return r.json()

def enable_ssl(headers, host):
    host_id = host["id"]
    domain = host["domain_names"][0]

    payload = {
        "domain_names":         host["domain_names"],
        "forward_scheme":       host["forward_scheme"],
        "forward_host":         host["forward_host"],
        "forward_port":         host["forward_port"],
        "access_list_id":       host.get("access_list_id", 0),
        "certificate_id":       "new",
        "ssl_forced":           1,
        "http2_support":        1,
        "block_exploits":       host.get("block_exploits", 0),
        "caching_enabled":      host.get("caching_enabled", 0),
        "allow_websocket_upgrade": host.get("allow_websocket_upgrade", 1),
        "meta": {
            "letsencrypt_agree": True,
            "dns_challenge": False
        }
    }
    r = requests.put(f"{NPM_URL}/api/nginx/proxy-hosts/{host_id}",
                     headers=headers, json=payload)
    return r

def main():
    print("NPM SSL 자동 발급 스크립트")
    print(f"대상: *.{DOMAIN_SUFFIX} (학생 도메인만)\n")

    password = os.environ.get("NPM_PASS") or getpass.getpass("NPM 비밀번호: ")
    try:
        token = get_token(password)
    except Exception as e:
        print(f"로그인 실패: {e}")
        sys.exit(1)
    print("토큰 발급 성공\n")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    hosts = get_all_proxy_hosts(headers)

    # 학생 도메인만 필터 (이미 SSL 없는 것)
    targets = []
    for h in hosts:
        domains = h.get("domain_names", [])
        if not domains:
            continue
        d = domains[0]
        # 학번 패턴: 숫자7자리.robotandi.deamon.io, 아직 SSL 없는 것
        if d.endswith(f".{DOMAIN_SUFFIX}") and h.get("certificate_id", 0) == 0:
            targets.append(h)

    print(f"SSL 미적용 학생 도메인: {len(targets)}개\n")
    if not targets:
        print("모두 이미 SSL 적용됨.")
        return

    ok, fail = 0, 0
    for i, host in enumerate(targets, 1):
        domain = host["domain_names"][0]
        print(f"[{i:02d}/{len(targets)}] {domain} ... ", end="", flush=True)

        r = enable_ssl(headers, host)
        if r.status_code == 200:
            print("OK ✓")
            ok += 1
        else:
            err = r.json().get("error", {}).get("message", r.text[:60])
            print(f"FAIL - {err}")
            fail += 1

        # Let's Encrypt rate limit 방지 (마지막 항목 제외)
        if i < len(targets):
            time.sleep(5)

    print(f"\n완료: 성공 {ok}개 / 실패 {fail}개")
    if ok > 0:
        print(f"\n접속 예시 (HTTPS):")
        for h in targets[:3]:
            print(f"  https://{h['domain_names'][0]}")

if __name__ == "__main__":
    main()
