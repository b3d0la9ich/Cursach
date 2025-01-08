from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from datetime import datetime
from extensions import db, login_manager
from models import User, Task  # Импорт моделей

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://infosec_user:admin@db/infosec_db'



app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)  # Инициализация базы данных
login_manager.init_app(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

# Создание таблиц при запуске приложения
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Убираем лишние пробелы
        password = request.form['password']  # Пароль оставляем как есть
        role = request.form['role']

        # Проверка логина
        if not username:
            return render_template('register.html', error_message="Логин не может быть пустым или состоять только из пробелов")

        if ' ' in username:
            return render_template('register.html', error_message="Логин не должен содержать пробелы")

        # Проверка пароля
        if not password.strip():  # Проверяем, не состоит ли пароль только из пробелов
            return render_template('register.html', error_message="Пароль не может быть пустым или состоять только из пробелов")

        if ' ' in password:
            return render_template('register.html', error_message="Пароль не должен содержать пробелы")

        # Проверка на существующего пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error_message="Пользователь с таким логином уже существует")

        # Создание нового пользователя
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Ошибка базы данных: {e}")
            db.session.rollback()
            return render_template('register.html', error_message="Ошибка при сохранении пользователя")

        return redirect(url_for('login'))  # После успешной регистрации перенаправляем на страницу входа

    return render_template('register.html')


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Личный кабинет
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'сотрудник':
        return render_template('employee_dashboard.html', user=current_user)
    elif current_user.role == 'начальник':
        tasks = Task.query.filter_by(manager_id=current_user.id).all()
        return render_template('manager_dashboard.html', user=current_user, tasks=tasks)
    return redirect(url_for('index'))



@app.route('/team')
@login_required
def team():
    if current_user.role != 'сотрудник':
        return redirect(url_for('dashboard'))
    
    manager = None
    if current_user.manager_id:
        manager = User.query.get(current_user.manager_id)
    
    team = User.query.filter_by(manager_id=current_user.manager_id).all() if manager else []
    return render_template('team.html', manager=manager, team=team)



from flask import jsonify

@app.route('/resign', methods=['POST'])
@login_required
def resign():
    # Используем current_user для получения информации о текущем пользователе
    employee_id = current_user.id

    # Проверяем, есть ли у пользователя начальник
    if not current_user.manager_id:
        return jsonify({'error': 'У вас уже нет начальника!'}), 400

    # Проверяем наличие незавершенных задач
    incomplete_tasks = Task.query.filter_by(employee_id=employee_id, status='не выполнена').all()

    if incomplete_tasks:
        # Если есть незавершенные задачи, возвращаем всплывающее уведомление
        return jsonify({'error': 'У вас есть незавершенные задачи!'}), 400

    # Если задач нет, обнуляем manager_id у пользователя
    user = User.query.get(employee_id)
    if user:
        user.manager_id = None
        db.session.commit()
        return jsonify({'success': 'Вы успешно уволились!'}), 200
    else:
        return jsonify({'error': 'Пользователь не найден'}), 400

@app.route('/manage_employees')
@login_required
def manage_employees():
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))
    
    available_employees = User.query.filter_by(manager_id=None, role='сотрудник').all()
    my_team = User.query.filter_by(manager_id=current_user.id).all()
    return render_template('manage_employees.html', available_employees=available_employees, my_team=my_team)

@app.route('/add_employee/<int:employee_id>')
@login_required
def add_employee(employee_id):
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))
    
    employee = User.query.get(employee_id)
    if employee and employee.manager_id is None:
        employee.manager_id = current_user.id
        db.session.commit()
    return redirect(url_for('manage_employees'))

@app.route('/remove_employee/<int:employee_id>')
@login_required
def remove_employee(employee_id):
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))
    
    employee = User.query.get(employee_id)
    if employee and employee.manager_id == current_user.id:
        tasks = Task.query.filter_by(employee_id=employee.id, status='не выполнена').all()
        if not tasks:
            employee.manager_id = None
            db.session.commit()
    return redirect(url_for('manage_employees'))

@app.route('/assign_tasks', methods=['GET', 'POST'])
@login_required
def assign_tasks():
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Получение данных из формы
        task_id = request.form.get('task_id')
        employee_id = request.form.get('employee_id')
        
        # Проверяем, существуют ли задача и сотрудник
        task = Task.query.get(task_id)
        employee = User.query.get(employee_id)

        if task and employee and employee.role == 'сотрудник' and task.manager_id == current_user.id:
            # Назначаем задачу сотруднику
            task.employee_id = employee.id
            task.status = 'не выполнена'
            db.session.commit()
            flash('Задача успешно назначена сотруднику.', 'success')
        else:
            flash('Ошибка при назначении задачи. Проверьте данные.', 'danger')
        
        return redirect(url_for('assign_tasks'))

    # Получаем данные для отображения в форме
    tasks = Task.query.filter_by(manager_id=current_user.id, employee_id=None).all()
    employees = User.query.filter_by(manager_id=current_user.id).all()
    
    return render_template('assign_tasks.html', tasks=tasks, employees=employees)



