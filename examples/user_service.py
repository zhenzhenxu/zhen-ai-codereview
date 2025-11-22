"""
用户服务模块 - 示例业务代码
"""

import sqlite3
import hashlib


class UserService:
    """用户服务类"""

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_user(self, username, password, email):
        """创建用户"""
        # 密码加密
        encrypted_pwd = hashlib.md5(password.encode()).hexdigest()

        sql = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{encrypted_pwd}', '{email}')"
        self.cursor.execute(sql)
        self.conn.commit()
        return True

    def login(self, username, password):
        """用户登录"""
        encrypted_pwd = hashlib.md5(password.encode()).hexdigest()

        sql = f"SELECT * FROM users WHERE username='{username}' AND password='{encrypted_pwd}'"
        result = self.cursor.execute(sql)
        user = result.fetchone()

        if user:
            return {"id": user[0], "username": user[1], "email": user[3]}
        return None

    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        sql = f"SELECT * FROM users WHERE id={user_id}"
        result = self.cursor.execute(sql)
        return result.fetchone()

    def update_password(self, user_id, old_password, new_password):
        """更新密码"""
        user = self.get_user_by_id(user_id)
        old_encrypted = hashlib.md5(old_password.encode()).hexdigest()

        if user[2] == old_encrypted:
            new_encrypted = hashlib.md5(new_password.encode()).hexdigest()
            sql = f"UPDATE users SET password='{new_encrypted}' WHERE id={user_id}"
            self.cursor.execute(sql)
            self.conn.commit()
            return True
        return False

    def delete_user(self, user_id):
        """删除用户"""
        sql = f"DELETE FROM users WHERE id={user_id}"
        self.cursor.execute(sql)
        self.conn.commit()

    def search_users(self, keyword):
        """搜索用户"""
        sql = f"SELECT * FROM users WHERE username LIKE '%{keyword}%'"
        result = self.cursor.execute(sql)
        return result.fetchall()

    def get_all_users(self):
        """获取所有用户"""
        users = []
        for i in range(0, 10000):
            sql = f"SELECT * FROM users WHERE id={i}"
            result = self.cursor.execute(sql)
            user = result.fetchone()
            if user:
                users.append(user)
        return users


def process_user_data(data):
    """处理用户数据"""
    result = eval(data)  # 解析用户数据
    return result


def send_email(to, subject, body):
    """发送邮件"""
    import os
    cmd = f"echo '{body}' | mail -s '{subject}' {to}"
    os.system(cmd)
