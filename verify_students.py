import subprocess
import re

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1
    except Exception as e:
        return str(e), -1

def main():
    containers = []
    for i in range(1, 30):
        containers.append(f"student{i:02d}")

    print(f"{'Container':<12} | {'Student ID':<12} | {'Port':<6} | {'Status':<6} | {'Classification'}")
    print("-" * 70)

    stats = {"TEMPLATE_OK": 0, "HELLO_OMNI": 0, "HTTP_NON_200": 0, "TIMEOUT_OR_EMPTY": 0, "ERROR": 0}
    failing = []

    for container in containers:
        # 1. Get STUDENT_ID
        env_out, _ = run_command(f"docker exec {container} printenv STUDENT_ID")
        student_id = env_out if env_out and not env_out.startswith("Error") else "N/A"

        # 2. Get host port
        port_out, _ = run_command(f"docker port {container} 5000")
        match = re.search(r":(\d+)$", port_out)
        host_port = match.group(1) if match else "N/A"

        # 3. Request page
        status_code = "N/A"
        classification = "ERROR"
        
        if host_port != "N/A":
            curl_out, _ = run_command(f"curl -s -w '%{{http_code}}' --max-time 5 http://localhost:{host_port}")
            if curl_out == "TIMEOUT":
                classification = "TIMEOUT_OR_EMPTY"
            elif len(curl_out) >= 3:
                status_code = curl_out[-3:]
                body = curl_out[:-3]
                
                if status_code == "200":
                    if 'A+ Finder' in body or '성적 조회 서비스' in body:
                        classification = "TEMPLATE_OK"
                    elif 'Hello, Omni!' in body:
                        classification = "HELLO_OMNI"
                    else:
                        classification = "UNKNOWN_CONTENT"
                else:
                    classification = "HTTP_NON_200"
            else:
                classification = "TIMEOUT_OR_EMPTY"
        else:
            classification = "NO_PORT"

        print(f"{container:<12} | {student_id:<12} | {host_port:<6} | {status_code:<6} | {classification}")
        
        stats[classification] = stats.get(classification, 0) + 1
        if classification != "TEMPLATE_OK":
            failing.append(container)

    print("\nSummary Counts:")
    for k, v in stats.items():
        print(f"{k}: {v}")
    
    print("\nFailing Containers:")
    print(", ".join(failing) if failing else "None")

if __name__ == "__main__":
    main()
