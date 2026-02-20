from flask import Blueprint, jsonify, request
from ..models import db, NodeSetting

bp = Blueprint("settings", __name__, url_prefix="/api/settings")

@bp.route("/nodes", methods=["GET"])
def get_all_node_settings():
    settings = NodeSetting.query.all()
    return jsonify(data=[
        {
            "node_type": s.node_type,
            "node_id": s.node_id,
            "label_visible": s.label_visible
        } for s in settings
    ])

@bp.route("/nodes/<string:node_type>/<int:node_id>", methods=["PUT"])
def update_node_setting(node_type, node_id):
    data = request.get_json()
    if not data or "label_visible" not in data:
        return jsonify(error="label_visible required"), 400

    setting = NodeSetting.query.filter_by(node_type=node_type, node_id=node_id).first()
    if not setting:
        setting = NodeSetting(
            node_type=node_type,
            node_id=node_id,
            label_visible=data["label_visible"]
        )
        db.session.add(setting)
    else:
        setting.label_visible = data["label_visible"]

    db.session.commit()
    return jsonify(message="Saved")
