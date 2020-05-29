from . import bp
from .auth import basic_auth, token_auth
from flask import g, jsonify, current_app
from .. import db
from .errors import error_response


@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    user = g.current_user
    if not user.is_verified:
        message = f'User email is not verified. Please visit {current_app.config["BASE_URL"]} to login and complete email verification process.'
        return error_response(403, message)
    token_data = user.get_token()
    db.session.commit()
    return jsonify(token_data)


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204
