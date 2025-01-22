import mysql.connector 
from datetime import datetime
from flask import session

class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    #디렉토리 생성
    def connect(self): 
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.6",
                user = "suyong",
                password="1234",
                database="board_db3",
                charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True)
        
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패 : {error}")
    
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    
    def get_all_posts(self):
        try: 
            self.connect()
            sql = "SELECT * FROM posts"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패 : {error}")
            return []
        finally:
            self.disconnect()

    def get_user_by_id(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE userid = %s"
            value = (userid,)
            self.cursor.execute(sql,value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패: {error}")
            return None 
        finally:
            self.disconnect()
        
    def insert_post(self, username, title, content , filename):
        try: 
            self.connect()

            sql = "INSERT INTO posts( username, title, content, filename, created_at, updated_at, views) values (%s, %s, %s, %s, %s, %s, %s)"
            values = (username, title, content, filename, datetime.now(), datetime.now(), 0)
            self.cursor.execute(sql, values)
            

            # values = [(name, email, department, salary, datetime.now().date()),(name, email, department, salary, datetime.now().date())]
            # self.cursor.execute(sql, values)
           

            self.connection.commit()
            return True
        except mysql.connector.Error as error :
            self.connection.rollback()
            print(f"게시글 추가 실패 : {error}")
            return False
        finally:
            self.disconnect()
    
    def get_post_by_id(self, id):
        try: 
            self.connect()
            sql = """
                UPDATE posts
                SET views = views + 1
                WHERE id = %s
            """
            # SQL 실행
            self.cursor.execute(sql, (id,))
            self.connection.commit()
            
            sql = "SELECT * FROM posts WHERE id = %s"
            value = (id,) # 튜플 1개일때 
            self.cursor.execute(sql, value)
            return self.cursor.fetchone()
        except mysql.connector.Error as error :
            print(f"내용 조회 실패 : {error}")
            return None
        finally:
            self.disconnect()
    

    def update_post(self, id, title, content, filename):
        try: 
            self.connect()
            if filename :
                sql = """UPDATE posts SET 
                         title= %s, content= %s, filename=%s 
                         WHERE id = %s"""
                values = (title, content, filename, id)
            else :
                sql = """UPDATE posts SET 
                         title= %s, content= %s 
                         WHERE id = %s"""
                values = (title, content, id)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error :
            self.connection.rollback()
            print(f"내용 수정 실패 : {error}")
            return False
        finally:
            self.disconnect()

    def delete_post(self, id):
        try: 
            self.connect()
            sql = "DELETE FROM posts WHERE id = %s"
            value = (id,) # 튜플 1개일때 
            self.cursor.execute(sql, value)
            self.connection.commit()
            return True
        except mysql.connector.Error as error :
            print(f"직원 삭제 실패 : {error}")
            return False
        finally:
            self.disconnect()

    def register_member(self, userid, username, password):
        try:
            self.connect()
            sql="""
                INSERT INTO members(userid, uname, password,role) VALUES(%s,%s,%s,%s)
                """
            role = "user" # role 기본값을 user로 설정
            values = (userid, username,password, role)
            self.cursor.execute(sql,values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()

    def duplicate_member(self, userid):
        try:
            self.connect()
            sql = 'SELECT * FROM members WHERE userid = %s'
            self.cursor.execute(sql, (userid,))
            result = self.cursor.fetchone()
            if result : 
                return True
            else :
                return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()
    
    #모든 회원의 정보를 가져옴
    def get_all_members(self):
        try:
            self.connect()
            sql = "SELECT userid, uname AS username, role FROM members"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as error:
            print(f"회원 목록 조회 실패 : {error}")
            return []
        finally:
            self.disconnect()        
    
    def delete_member(self, userid):
        try:
            self.connect()
            sql = "DELETE FROM members WHERE userid = %s"
            value = (userid, )
            self.cursor.execute(sql,value)
            self.connection.commit()
            return True
        except Exception as error:
            print(f"회원 탈퇴 실패 : {error}")
            return False
        finally : 
            self.disconnect()

    def get_posts_by_page(self, page, posts_per_page=5):
        try:
            self.connect()
            offset = (page - 1) * posts_per_page
            sql = "SELECT * FROM posts ORDER BY created_at DESC LIMIT %s OFFSET %s"
            self.cursor.execute(sql, (posts_per_page, offset))
            return self.cursor.fetchall()
        except mysql.connector.Error as error:
            print(f"게시글 가져오기 실패: {error}")
            return []
        finally:
            self.disconnect()
    
    def get_total_post_count(self):
        try:
            self.connect()
            sql = "SELECT COUNT(*) as total_count FROM posts"
            self.cursor.execute(sql)
            result = self.cursor.fetchone()  # result는 이제 딕셔너리 형태
            return result['total_count'] if result else 0  # 딕셔너리에서 키로 값을 가져옴
            
        except mysql.connector.Error as error:
            print(f"게시글 개수 가져오기 실패: {error}")
            return 0
        finally:
            self.disconnect()