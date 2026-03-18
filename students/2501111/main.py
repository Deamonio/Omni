from flask import Flask

# Flask 애플리케이션 생성
app = Flask(__name__)

# 라우팅 설정: '/' 경로로 접속했을 때 실행될 함수
@app.route('/')
def hello_world():
    return 'Hello, Flask!'

# 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
