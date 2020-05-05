from flask import render_template
from flask import current_app
from ..email import send_mail


def change_email_otp_email(otp, user, email):
    send_mail(
        subject="[Microblog] OTP for changing email of @"+user.username,
        sender=current_app.config['ADMINS'][0],
        recipients=[email],
        text_body=render_template(
            "change_email/change_email_otp.txt", user=user, otp=otp),
        html_body=render_template(
            "change_email/change_email_otp.html", user=user, otp=otp)
    )


def create_user_otp_email(otp, email):
    send_mail(
        subject="[Microblog] OTP for creating new user",
        sender=current_app.config['ADMINS'][0],
        recipients=[email],
        text_body=render_template(
            "create_user/create_user_otp.txt", otp=otp),
        html_body=render_template(
            "create_user/create_user_otp.html", otp=otp)
    )


def forgot_password_otp_email(otp, username, email):
    send_mail(
        subject="[Microblog] OTP to reset forgotten password",
        sender=current_app.config['ADMINS'][0],
        recipients=[email],
        text_body=render_template(
            "forgot_password/forgot_password_otp.txt", username=username, otp=otp),
        html_body=render_template(
            "forgot_password/forgot_password_otp.html", username=username, otp=otp)
    )
