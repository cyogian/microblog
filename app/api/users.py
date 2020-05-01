from flask import url_for
from random import randint
import re
from .errors import bad_request, error_response
from flask import jsonify, request, g, abort
from .. import db
from . import bp
from ..models import User, Post, TempEmailChange
from .auth import token_auth
from .email import change_email_otp_email
from datetime import datetime, timedelta

email_regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'


@bp.route('/users/current', methods=['GET'])
@token_auth.login_required
def get_current_user():
    """ api route to get currently logged in user details """
    return jsonify(g.current_user.to_dict(include_email=True))


@bp.route('/users/by_name', methods=['GET'])
@token_auth.login_required
def get_user_by_name():
    """ api route to get user by username """
    username = request.args.get('username', "", type=str)
    return jsonify(User.query.filter_by(username=username).first_or_404().to_dict())


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    """ api route to get user by id """
    return jsonify(User.query.get_or_404(id).to_dict())


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    """ api route to get all the users existing on site | pagination enabled """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query.filter(
        User.id != g.current_user.id), page, per_page, 'api.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    """ api route to get the followers of an user | pagination enabled """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(
        user.followers, page, per_page, 'api.get_followers', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    """ api route to get the users followed by an user | pagination enabled """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(
        user.followed, page, per_page, 'api.get_followed', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/posts', methods=['GET'])
@token_auth.login_required
def get_user_posts(id):
    """ api route to get an user's post by userId | pagination enabled """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Post.to_collection_dict(
        user.posts.order_by(Post.timestamp.desc()), page, per_page, 'api.get_user_posts', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/follow', methods=['PATCH'])
@token_auth.login_required
def follow(id):
    """ api route to follow an user """
    user = User.query.get_or_404(id)
    if user == g.current_user:
        return bad_request("CANNOT_FOLLOW_YOURSELF")
    g.current_user.follow(user)
    db.session.commit()
    data = {
        "username": user.username,
        "isFollowing": g.current_user.is_following(user)
    }
    response = jsonify(data)
    response.status_code = 201
    return response


@bp.route('/users/<int:id>/unfollow', methods=['PATCH'])
@token_auth.login_required
def unfollow(id):
    """ api route to unfollow an user """
    user = User.query.get_or_404(id)
    if user == g.current_user:
        return bad_request("CANNOT_UNFOLLOW_YOURSELF")
    g.current_user.unfollow(user)
    db.session.commit()
    data = {
        "username": user.username,
        "isFollowing": g.current_user.is_following(user)
    }
    response = jsonify(data)
    response.status_code = 201
    return response


@bp.route('/users', methods=['POST'])
def create_user():
    """ api route to create new user """
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    else:
        data['username'] = data['username'].strip().lower()
        data['email'] = data['email'].strip().lower()
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if (not re.search(email_regex, data['email'])) or User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')

    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response


@bp.route('/users', methods=['PUT'])
@token_auth.login_required
def update_user():
    """ api route to change profile [username & about_me] of current user """
    user = g.current_user
    data = request.get_json() or {}
    if 'username' in data:
        data['username'] = data['username'].strip().lower()
        if data['username'] != user.username and User.query.filter_by(username=data['username']).first():
            return bad_request('please use a different username')
    data["email"] = user.email
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict(include_email=True))


@bp.route('/users/email_update', methods=['PUT'])
@token_auth.login_required
def update_email():
    """ api route to start a request to change email of currentUser """
    user = g.current_user
    data = request.get_json() or {}
    if 'email' in data:
        data['email'] = data['email'].strip().lower()
        if re.search(email_regex, data['email']):
            if User.email_is_available(data['email']):
                otp = randint(100000, 999999)
                tempEmailChange = TempEmailChange()
                tempEmailChange.otp = otp
                tempEmailChange.userId = user.id
                tempEmailChange.email = data['email']
                tempEmailChange.otp_expiration = datetime.utcnow() + timedelta(seconds=900)
                try:
                    change_email_otp_email(otp, user, data['email'])
                    db.session.add(tempEmailChange)
                    db.session.commit()
                    response = jsonify({
                        "tempId": tempEmailChange.id,
                        "otp_expiration": tempEmailChange.otp_expiration
                    })
                    response.status_code = 201
                    return response
                except Exception:
                    return error_response(500, "Unexpected Error")
            else:
                return bad_request("Email already in use")
        else:
            return bad_request("Invalid Email address")
    else:
        return bad_request("Missing Parameter: email")


@bp.route('/users/verify_update', methods=['POST'])
@token_auth.login_required
def verify_update():
    """ api route to verify otp for email change request"""
    currentUser = g.current_user
    data = request.get_json() or {}
    if 'tempId' in data:
        try:
            tempId = int(data['tempId'])
            tempEmailChange = TempEmailChange.query.get(tempId)
            if tempEmailChange:
                if 'resend' in data and data['resend']:
                    otp = randint(100000, 999999)
                    tempEmailChange.otp = otp
                    tempEmailChange.otp_expiration = datetime.utcnow() + timedelta(seconds=900)
                    try:
                        change_email_otp_email(
                            otp, User.query.get(tempEmailChange.userId), tempEmailChange.email)
                        db.session.commit()
                        response = jsonify({
                            "tempId": tempEmailChange.id,
                            "otp_expiration": tempEmailChange.otp_expiration
                        })
                        response.status_code = 201
                        return response
                    except Exception:
                        return error_response(500, "Unexpected Error")
                elif 'otp' in data:
                    try:
                        otp = int(data['otp'])
                        if (tempEmailChange.otp_expiration < datetime.utcnow()):
                            return bad_request("OTP Expired")
                        if (tempEmailChange.otp == otp):
                            if tempEmailChange.userId == currentUser.id:
                                email = tempEmailChange.email
                                if User.email_is_available(email):
                                    currentUser.email = email
                                    db.session.commit()
                                    response = jsonify(
                                        currentUser.to_dict(include_email=True))
                                    response.status_code = 201
                                    db.session.delete(tempEmailChange)
                                    db.session.commit()
                                    return response
                                else:
                                    db.session.delete(tempEmailChange)
                                    db.session.commit()
                                    return error_response(500, "Unexpected Error")
                            else:
                                return error_response(401, "Can't change other users data")
                        else:
                            return bad_request("Wrong OTP")
                    except ValueError:
                        return bad_request("Invalid OTP format")
                else:
                    return bad_request("Missing Parameter: otp")
            else:
                return error_response(404, "Temporary Request Not Found")
        except ValueError:
            return bad_request("Invalid tempId")
    else:
        return bad_request("Missing Parameter: tempId")


@bp.route('/users/duplicate_check', methods=['POST'])
def duplicate_check():
    """ api route to check username and email availablity """
    data = request.get_json() or {}
    if 'username' not in data and 'email' not in data:
        return bad_request("Invalid data provided")
    response = {
        "success": False,
        "errors": {}
    }
    if 'username' in data:
        username = data["username"].strip().lower()
        if len(username) <= 2:
            response["errors"]["username"] = "Username too short"
        elif len(username) > 64:
            response["errors"]["username"] = "Username too long"
        elif len(username.split(" ")) > 1:
            response["errors"]["username"] = "Username can't contain spaces"
        elif not User.username_is_available(username):
            response["errors"]["username"] = "Username already in use"

    if 'email' in data:
        email = data["email"].strip().lower()
        if re.search(email_regex, email):
            if not User.email_is_available(email):
                response["errors"]["email"] = "Email already in use"
        else:
            response["errors"]["email"] = "not a valid email address"

    if not response["errors"]:
        response["success"] = True

    return jsonify(response)
