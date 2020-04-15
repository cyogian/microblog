from flask import jsonify, request, g, abort, url_for
from .. import db
from . import bp
from ..models import Post
from .auth import token_auth
from ..api.errors import bad_request


@bp.route('/posts', methods=["GET"])
@token_auth.login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Post.to_collection_dict(
        Post.query.order_by(Post.timestamp.desc()
                            ), page, per_page, 'api.get_posts')
    return jsonify(data)


@bp.route('/posts/followed_posts', methods=["GET"])
@token_auth.login_required
def get_followed_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Post.to_collection_dict(
        g.current_user.followed_posts(), page, per_page, 'api.get_posts')
    return jsonify(data)


@bp.route('/posts/<int:id>', methods=["GET"])
@token_auth.login_required
def get_post(id):
    return jsonify(Post.query.get_or_404(id).to_dict())


@bp.route('/posts/<int:id>', methods=["PUT"])
@token_auth.login_required
def update_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author:
        abort(401)
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request('please provide a body for post')
    if len(data["body"]) > 180:
        return bad_request('please make sure that the post is not more than 180 characters long')
    post.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(post.to_dict())


@bp.route('/posts/<int:id>', methods=["DELETE"])
@token_auth.login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author:
        abort(401)
    db.session.delete(post)
    db.session.commit()
    return '', 204


@bp.route('/posts', methods=['POST'])
@token_auth.login_required
def create_post():
    data = request.get_json() or {}
    if "body" not in data:
        return bad_request('please provide a body for post')
    if len(data["body"]) > 180:
        return bad_request('please make sure that the post is not more than 180 characters long')
    data["user_id"] = g.current_user.id
    post = Post()
    post.from_dict(data, new_post=True)
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response
