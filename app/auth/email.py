from flask_mail import Message
from flask import render_template
from app import mail, app
from threading import Thread
from flask_babel import lazy_gettext as _l

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_mail(
        subject=_l("[Microblog] Reset Your Password"), 
        sender=app.config['ADMINS'][0], 
        recipients=[user.email],
        text_body=render_template("email/reset_password.txt", user=user, token=token), 
        html_body=render_template("email/reset_password.html", user=user, token=token)
    )

def send_email_verification_email(user):
    token = user.get_email_verification_token()
    send_mail(
        subject=_l("[Microblog] Verify Your Email"), 
        sender=app.config['ADMINS'][0], 
        recipients=[user.email],
        text_body=render_template("email/verify_email.txt", user=user, token=token), 
        html_body=render_template("email/verify_email.html", user=user, token=token)
    )
