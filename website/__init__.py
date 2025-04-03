from flask import Flask
from flask_login import LoginManager
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
DATABASE = {
    'dbname': os.getenv('DB_NAME', 'barbershop'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Database connection
def get_db_connection():
    conn = psycopg2.connect(**DATABASE)
    return conn

def run_query(query: str, data=None, is_fetch=True):
    conn = psycopg2.connect(**DATABASE)
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, data)
            if is_fetch:
                return cur.fetchall()
            conn.commit()
    conn.close()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

    from .views import views
    from .auth import auth
    from website.models import User

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.get(id)

    return app
