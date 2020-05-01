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
