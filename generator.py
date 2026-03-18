import os

STUDENT_DATA = [
    ("Baltukov Nomto", "2501125", "nomto"), ("CONTRERAS RIVERA MAURO JEISON", "2501111", "maurocontrerasrivera"),
    ("Dorzhieva Aiana", "2201901", "2201901aia"), ("UYANIK ILSU SUZAN", "2501115", "ilsusuzanuyanik26"),
    ("강문성", "2301301", "moonsung121200"), ("강성우", "2501003", "sjwwa951"),
    ("김광호", "2301104", "kkm9514269"), ("김준석", "2201403", "baby3565"),
    ("김진형", "2301112", "rlawlsgud2438"), ("김찬민", "2301113", "chanmin9689"),
    ("문초연", "2501080", "choyeon-mun"), ("박성준", "2301206", "goldbong74"),
    ("박준성", "2301306", "pjspjs04"), ("박지혜", "2501089", "star88222"),
    ("배정환", "2501090", "hwanarchive"), ("석민재", "2301209", "0425seok"),
    ("신윤호", "2301123", "younhnoo0325"), ("엄태영", "2501045", "sjdisjsjs90"),
    ("이순주", "2301129", "l90670847"), ("이어진", "2501058", "a46750309"),
    ("이웅재", "2501059", "kyalkwlww1"), ("이현재", "2401061", "goxodpdltm"),
    ("이희성", "2201130", "dlgmltjd3353"), ("장한별", "2501092", "hanbyul0623"),
    ("정구진", "2301136", "koojin0708"), ("정서윤", "2501085", "snsynu"),
    ("최민혁", "2501073", "minb55"), ("황연준", "2501076", "yeonjun0103"),
    ("System Admin", "0000000", "test1234")
]

BASE_PATH = "students"
IMAGE_NAME = "flask-mysql-ssh"
if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH)

docker_compose_content = "services:\n"

for i, (name, s_id, s_pw) in enumerate(STUDENT_DATA, 1):
    linux_id = f"s{s_id}"
    last_4 = s_id[-4:]
    docker_compose_content += f"""
  student{i:02d}:
    image: {IMAGE_NAME}
    container_name: student{i:02d}
    ports:
      - "2{last_4}:22"
      - "3{last_4}:5000"
      - "4{last_4}:3306"
      - "5{last_4}:7681"
    environment:
      - STUDENT_ID={linux_id}
      - USER_PASS={s_pw}
      - DB_ROOT_PASS=admin1234
    volumes:
      - ./{BASE_PATH}/{s_id}:/var/www/html
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    restart: always
"""

# [중요] 대시보드 설정: 도커 소켓 마운트 추가
docker_compose_content += """
  dashboard:
    image: flask-mysql-ssh
    container_name: dashboard
    ports:
      - "80:80"
    volumes:
      - ./dashboard:/app
      - /var/run/docker.sock:/var/run/docker.sock
    working_dir: /app
    command: python -u app.py
    user: root
    restart: always
"""

with open("docker-compose.yml", "w", encoding="utf-8") as f:
    f.write(docker_compose_content)
