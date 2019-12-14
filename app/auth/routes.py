from . import bp
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, EmailVerificationForm
from .email import send_email_verification_email, send_password_reset_email
from flask import render_template, flash, redirect, url_for, request
from .. import db
from ..models import User
from flask_login import current_user, logout_user, login_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _
from flask_babel import lazy_gettext as _l


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template("login.html", title=_l("Sign In"), form = form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        send_email_verification_email(user)
        flash(_("Congratulations, you are now a registered user!\nAn email containing the verification link has been sent to the email associated with this account."))
        return redirect(url_for('auth.login'))
    return render_template("register.html", title=_l("Register"), form=form)

@bp.route('/email_verification_prompt', methods=["GET", "POST"])

@login_required
def email_verification_prompt():
    if current_user.is_verified:
        return redirect(url_for("main.index"))
    form = EmailVerificationForm()
    if form.validate_on_submit():
        send_email_verification_email(current_user)
        flash(_("An email containing the verification link has been sent to the email associated with this account."))
        return redirect(url_for("auth.email_verification_prompt"))
    return render_template("email_verification_prompt.html", title=_l("Verify Your Account"), form=form)
    
@bp.route('/verify_email/<token>')
def verify_email(token):
    if current_user.is_authenticated:
        if current_user.is_verified:
            return redirect(url_for("main.index"))
        user = User.verify_email_verification_token(token)
        if not user:
            return redirect(url_for("main.index"))
        if current_user == user:
            print("LEVEL 5")
            user.is_verified = True
            db.session.commit()
            flash(_("Your account is successfully verified."))
            return redirect(url_for("main.index"))
        return redirect(url_for("main.index"))
        
    user = User.verify_email_verification_token(token)
    if not user:
        return redirect(url_for("main.index"))
    if user.is_verified:
        return redirect(url_for("main.index"))
    user.is_verified = True
    db.session.commit()
    flash(_("Your account is successfully verified. Login to continue."))
    return redirect(url_for("auth.login"))
       
        

@bp.route('/reset_password_request', methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(_("Check your email for the instructions to reset your password."))
        return redirect(url_for("auth.login"))
    return render_template("reset_password_request.html", title=_l("Reset Password"), form=form)

@bp.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_("Your password has been reset."))
        return redirect(url_for("auth.login"))
    return render_template('reset_password.html', title=_l("Reset Password"), form=form)
