from flask_login import UserMixin
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Функция загрузки пользователя по ID

# models.py
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='сотрудник')
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Ссылка на начальника

    # Связь с подчинёнными
    subordinates = db.relationship('User', backref=db.backref('manager', remote_side=[id]))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Внешний ключ для связи с пользователем

    def __repr__(self):
        return f'<Task {self.name}>'