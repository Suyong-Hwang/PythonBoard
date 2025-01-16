from flask import Flask, session, url_for, render_template, flash, send_from_directory, jsonify ,request, redirect
import os
from datetime import datetime
from models import DBManager
from functools import wraps

app = Flask(__name__)

manager = DBManager()

app.secret_key = 'your-secret-key'  # 비밀 키 설정, 실제 애플리케이션에서는 더 안전한 방법으로 설정해야 함


#디텍토리생성
#디렉토리 생성


# 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')  # 로그인되지 않았다면 로그인 페이지로 리디렉션
        return f(*args, **kwargs)
    return decorated_function

# 관리자 권한 필수 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['role'] != 'admin':
            return "접근 권한이 없습니다", 403  # 관리자만 접근 가능
        return f(*args, **kwargs)
    return decorated_function

# 로그인 페이지 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        user = manager.get_user_by_id(userid)  # DB에서 사용자 정보를 가져옴
        if user and user['password'] == password:  # 아이디와 비밀번호가 일치하면
            session['user'] = userid  # 세션에 사용자 아이디 저장
            session['role'] = user['role']  # 세션에 역할(role) 저장
            session['username'] = user['uname'] #세션에 이름(username) 저장
            flash('로그인 성공!', 'success')
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))  # 대시보드로 리디렉션
            else :
                return redirect(url_for('dashboard'))
        else:
            flash('아이디 또는 비밀번호가 일치하지 않습니다.', 'error')  # 로그인 실패 시 메시지
            return render_template('login.html')  # 로그인 폼 다시 렌더링

    return render_template('login.html')  # GET 요청시 로그인 폼 보여주기

# 대시보드 페이지 (로그인된 사용자만 접근)
@app.route('/dashboard')
@login_required  # 로그인된 사용자만 접근 가능
def dashboard():
    page = request.args.get('page', 1, type=int)  # 페이지 번호를 쿼리 파라미터로 받음
    posts = manager.get_posts_by_page(page)  # 페이지에 맞는 게시글 가져오기
    total_posts = manager.get_total_post_count()
    total_pages = (total_posts + 4) // 5  # 5개씩 페이지 나누기
    userid = session['user']
    user = manager.get_user_by_id(userid)
    return render_template('dashboard.html', user = user, posts=posts, page=page, total_pages=total_pages )

# 관리자 페이지 (관리자만 접근)
@app.route('/admin')
@admin_required  # 관리자만 접근 가능
def admin_dashboard():
    page = request.args.get('page', 1, type=int)  # 페이지 번호를 쿼리 파라미터로 받음
    posts = manager.get_posts_by_page(page)  # 페이지에 맞는 게시글 가져오기
    total_posts = manager.get_total_post_count()
    total_pages = (total_posts + 4) // 5  # 5개씩 페이지 나누기
    userid = session['user']
    user = manager.get_user_by_id(userid)
    return render_template('admin_dashboard.html', user = user, posts=posts, page=page, total_pages=total_pages)  # 관리자 대시보드 렌더링

# 로그아웃 라우트
@app.route('/logout')
def logout():
    # session.pop('user', None)  # 세션에서 사용자 정보 제거
    # session.pop('role', None)  # 세션에서 역할 정보 제거
    session.clear()
    return redirect('/login')  # 로그아웃 후 로그인 페이지로 리디렉션

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static','uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 회원가입
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        username = request.form['username']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('암호가 일치하지 않습니다', 'error')
            return render_template('signup.html')
        if manager.duplicate_member(userid):
            flash('이미 존재하는 아이디 입니다.', 'error')
            return render_template('signup.html')
        if manager.register_member(userid,username,password):
            return redirect(url_for('index'))
        flash('회원가입에 실패했습니다.', 'error') 
        return redirect(url_for('register'))
    return render_template('signup.html')

#회원탈퇴
@app.route('/delete_account', methods=['GET', 'POST'])
@login_required  # 로그인된 사용자만 접근 가능
def delete_account():
    userid = session['user']  # 세션에서 사용자 ID 가져오기
    
    if request.method == 'POST':
        # DB에서 사용자 정보 삭제
        if manager.delete_member(userid):
            # 세션에서 사용자 정보 삭제
            session.clear()  # 사용자 세션을 모두 삭제
            flash('회원 탈퇴가 완료되었습니다.', 'success')
            return redirect(url_for('index'))  # 탈퇴 후 홈 화면으로 리디렉션
        
        flash('회원 탈퇴에 실패했습니다. 다시 시도해 주세요.', 'error')
        return redirect(url_for('dashboard'))  # 탈퇴 실패 시 대시보드로 돌아가기
    
    return render_template('delete_account.html')  # GET 요청 시 회원 탈퇴 확인 페이지 표시

#회원목록
@app.route('/members')
@admin_required  # 관리자만 접근 가능
def members():
    # 모든 회원 정보 조회
    members = manager.get_all_members()  # DB에서 모든 회원을 가져오는 메서드 호출
    return render_template('members.html', members=members)

#관리자 회원목록에서 탈퇴시키기
@app.route('/delete_member/<userid>', methods=['POST'])
@admin_required  # 관리자만 접근 가능
def delete_member(userid):
    # DB에서 해당 회원 삭제
    if manager.delete_member(userid):  # DB에서 회원 삭제
        flash(f'{userid} 회원이 탈퇴되었습니다.', 'success')
    else:
        flash(f'{userid} 회원 탈퇴 실패.', 'error')
    
    return redirect(url_for('members'))


#목록 보기
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)  # 페이지 번호를 쿼리 파라미터로 받음
    posts = manager.get_posts_by_page(page)  # 페이지에 맞는 게시글 가져오기
    total_posts = manager.get_total_post_count()
    total_pages = (total_posts + 4) // 5  # 5개씩 페이지 나누기
    return render_template('index.html', posts=posts, page=page, total_pages=total_pages)



#내용 보기
@app.route('/post/<int:id>')
def view_post(id):
    post = manager.get_post_by_id(id)
    return render_template('view.html', post=post)

#내용 추가
#파일 업로드 : enctype="multipart/form-data", methods='POST', type="file", accept=".png,.jpg,.gif"
@app.route('/post/add', methods=['GET','POST'])
def add_post():
    username = session['username']
  
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # 첨부파일 한개
        file = request.files['file'] # id = "file" 이기때문에 request.files['file']
        filename = file.filename if file else None
        
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if manager.insert_post(username, title, content, filename):
            return redirect("/dashboard")
        return "게시글 추가 실패", 400
    
    return render_template('add.html')

@app.route('/post/edit/<int:id>', methods=['GET','POST'])
def edit_post(id):
    post= manager.get_post_by_id(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # 첨부파일 한개
        file = request.files['file'] # id = "file" 이기때문에 request.files['file']
        filename = file.filename if file else None
        
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if manager.update_post( id, title, content, filename):
            return redirect("/")
        return "게시글 수정 실패", 400
    
    return render_template('edit.html', post=post)

@app.route('/post/delete/<int:id>')
def delete_post(id):
    if manager.delete_post(id):
        return redirect(url_for('dashboard'))
    return "게시글 삭제 실패", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)




