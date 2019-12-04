from flask import render_template
from flask_babel import lazy_gettext as _l
from flask_babel import _
from flask import current_app
from app.email import send_mail
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_mail(
        subject=_("[Microblog] Reset Your Password"), 
        sender=current_app.config['ADMINS'][0], 
        recipients=[user.email],
        text_body=render_template("email/reset_password.txt", user=user, token=token), 
        html_body=render_template("email/reset_password.html", user=user, token=token)
    )

def send_email_verification_email(user):
    token = user.get_email_verification_token()
    send_mail(
        subject=_("[Microblog] Verify Your Email"), 
        sender=current_app.config['ADMINS'][0], 
        recipients=[user.email],
        text_body=render_template("email/verify_email.txt", user=user, token=token), 
        html_body=render_template("email/verify_email.html", user=user, token=token)
    )
