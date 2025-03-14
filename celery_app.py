from celery import Celery
from app import app

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['broker_url'])
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)