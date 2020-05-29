from . import bp
from flask import request, current_app, jsonify
from .. import db, executor
from .errors import bad_request
from ..models import TempEmailChange, TempEmailVerify
from datetime import datetime, timedelta


def tempClean():
    t = datetime.utcnow() - timedelta(seconds=3600)
    delete_q = TempEmailVerify.__table__.delete().where(
        TempEmailVerify.otp_expiration < t)
    db.session.execute(delete_q)
    delete_q = TempEmailChange.__table__.delete().where(
        TempEmailChange.otp_expiration < t)
    db.session.execute(delete_q)
    db.session.commit()


@bp.route("/cleanup")
def cleanup():
    key = current_app.config["CLEANUP_KEY"]
    request_key = request.args.get("key")
    if request_key:
        if request_key == key:
            executor.submit(tempClean)
            response = jsonify({"message": "Cleanup Request Accepted"})
            response.status_code = 201
            return response
        else:
            return bad_request("Invalid Key")
    else:
        return bad_request("Missing Parameter: key")
