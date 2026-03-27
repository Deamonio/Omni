#!/usr/bin/env python3
"""
NPM 프록시 호스트 자동 등록 스크립트
https://{s_id}.robotandi.deamon.io -> student{i:02d}:5000
"""
import requests, getpass, sys, time

NPM_URL = "http://localhost:81"
NPM_EMAIL = "hyun0810d@gmail.com"
DOMAIN_SUFFIX = "robotandi.deamon.io"

STUDENT_DATA = [
    ("Baltukov Nomto",              "2501125", "student01"),
    ("CONTRERAS RIVERA MAURO JEISON","2501111", "student02"),
    ("Dorzhieva Aiana",             "2201901", "student03"),
    ("UYANIK ILSU SUZAN",           "2501115", "student04"),
    ("강문성",                       "2301301", "student05"),
    ("강성우",                       "2501003", "student06"),
    ("김광호",                       "2301104", "student07"),
    ("김준석",                       "2201403", "student08"),
    ("김진형",                       "2301112", "student09"),
    ("김찬민",                       "2301113", "student10"),
    ("문초연",                       "2501080", "student11"),
    ("박성준",                       "2301206", "student12"),
    ("박준성",                       "2301306", "student13"),
    ("박지혜",                       "2501089", "student14"),
    ("배정환",                       "2501090", "student15"),
    ("석민재",                       "2301209", "student16"),
    ("신윤호",                       "2301123", "student17"),
    ("엄태영",                       "2501045", "student18"),
    ("이순주",                       "2301129", "student19"),
    ("이어진",                       "2501058", "student20"),
    ("이웅재",                       "2501059", "student21"),
    ("이현재",                       "2401061", "student22"),
    ("이희성",                       "2201130", "student23"),
    ("장한별",                       "2501092", "student24"),
    ("정구진",                       "2301136", "student25"),
    ("정서윤",                       "2501085", "student26"),
    ("최민혁",                       "2501073", "student27"),
    ("황연준",                       "2501076", "student28"),
    ("System Admin",                "0000000", "student29"),
]

def get_token(password):
    r = requests.post(f"{NPM_URL}/api/tokens", json={
        "identity": NPM_EMAIL,
        "secret": password
    })
    r.raise_for_status()
    return r.json()["token"]

def get_existing_domains(headers):
    r = requests.get(f"{NPM_URL}/api/nginx/proxy-hosts", headers=headers)
    r.raise_for_status()
    existing = set()
    for h in r.json():
        for d in h.get("domain_names", []):
            existing.add(d)
    return existing

def create_proxy_host(headers, domain, container_name, use_ssl=False):
    payload = {
        "domain_names": [domain],
        "forward_scheme": "http",
        "forward_host": container_name,
        "forward_port": 5000,
        "access_list_id": 0,
        "certificate_id": 0,
        "ssl_forced": 0,
        "http2_support": 0,
        "block_exploits": 0,
        "caching_enabled": 0,
        "allow_websocket_upgrade": 1,
        "meta": {
            "letsencrypt_agree": False,
            "dns_challenge": False
        }
    }
    if use_ssl:
        payload.update({
            "certificate_id": "new",
            "ssl_forced": 1,
            "http2_support": 1,
            "meta": {
                "letsencrypt_agree": True,
                "dns_challenge": False
            }
        })
    r = requests.post(f"{NPM_URL}/api/nginx/proxy-hosts", headers=headers, json=payload)
    return r

def main():
    use_ssl = "--ssl" in sys.argv
    print(f"NPM 프록시 호스트 자동 등록 {'[SSL 포함]' if use_ssl else '[HTTP only]'}")
    print(f"대상: {len(STUDENT_DATA)}명 → {{s_id}}.{DOMAIN_SUFFIX}\n")

    import os
    password = os.environ.get("NPM_PASS") or getpass.getpass("NPM 비밀번호: ")
    try:
        token = get_token(password)
    except Exception as e:
        print(f"로그인 실패: {e}")
        sys.exit(1)
    print("토큰 발급 성공\n")

    headers = {"Authorization": f"Bearer {token}"}
    existing = get_existing_domains(headers)
    print(f"기존 등록된 도메인 {len(existing)}개 확인\n")

    ok, skip, fail = 0, 0, 0
    for name, s_id, container in STUDENT_DATA:
        domain = f"{s_id}.{DOMAIN_SUFFIX}"
        if domain in existing:
            print(f"  SKIP  {domain} (이미 존재)")
            skip += 1
            continue

        r = create_proxy_host(headers, domain, container, use_ssl)
        if r.status_code == 201:
            print(f"  OK    {domain} -> {container}:5000")
            ok += 1
        else:
            print(f"  FAIL  {domain} [{r.status_code}] {r.text[:80]}")
            fail += 1

        if use_ssl:
            time.sleep(3)  # Let's Encrypt rate limit 방지

    print(f"\n완료: 등록 {ok}개 / 스킵 {skip}개 / 실패 {fail}개")
    if ok > 0:
        print(f"\n접속 URL 예시:")
        print(f"  http://2501125.{DOMAIN_SUFFIX}  (Baltukov Nomto)")
        print(f"  http://2301104.{DOMAIN_SUFFIX}  (김광호)")

if __name__ == "__main__":
    main()
