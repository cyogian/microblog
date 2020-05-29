from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
import os
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from flask import request
from elasticsearch import Elasticsearch
from redis import Redis
import rq
from flask_cors import CORS
from flask_executor import Executor
from .fernet import Fernet

db = SQLAlchemy()                # flask-sqlalchemy : db-connector instance
migrate = Migrate()          # flask-migrate : db migration engine
login = LoginManager()           # flask-login : manages user login
# setting function which gets caller when login is required
login.login_view = 'auth.login'
login.login_message = _l("Please login to access this page.")
mail = Mail()
moment = Moment()
babel = Babel()
executor = Executor()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    executor.init_app(app)

    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('microblog-tasks', connection=app.redis)
    ikey = app.config['IMAGE_NAME_KEY'].encode()
    app.fernet = Fernet(ikey)

    if not babel.locale_selector_func:
        @babel.localeselector
        def get_locale():
            try:
                return request.accept_languages.best_match(app.config['LANGUAGES'])
            except RuntimeError:
                return "en"
            # return 'en'

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                                       fromaddr='no-reply@' +
                                       app.config['MAIL_SERVER'],
                                       toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                                       credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/microblog.log', maxBytes=10240, backupCount=10)

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Microblog startup')

    from .errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from . import models

    return app
