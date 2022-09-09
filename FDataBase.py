import math
import sqlite3
import time


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def make_menu(self):
        menu = [("Главная", "/"), ("Добавить статью", "/add_post"), ("Авторизация", "/login")]
        try:
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM mainmenu ")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                return False

            for i in range(0, 3):
                title, url = menu[i]
                self.__cur.execute(f'INSERT INTO mainmenu VALUES (NULL,?,?)', (title, url))
                self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка создания меню:" + str(e))
        return []

    def get_menu(self):
        sql = 'SELECT * FROM mainmenu'
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res:
                return res
        except:
            print("Ошибка чтения из БД")
        return []

    def add_post(self, title, intro, text, url):
        try:
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM posts WHERE url LIKE '{url}' ")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Статья с таким URL уже существует")
                return False

            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO posts VALUES (NULL,?,?,?,?,?)", (title, intro, text, url, tm))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления статьи в базу данных" + str(e))
            return False

        return True

    def get_posts_anonce(self):
        try:
            self.__cur.execute(f"SELECT id, title, intro, text,url FROM posts ORDER BY time DESC")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения статьи из БД:" + str(e))
        return []

    def get_post(self, alias):
        try:
            self.__cur.execute(f"SELECT title, intro, text, url FROM posts WHERE url LIKE '{alias}' LIMIT 1")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения статьи из БД" + str(e))
        return False, False, False, False

    def del_post(self, url):
        try:
            self.__cur.execute(f"delete FROM posts WHERE url LIKE '{url}' ")
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            print("Ошибка получения статьи из БД" + str(e))
            return False

    def update_post(self, title, text, url):
        try:
            self.__cur.execute(f" UPDATE posts SET title = ?, text=? WHERE url like '{url}'", (title, text))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления статьи в базу данных" + str(e))
            return False

        return True

    def add_user(self, name, email, hpsw):
        try:
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM users WHERE email LIKE '{email}' ")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Пользователь с таким email уже существует")
                return False

            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO users VALUES (NULL,?,?,?,NULL,?)", (name, email, hpsw, tm))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя в базу данных" + str(e))
            return False

        return True

    def get_user(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE id =  {user_id} LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из базы данных" + str(e))
        return False

    def get_user_by_email(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email =  '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных из базы данных" + str(e))
        return False

    def update_user_avatar(self, avatar, user_id):
        if not avatar:
            return False

        try:
            binary = sqlite3.Binary(avatar)
            self.__cur.execute(f"UPDATE users SET avatar =  ? WHERE id =  ?", (binary, user_id))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка обновления аватара в БД" + str(e))
            return False
        return True
