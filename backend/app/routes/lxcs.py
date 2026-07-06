from flask import jsonify
from ..models import db, LXC
from ._crud_factory import create_crud_blueprint

bp = create_crud_blueprint("lxcs", LXC, detail_route=False)


@bp.route("/<int:item_id>", methods=["GET"], endpoint="get_lxc_detail")
def get_lxc_detail(item_id):
    """Override GET detail to include related apps and storage."""
    lxc = db.get_or_404(LXC, item_id)
    result = lxc.to_dict()
    result["apps"] = [app.to_dict() for app in lxc.apps]
    result["storage_pools"] = [s.to_dict() for s in lxc.storage_pools]
    if lxc.hardware:
        result["hardware_name"] = lxc.hardware.name
    return jsonify(data=result)
