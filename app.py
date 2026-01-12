from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore

# 현재 디렉토리를 템플릿 및 정적 파일 폴더로 설정
app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'secret-key-for-class-website' # 보안 키

# Firebase 초기화 (서비스 계정 키 필요)
# Firebase Console -> Project Settings -> Service Accounts -> Generate new private key
# 다운로드 받은 JSON 파일을 'serviceAccountKey.json'으로 저장하세요.
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 회원 정보 클래스 (Firestore 데이터 래퍼)
class User(UserMixin):
    def __init__(self, id, username, password, name):
        self.id = id
        self.username = username
        self.password = password
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        data = doc.to_dict()
        return User(id=doc.id, username=data['username'], password=data['password'], name=data['name'])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        
        # Firestore에서 사용자 검색
        users_ref = db.collection('users')
        docs = users_ref.where('username', '==', username).stream()
        
        if any(docs):
            flash('이미 존재하는 아이디입니다.')
            return redirect(url_for('register'))
        
        # 비밀번호 암호화하여 Firestore에 저장
        users_ref.add({
            'username': username, 
            'name': name, 
            'password': generate_password_hash(password)
        })
        flash('회원가입 완료! 로그인해주세요.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users_ref = db.collection('users')
        docs = users_ref.where('username', '==', username).stream()
        user_doc = next(docs, None) # 첫 번째 결과 가져오기
        
        if user_doc:
            user_data = user_doc.to_dict()
            if check_password_hash(user_data['password'], password):
                user = User(id=user_doc.id, username=user_data['username'], password=user_data['password'], name=user_data['name'])
                login_user(user)
                return redirect(url_for('index'))
        
        flash('아이디 또는 비밀번호를 확인해주세요.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
