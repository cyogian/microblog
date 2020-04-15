from flask import url_for
from ..api.errors import bad_request
from flask import jsonify, request, g, abort
from .. import db
from . import bp
from ..models import User, Post
from .auth import token_auth
import re


@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())


@bp.route('/users/by_name', methods=['GET'])
@token_auth.login_required
def get_user_by_name():
    username = request.args.get('username', "", type=str)
    return jsonify(User.query.filter_by(username=username).first_or_404().to_dict())


@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)


@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(
        user.followers, page, per_page, 'api.get_followers', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(
        user.followed, page, per_page, 'api.get_followed', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/posts', methods=['GET'])
@token_auth.login_required
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Post.to_collection_dict(
        user.posts, page, per_page, 'api.get_user_posts', id=id)
    return jsonify(data)


@bp.route('/users/<int:id>/follow', methods=['PATCH'])
@token_auth.login_required
def follow(id):
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
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response


@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    if g.current_user.id != id:
        abort(401)
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if 'username' in data and data['username'] != user.username and User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route('/users/duplicate_check', methods=['POST'])
def duplicate_check():
    data = request.get_json() or {}
    if 'username' not in data and 'email' not in data:
        return bad_request("Invalid data provided")
    response = {
        "success": False,
        "errors": {}
    }
    if 'username' in data:
        username = data["username"]
        if len(username) <= 2:
            response["errors"]["username"] = "Username too short"
        elif len(username) > 64:
            response["errors"]["username"] = "Username too long"
        elif len(username.split(" ")) > 1:
            response["errors"]["username"] = "Username can't contain spaces"
        elif not User.username_is_available(username):
            response["errors"]["username"] = "Username already in use"

    if 'email' in data:
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        email = data["email"]
        if re.search(regex, email):
            if not User.email_is_available(email):
                response["errors"]["email"] = "Email already in use"
        else:
            response["errors"]["email"] = "not a valid email address"

    if not response["errors"]:
        response["success"] = True

    return jsonify(response)
