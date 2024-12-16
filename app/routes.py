from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db

main = Blueprint('main', __name__, template_folder='templates', static_folder='static')

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Отладка: вывод данных формы
        print(f"Регистрация: username={username}, password={password}")

        if not username or not password:
            flash('Логин и пароль обязательны!', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует!', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            # Отладка: вывод ошибки
            print(f"Ошибка при добавлении пользователя: {e}")
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте ещё раз.', 'danger')

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Проверка пользователя в базе данных
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flash('Вы успешно вошли!')
            return redirect(url_for('main.index'))
        else:
            flash('Неверный логин или пароль.')

    return render_template('login.html')
