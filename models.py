from extensions import db  # Импортируем db из extensions
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    tasks = db.relationship('Task', backref='employee', lazy=True, foreign_keys='Task.employee_id')
    managed_tasks = db.relationship('Task', backref='manager', lazy=True, foreign_keys='Task.manager_id')

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='не выполнена')
    completed_at = db.Column(db.DateTime, nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
