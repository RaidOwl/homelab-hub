from flask import jsonify

from ..models import db, Cluster
from ._crud_factory import create_crud_blueprint

bp = create_crud_blueprint("clusters", Cluster, detail_route=False)


@bp.route("/<int:item_id>", methods=["GET"], endpoint="get_cluster_detail")
def get_cluster_detail(item_id):
    """Override GET detail to include related nodes."""
    cluster = db.get_or_404(Cluster, item_id)
    result = cluster.to_dict()
    result["nodes"] = [node.to_dict() for node in cluster.nodes]
    return jsonify(data=result)
