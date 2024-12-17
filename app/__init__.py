from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Инициализация миграций

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Добавляем Flask-Migrate
    migrate.init_app(app, db)

    # Регистрация Blueprint после создания приложения
    from .routes import main
    app.register_blueprint(main)

    # Установка user_loader здесь, после инициализации db
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
