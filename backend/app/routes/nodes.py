from flask import jsonify

from ..models import db, Node
from ._crud_factory import create_crud_blueprint

bp = create_crud_blueprint("nodes", Node, detail_route=False)


@bp.route("/<int:item_id>", methods=["GET"], endpoint="get_node_detail")
def get_node_detail(item_id):
    """Override GET detail to include related VMs, apps, and storage."""
    node = db.get_or_404(Node, item_id)
    result = node.to_dict()
    result["vms"] = [vm.to_dict() for vm in node.vms]
    result["apps"] = [app.to_dict() for app in node.apps]
    result["storage_pools"] = [s.to_dict() for s in node.storage_pools]
    if node.cluster:
        result["cluster_name"] = node.cluster.name
    return jsonify(data=result)
