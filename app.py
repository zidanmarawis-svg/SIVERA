# app.py
# Titik masuk aplikasi. Mendaftarkan blueprint dan inisialisasi.
import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from models import db, User

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Registrasi blueprint
    from routes.auth import auth_bp
    from routes.warga import warga_bp
    from routes.staf import staf_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from flask import send_from_directory

    app.register_blueprint(auth_bp)
    app.register_blueprint(warga_bp)
    app.register_blueprint(staf_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # Arahkan sesuai role
        if current_user.role == 'warga':
            return redirect(url_for('warga.status'))
        elif current_user.role == 'staf':
            return redirect(url_for('staf.verifikasi'))
        return redirect(url_for('admin.dashboard'))

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)