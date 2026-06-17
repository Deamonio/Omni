#!/usr/bin/env python3

"""Run a full health check across all student containers.

Checks:
- SSH reachability on the published container port and on sshpiper port 22
- SSH login with the container's own credentials
- Web reachability on the published HTTP port and on internal 127.0.0.1:5000
- MariaDB reachability for the student account and root account

By default this loops every 60 seconds. Use --once for a single pass.
"""

from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

try:
    import paramiko
except ImportError as exc:  # pragma: no cover - environment issue
    print(f"FATAL: paramiko is required: {exc}", file=sys.stderr)
    raise SystemExit(2)


@dataclass(frozen=True)
class ServiceInfo:
    service: str
    student_id: str
    user_pass: str
    db_root_pass: str
    ssh_port: int
    web_port: int
    db_port: int


def run(cmd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, shell=True, text=True, capture_output=True)


def parse_published_ports(port_text: str) -> Dict[int, int]:
    ports: Dict[int, int] = {}
    for host_port, container_port in re.findall(r"0\.0\.0\.0:(\d+)->(\d+)/tcp", port_text):
        ports[int(container_port)] = int(host_port)
    return ports


def load_services() -> List[ServiceInfo]:
    proc = run("docker ps --format '{{.Label \"com.docker.compose.service\"}}\t{{.Ports}}'")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "docker ps failed")

    services: List[ServiceInfo] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        service, ports_text = parts[0], parts[1]
        if not service.startswith("student"):
            continue

        ports = parse_published_ports(ports_text)
        if not {22, 5000, 3306}.issubset(ports):
            continue

        env = run(
            f"docker compose exec -T {service} sh -lc 'printf \"%s\\t%s\\t%s\" \"$STUDENT_ID\" \"$USER_PASS\" \"$DB_ROOT_PASS\"'"
        )
        if env.returncode != 0 or not env.stdout.strip():
            continue
        student_id, user_pass, db_root_pass = (env.stdout.strip().split("\t") + ["", "", ""])[:3]

        services.append(
            ServiceInfo(
                service=service,
                student_id=student_id,
                user_pass=user_pass,
                db_root_pass=db_root_pass,
                ssh_port=ports[22],
                web_port=ports[5000],
                db_port=ports[3306],
            )
        )

    return sorted(services, key=lambda item: item.service)


def tcp_open(host: str, port: int, timeout: float = 3.0, retries: int = 3) -> bool:
    for _ in range(max(1, retries)):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            pass
        finally:
            sock.close()
        time.sleep(0.3)
    return False


def curl_code(url: str, retries: int = 3) -> str:
    for _ in range(max(1, retries)):
        proc = run(f"curl -m 5 -sS -o /dev/null -w '%{{http_code}}' {url}")
        if proc.returncode == 0:
            code = proc.stdout.strip() or "ERR"
            if code != "000":
                return code
        time.sleep(0.3)
    return "ERR"


def paramiko_login(port: int, username: str, password: str) -> bool:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname="127.0.0.1",
            port=port,
            username=username,
            password=password,
            timeout=7,
            auth_timeout=7,
            banner_timeout=7,
            look_for_keys=False,
            allow_agent=False,
        )
        stdin, stdout, stderr = client.exec_command("echo OK")
        return stdout.read().decode().strip().endswith("OK")
    except Exception:
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def internal_db_ping(service: str, command: str) -> bool:
    proc = run(f"docker compose exec -T {service} sh -lc '{command}'")
    return proc.returncode == 0


def check_one(service: ServiceInfo) -> dict:
    internal_web = "ERR"
    internal_user_db = False
    internal_root_db = False

    proc = run(
        "docker compose exec -T {svc} sh -lc '\n"
        "(curl -m 5 -sS -o /dev/null -w \"%{{http_code}}\" http://127.0.0.1:5000 || echo ERR); echo;\n"
        "mysqladmin ping -h 127.0.0.1 -u \"$STUDENT_ID\" -p\"$USER_PASS\" --silent >/dev/null 2>&1; echo U:$?;\n"
        "mysqladmin ping -h 127.0.0.1 -u root -p\"$DB_ROOT_PASS\" --silent >/dev/null 2>&1; echo R:$?\n"
        "'".format(svc=service.service)
    )
    if proc.returncode == 0:
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if lines:
            internal_web = lines[0]
        internal_user_db = any(line == "U:0" for line in lines)
        internal_root_db = any(line == "R:0" for line in lines)

    host_web = curl_code(f"http://127.0.0.1:{service.web_port}")
    host_ssh = tcp_open("127.0.0.1", service.ssh_port)
    host_db = tcp_open("127.0.0.1", service.db_port)

    return {
        "service": service.service,
        "student_id": service.student_id,
        "ssh_port": service.ssh_port,
        "web_port": service.web_port,
        "db_port": service.db_port,
        "host_ssh": host_ssh,
        "host_web": host_web,
        "host_db": host_db,
        "ssh_direct": paramiko_login(service.ssh_port, service.student_id, service.user_pass),
        "ssh_p22": paramiko_login(22, service.student_id, service.user_pass),
        "internal_web": internal_web,
        "internal_user_db": internal_user_db,
        "internal_root_db": internal_root_db,
    }


def is_ok_http(code: str) -> bool:
    return code.startswith("2") or code.startswith("3") or code == "401"


def summarize(result: dict) -> Tuple[bool, str]:
    ok = (
        result["host_ssh"]
        and result["host_db"]
        and is_ok_http(result["host_web"])
        and result["ssh_direct"]
        and result["ssh_p22"]
        and is_ok_http(result["internal_web"])
        and (result["internal_user_db"] or result["internal_root_db"])
    )
    line = (
        f"{result['service']} {result['student_id']} "
        f"ssh={int(result['host_ssh'])}/{int(result['ssh_direct'])}/{int(result['ssh_p22'])} "
        f"db={int(result['host_db'])}/{int(result['internal_user_db'] or result['internal_root_db'])} "
        f"web={result['host_web']}/{result['internal_web']}"
    )
    return ok, line


def run_once() -> int:
    services = load_services()
    if not services:
        print("No student services found.")
        return 2

    results: List[dict] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(check_one, service) for service in services]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item["service"])
    failures: List[dict] = []
    for result in results:
        ok, line = summarize(result)
        print(line)
        if not ok:
            failures.append(result)

    print(f"TOTAL {len(results)} PASS {len(results) - len(failures)} FAIL {len(failures)}")
    if failures:
        print("---FAILED---")
        for result in failures:
            print(result["service"], result["student_id"])
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Full student health check")
    parser.add_argument("--once", action="store_true", help="Run one pass and exit")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between checks in loop mode")
    args = parser.parse_args()

    if args.once:
        return run_once()

    while True:
        started = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"=== healthcheck {started} ===")
        code = run_once()
        print(f"=== exit {code} ===")
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())