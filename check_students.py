import subprocess
import requests

def get_mapped_port(container):
    try:
        cmd = f"docker port {container}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            # Look for mapping of internal port 5000
            for line in result.stdout.strip().split('\n'):
                if "5000/tcp" in line:
                    parts = line.split(':')
                    return parts[-1]
    except:
        pass
    return None

def get_student_id(container):
    try:
        cmd = f"docker exec {container} printenv STUDENT_ID"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "Unknown"
    except:
        return "Unknown"

def check_url(port):
    if not port:
        return "BROKEN", "No port mapping for 5000/tcp"
    url = f"http://localhost:{port}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            if "Hello, Omni!" in response.text:
                return "UNSET_OK", response.text
            else:
                return "SET_OK", response.text
        else:
            return "BROKEN", f"HTTP {response.status_code}"
    except Exception as e:
        return "BROKEN", str(e)

def main():
    stats = {"UNSET_OK": 0, "SET_OK": 0, "BROKEN": 0}
    set_accounts = []
    broken_accounts = []

    for i in range(1, 30):
        container = f"student{i:02d}"
        student_id = get_student_id(container)
        port = get_mapped_port(container)
        status, detail = check_url(port)
        
        stats[status] += 1
        
        if status == "SET_OK":
            set_accounts.append(f"{container} | {student_id} | {port}")
        elif status == "BROKEN":
            broken_accounts.append(f"{container} ({detail})")

    print("1) Total counts per class:")
    for k in ["UNSET_OK", "SET_OK", "BROKEN"]:
        print(f"   {k}: {stats[k]}")

    print("\n2) List of SET accounts (container | STUDENT_ID | port):")
    if set_accounts:
        for item in set_accounts:
            print(f"   {item}")
    else:
        print("   None")

    print("\n3) List of BROKEN accounts:")
    if broken_accounts:
        for item in broken_accounts:
            print(f"   {item}")
    else:
        print("   None")

if __name__ == '__main__':
    main()
