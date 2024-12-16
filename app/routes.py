from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash
from flask_login import login_required, current_user, login_user, logout_user
from .models import User, Task
from . import db
from urllib.parse import urlparse, urljoin

main = Blueprint('main', __name__, template_folder='templates', static_folder='static')

# Главная страница
@main.route('/')
def index():
    return render_template('index.html')


# Регистрация пользователей
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')  # Получаем роль из формы (сотрудник/начальник)

        if not username or not password:
            flash('Логин и пароль обязательны!', 'danger')
            return redirect(url_for('main.register'))

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким логином уже существует!', 'danger')
            return redirect(url_for('main.register'))

        # Создаем пользователя и хэшируем пароль
        new_user = User(username=username, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна!', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# Логин пользователей
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            print(f'Пользователь {user.username} авторизован: {current_user.is_authenticated}')
            flash('Вы успешно вошли!', 'success')
            return redirect(request.args.get('next') or url_for('main.dashboard'))
        else:
            flash('Неправильный логин или пароль.', 'danger')

    return render_template('login.html')


# Личный кабинет (для всех пользователей)
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username, role=current_user.role)


# Страница для начальников
@main.route('/admin')
@login_required
def admin():
    if current_user.role != 'начальник':
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('admin.html')


# Выход из системы
@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'success')
    return redirect(url_for('main.index'))


# Страница для создания задач
@main.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    if request.method == 'POST':
        task_name = request.form.get('task_name')

        if not task_name:
            flash('Название задачи обязательно!', 'danger')
            return redirect(url_for('main.tasks'))

        # Создание новой задачи и сохранение в базу данных
        new_task = Task(name=task_name, created_by=current_user.id)
        db.session.add(new_task)
        db.session.commit()

        flash('Задача успешно добавлена!', 'success')
        return redirect(url_for('main.tasks'))

    # Получение всех задач пользователя
    tasks = Task.query.filter_by(created_by=current_user.id).all()
    return render_template('tasks.html', tasks=tasks)

@main.route('/clear_tasks', methods=['POST'])
@login_required
def clear_tasks():
    from .models import Task
    Task.query.filter_by(created_by=current_user.id).delete()
    db.session.commit()
    flash('Список задач успешно очищен!', 'success')
    return redirect(url_for('main.tasks'))
