import os
import sqlite3

from flask import Flask, abort, g, flash, make_response, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from decouple import config

from admin.admin import admin
from FDataBase import FDataBase
from forms import LoginForm, RegisterForm
from UserLogin import UserLogin

DATABASE = '/tmp/flsite.db'
SECRET_KEY = config('SECRET_KEY', default='')
MAX_CONTENT_LENGTH = 2048 * 2048

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

app.register_blueprint(admin, url_prefix='/admin')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = 'success'


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().from_DB(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
        db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


dbase = None


@app.before_first_request
def before_first_request():
    create_db()
    global dbase
    db = get_db()
    dbase = FDataBase(db)
    dbase.make_menu()


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.route('/')
def index():
    return render_template('index.html', menu=dbase.get_menu(), posts=dbase.get_posts_anonce())


@app.route('/add_post', methods=["POST", "GET"])
@login_required
def add_post():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.add_post(request.form['name'], request.form['intro'], request.form['post'], request.form['url'])
            if not res:
                flash("Ошибка добавления статьи", category='error')
            else:
                flash("Статья добавлена успешно", category='success')
        else:
            flash("Ошибка добавления статьи!", category='error')
    return render_template('add_post.html', menu=dbase.get_menu(), title="Добавление статьи")


@app.route('/post/<alias>')
def show_post(alias):
    title, intro, post, url = dbase.get_post(alias)
    if not title:
        abort(404)
    return render_template('post.html', menu=dbase.get_menu(), title=title, post=post, url=url)


@app.route('/post/post/<path:url>/delete', methods=["POST", "GET"])
@login_required
def post_delete(url):
    res = dbase.del_post(url)
    if res:
        print("Статья удалена успешно")
    return redirect(url_for('index'))


@app.route('/post/post/<path:url>/update', methods=["POST", "GET"])
@login_required
def post_update(url):
    name, intro, post, url = dbase.get_post(url)
    if request.method == "POST":
        name, intro, post, url = dbase.get_post(url)
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.update_post(request.form['name'], request.form['post'], url)
            if not res:
                flash("Ошибка добавления статьи?", category='error')
            else:
                # flash("Статья изменена успешно", category='success')
                return redirect(url_for('index'))
        else:
            flash("Ошибка добавления статьи!", category='error')
    return render_template('update_post.html', menu=dbase.get_menu(), title="Редактирование статьи", name=name,
                           text=post)


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.get_user_by_email(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get('next') or url_for('profile'))
        flash("Неверная пара логин/пароль", 'error')

    return render_template('login.html', menu=dbase.get_menu(), title="Авторизация", form=form)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash = generate_password_hash(form.psw.data)
        res = dbase.add_user(form.name.data, form.email.data, hash)
        if res:
            flash("Вы успешно зарегистрированы", category='success')
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", category='error')

    return render_template('register.html', menu=dbase.get_menu(), title="Регистрация", form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", 'success')
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', menu=dbase.get_menu(), title="Профиль")


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.update_user_avatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", 'error')
                flash("Аватар обновлен", 'success')
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", 'error')
        else:
            flash("Ошибка обновления аватара", 'error')
    return redirect(url_for('profile'))


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()
    return ''


if __name__ == '__main__':
    app.run(debug=True)
