from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '<h1>Hello, World!</h1><p>이곳은 강현님의 AI 실습 서버입니다.</p>'

if __name__ == '__main__':
    # 컨테이너 환경이므로 host='0.0.0.0' 설정이 필수입니다.
    app.run(host='0.0.0.0', debug=True)
