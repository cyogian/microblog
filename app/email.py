from flask_mail import Message
from flask import render_template
from app import mail, app
from threading import Thread
from flask_babel import lazy_gettext as _l

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_mail(subject, sender, recipients, text_body, html_body):
    msg = Message(subject=subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

