from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'deamon_mesh_secret_key'

# MySQL 연결 설정 (사용자 정보에 맞춰 확인하세요)
# mysql+pymysql://디비아이디:디비비번@localhost/디비명
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://s0000000:test1234@localhost/student_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DB 모델 (기존과 동일) ---
class User(db.Model):
    __tablename__ = 'users'
    student_id = db.Column(db.String(10), primary_key=True)
    login_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    grade = db.relationship('Grade', backref='user', uselist=False)

class Grade(db.Model):
    __tablename__ = 'grades'
    student_id = db.Column(db.String(10), db.ForeignKey('users.student_id'), primary_key=True)
    sql_score = db.Column(db.Integer, default=0)
    network_score = db.Column(db.Integer, default=0)
    programming_score = db.Column(db.Integer, default=0)

# --- DB 모델 정의 추가 ---
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(10), db.ForeignKey('users.student_id'), nullable=False)
    target_id = db.Column(db.String(10), nullable=False)  # 어떤 학생의 페이지인지
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    # 작성자 정보를 가져오기 위한 관계
    author = db.relationship('User', backref='my_comments')

# --- 학번 생성 로직 ---
def generate_student_id():
    current_year = datetime.now().year # 2026
    last_user = User.query.filter(User.student_id.like(f"{current_year}%")).order_by(User.student_id.desc()).first()
    if last_user:
        last_num = int(last_user.student_id[4:])
        return f"{current_year}{str(last_num + 1).zfill(4)}"
    return f"{current_year}0001"

# --- 유틸리티 함수 및 컨텍스트 프로세서 ---
def calculate_grade(score):
    if score >= 95: return 'A+'
    elif score >= 90: return 'A'
    elif score >= 85: return 'B+'
    elif score >= 80: return 'B'
    elif score >= 75: return 'C+'
    elif score >= 70: return 'C'
    elif score >= 65: return 'D+'
    elif score >= 60: return 'D'
    else: return 'F'

def fetch_comments(target_id):
    return Comment.query.filter_by(target_id=target_id).order_by(Comment.created_at.asc()).all()

@app.context_processor
def utility_processor():
    return dict(get_grade=calculate_grade, get_comments=fetch_comments)

# --- 라우트 구현 (url_for 사용 권장) ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_id = generate_student_id()
        new_user = User(
            student_id=new_id,
            login_id=request.form['login_id'],
            password=hashed_pw,
            name=request.form['name'],
            phone=request.form.get('phone'),
            email=request.form.get('email')
        )
        new_grade = Grade(student_id=new_id)
        
        try:
            db.session.add(new_user)
            db.session.add(new_grade)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash("이미 존재하는 아이디입니다.")
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(login_id=request.form['login_id']).first()
        if not user:
            return render_template('login.html')

        raw_password = request.form['password']

        # Legacy support: some seeded accounts may still store plaintext passwords.
        password_ok = check_password_hash(user.password, raw_password)
        if not password_ok and user.password == raw_password:
            password_ok = True
            user.password = generate_password_hash(raw_password, method='pbkdf2:sha256')
            db.session.commit()

        if password_ok:
            session['user_id'] = user.student_id
            session['is_admin'] = user.is_admin
            session['user_name'] = user.name
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['is_admin']:
        users = User.query.filter_by(is_admin=False).all()
        return render_template('admin.html', users=users)
    else:
        grade = Grade.query.get(session['user_id'])
        return render_template('student.html', grade=grade)

@app.route('/edit_grade/<student_id>', methods=['POST'])
def edit_grade(student_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    grade = Grade.query.get(student_id)
    if grade:
        grade.sql_score = request.form['sql']
        grade.network_score = request.form['network']
        grade.programming_score = request.form['programming']
        db.session.commit()
    return redirect(url_for('dashboard'))

# --- 댓글 작성 라우트 ---
@app.route('/add_comment/<target_id>', methods=['POST'])
def add_comment(target_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form.get('content')
    if content:
        new_comment = Comment(
            student_id=session['user_id'],
            target_id=target_id,
            content=content
        )
        db.session.add(new_comment)
        db.session.commit()
    
    # 관리자가 댓글을 달았다면 관리자 대시보드로, 학생이면 본인 대시보드로 리다이렉트
    return redirect(request.referrer or url_for('dashboard'))

# --- 댓글 삭제 라우트 ---
@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    comment = Comment.query.get_or_404(comment_id)
    
    # 본인이거나 관리자인 경우에만 삭제 가능
    if comment.student_id == session['user_id'] or session.get('is_admin'):
        db.session.delete(comment)
        db.session.commit()
        flash("댓글이 삭제되었습니다.", "success")
    else:
        flash("삭제 권한이 없습니다.", "danger")
        
    return redirect(request.referrer or url_for('dashboard'))

# --- 댓글 수정 라우트 ---
@app.route('/edit_comment/<int:comment_id>', methods=['POST'])
def edit_comment(comment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    comment = Comment.query.get_or_404(comment_id)
    
    # 본인만 수정 가능
    if comment.student_id == session['user_id']:
        new_content = request.form.get('content')
        if new_content:
            comment.content = new_content
            db.session.commit()
            flash("댓글이 수정되었습니다.", "success")
    else:
        flash("수정 권한이 없습니다.", "danger")
        
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # 로컬 테스트용 개발 서버 포트
    app.run(host='0.0.0.0', debug=True)