@app.route('/all_tasks')
@login_required
def all_tasks():
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))
    
    # Получение всех задач, созданных текущим начальником
    tasks = Task.query.filter_by(manager_id=current_user.id).all()
    
    return render_template('all_tasks.html', tasks=tasks)

@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        deadline_str = request.form['deadline']

        if not title:
            flash("Название задачи не может быть пустым или состоять только из пробелов.", "danger")
            return redirect(url_for('create_task'))

        if not description:
            flash("Описание задачи не может быть пустым или состоять только из пробелов.", "danger")
            return redirect(url_for('create_task'))

        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')

            # Check if deadline is not in the past
            if deadline < datetime.now():
                flash("Срок выполнения не может быть раньше текущего момента.", "danger")
                return redirect(url_for('create_task'))

            task = Task(
                title=title,
                description=description,
                deadline=deadline,
                manager_id=current_user.id
            )
            db.session.add(task)
            db.session.commit()
            flash("Задача успешно создана.", "success")
            return redirect(url_for('create_task'))
        except ValueError:
            flash("Некорректный формат даты и времени.", "danger")
        except Exception as e:
            print(f"Ошибка при создании задачи: {e}")
            db.session.rollback()
            flash("Ошибка при создании задачи.", "danger")

    return render_template('create_task.html')


@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if current_user.role != 'начальник':
        flash("У вас нет прав на выполнение этого действия.", "danger")
        return redirect(url_for('dashboard'))

    task = Task.query.get(task_id)
    if task and task.manager_id == current_user.id:  # Убедитесь, что задача принадлежит начальнику
        db.session.delete(task)
        db.session.commit()
        flash("Задача успешно удалена.", "success")
    else:
        flash("Задача не найдена или у вас нет прав на её удаление.", "danger")

    return redirect(url_for('all_tasks'))


@app.route('/return_task/<int:task_id>', methods=['POST'])
@login_required
def return_task(task_id):
    if current_user.role != 'сотрудник':
        return redirect(url_for('dashboard'))

    task = Task.query.get(task_id)
    if task and task.employee_id == current_user.id:
        task.employee_id = None  # Сбрасываем привязку сотрудника
        task.status = 'возвращена'  # Помечаем задачу как возвращённую
        db.session.commit()
        flash("Задача возвращена начальнику для доработки.", "info")
    else:
        flash("Задача не найдена или у вас нет прав на возврат.", "danger")
    
    return redirect(url_for('employee_tasks'))

@app.route('/employee_tasks', methods=['GET'])
@login_required
def employee_tasks():
    if current_user.role != 'сотрудник':
        return redirect(url_for('dashboard'))

    # Получаем невыполненные задачи
    incomplete_tasks = Task.query.filter_by(employee_id=current_user.id, status='не выполнена').all()
    # Получаем выполненные задачи
    completed_tasks = Task.query.filter_by(employee_id=current_user.id, status='выполнена').all()

    return render_template('tasks.html', incomplete_tasks=incomplete_tasks, completed_tasks=completed_tasks)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))

    task = Task.query.get(task_id)
    if not task or task.status not in ['не выполнена', 'возвращена']:
        flash("Эту задачу нельзя редактировать.", "danger")
        return redirect(url_for('all_tasks'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        try:
            deadline_str = request.form['deadline']
            new_deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')

            # Проверка на то, что дедлайн не меньше текущей даты
            if new_deadline < datetime.now():
                flash("Дедлайн не может быть раньше текущей даты и времени.", "danger")
                return render_template('edit_task.html', task=task)

            task.deadline = new_deadline
        except ValueError:
            flash("Некорректный формат даты.", "danger")
            return render_template('edit_task.html', task=task)

        db.session.commit()
        flash("Задача успешно обновлена.", "success")
        return redirect(url_for('all_tasks'))

    return render_template('edit_task.html', task=task)



@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    if current_user.role != 'сотрудник':
        return redirect(url_for('dashboard'))
    
    task = Task.query.get(task_id)
    if task and task.employee_id == current_user.id:
        task.status = 'выполнена'
        task.completed_at = datetime.now()  # Записываем дату завершения
        db.session.commit()
    return redirect(url_for('employee_tasks'))

@app.route('/completed_tasks')
@login_required
def completed_tasks():
    if current_user.role != 'начальник':
        return redirect(url_for('dashboard'))
    
    tasks = Task.query.filter_by(manager_id=current_user.id, status='выполнена').all()
    return render_template('completed_tasks.html', tasks=tasks)


@app.route('/tasks_overview')
@login_required
def tasks_overview():
    if current_user.role == 'начальник':
        tasks = Task.query.filter_by(manager_id=current_user.id).all()
    elif current_user.role == 'сотрудник':
        tasks = Task.query.filter_by(employee_id=current_user.id).all()
    else:
        tasks = []
    
    return render_template('tasks_overview.html', tasks=tasks)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
