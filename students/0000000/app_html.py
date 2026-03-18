from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # 컨테이너 환경이므로 host='0.0.0.0' 설정이 필수입니다.
    app.run(host='0.0.0.0',debug=True)