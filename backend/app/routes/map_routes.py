from flask import Blueprint, jsonify, request
from ipaddress import ip_address, ip_network, AddressValueError

from ..models import (
    db, Hardware, VM, AppService, Storage, Network, Misc, Share,
    NetworkMember, Relationship, MapLayout, MapEdge,
)

bp = Blueprint("map", __name__, url_prefix="/api/map")

ENTITY_MAP = {
    "hardware": Hardware,
    "vms": VM,
    "apps": AppService,
    "storage": Storage,
    "networks": Network,
    "misc": Misc,
}


def get_network_for_ip(ip_addr):
    """Determine which network an IP address belongs to based on subnet matching."""
    if not ip_addr:
        return None
    
    try:
        ip = ip_address(ip_addr)
        # Check all networks to see if this IP is in their subnet
        for network in Network.query.all():
            if network.subnet:
                try:
                    net = ip_network(network.subnet, strict=False)
                    if ip in net:
                        return network
                except (AddressValueError, ValueError):
                    continue
    except (AddressValueError, ValueError):
        pass
    
    return None


@bp.route("/graph", methods=["GET"])
def get_graph():
    """Return full graph data: nodes + edges for Cytoscape.js."""
    nodes = []
    edges = []

    # Collect all nodes with additional metadata (exclude networks)
    for entity_type, model in ENTITY_MAP.items():
        # Skip networks - they'll be shown in a separate panel
        if entity_type == "networks":
            continue
            
        for item in model.query.all():
            # Assign ranks for hierarchical layout
            rank_map = {
                "hardware": 0,
                "vms": 1,
                "apps": 2,
                "storage": 2,
                "misc": 3,
            }
            node_data = {
                "id": f"{entity_type}-{item.id}",
                "label": item.name,
                "type": entity_type,
                "entity_id": item.id,
                "rawName": item.name,
                "rank": rank_map.get(entity_type, 3),
            }
            
            # If icon exists, distinguish between image (data URL) and emoji
            if hasattr(item, "icon") and item.icon:
                # Check if it's an image data URL
                if item.icon.startswith("data:image/"):
                    node_data["imageIcon"] = item.icon
                    node_data["label"] = ""  # No text label for images

                    # Create a separate node for the label
                    label_node_data = {
                        "id": f"label-{entity_type}-{item.id}",
                        "label": item.name,
                        "type": "label_node",
                        "parent_id": node_data["id"]
                    }
                    nodes.append({"data": label_node_data})

                    # Create an edge to connect the main node to its label
                    edges.append({
                        "data": {
                            "source": node_data["id"],
                            "target": label_node_data["id"],
                        },
                        "classes": "label_edge"
                    })
                else:
                    # It's an emoji or text icon
                    node_data["icon"] = item.icon
                    node_data["label"] = item.icon  # Only show the icon
            
            # Automatically determine network membership based on IP address
            if hasattr(item, "ip_address") and item.ip_address:
                network = get_network_for_ip(item.ip_address)
                if network:
                    node_data["networkId"] = network.id
                    node_data["networkName"] = network.name
                    # Use network color or default if not set
                    node_data["networkColor"] = network.color or "#E74C3C"
            
            nodes.append({"data": node_data})

    # Edges from FK relationships
    for vm in VM.query.all():
        edges.append({
            "data": {
                "source": f"hardware-{vm.hardware_id}",
                "target": f"vms-{vm.id}",
                "label": "hosts",
            }
        })

    for app in AppService.query.all():
        if app.hardware_id:
            edges.append({
                "data": {
                    "source": f"hardware-{app.hardware_id}",
                    "target": f"apps-{app.id}",
                    "label": "runs",
                }
            })
        elif app.vm_id:
            edges.append({
                "data": {
                    "source": f"vms-{app.vm_id}",
                    "target": f"apps-{app.id}",
                    "label": "runs",
                }
            })

    for s in Storage.query.all():
        if s.hardware_id:
            edges.append({
                "data": {
                    "source": f"hardware-{s.hardware_id}",
                    "target": f"storage-{s.id}",
                    "label": "storage",
                }
            })
        elif s.vm_id:
            edges.append({
                "data": {
                    "source": f"vms-{s.vm_id}",
                    "target": f"storage-{s.id}",
                    "label": "storage",
                }
            })

    # Add shares as nodes and edges from storage to shares
    for share in Share.query.all():
        # Create share node
        node_data = {
            "id": f"shares-{share.id}",
            "label": share.name,
            "type": "shares",
            "entity_id": share.id,
            "rawName": share.name,
            "rank": 3,  # Same level as misc
            "shareType": share.share_type,
        }
        
        # Add network membership if share has an IP
        if share.ip:
            network = get_network_for_ip(share.ip)
            if network:
                node_data["networkId"] = network.id
                node_data["networkName"] = network.name
                node_data["networkColor"] = network.color or "#E74C3C"
        
        nodes.append({"data": node_data})
        
        # Create edge from storage to share
        edges.append({
            "data": {
                "source": f"storage-{share.storage_id}",
                "target": f"shares-{share.id}",
                "label": share.share_type or "share",
            }
        })

    # Skip network membership edges since networks aren't nodes anymore

    # Edges from generic relationships
    for rel in Relationship.query.all():
        edges.append({
            "data": {
                "source": f"{rel.source_type}-{rel.source_id}",
                "target": f"{rel.target_type}-{rel.target_id}",
                "label": rel.label or "",
            }
        })

    # Manual map edges
    for edge in MapEdge.query.all():
        edges.append({
            "data": {
                "source": f"{edge.source_type}-{edge.source_id}",
                "target": f"{edge.target_type}-{edge.target_id}",
                "label": edge.label or "",
                "manual": True,
            }
        })

    return jsonify(nodes=nodes, edges=edges)


@bp.route("/networks", methods=["GET"])
def get_networks():
    """Return all networks for display in a separate panel."""
    networks = []
    for network in Network.query.all():
        networks.append({
            "id": network.id,
            "name": network.name,
            "color": network.color or "#E74C3C",  # Default red if no color set
            "vlan_id": network.vlan_id,
            "notes": network.notes,
        })
    return jsonify(networks=networks)


@bp.route("/layout", methods=["GET"])
def get_layout():
    """Get all saved node positions."""
    layouts = MapLayout.query.all()
    result = {}
    for layout in layouts:
        result[f"{layout.node_type}-{layout.node_id}"] = {
            "x": layout.x,
            "y": layout.y,
            "pinned": layout.pinned,
        }
    return jsonify(data=result)


@bp.route("/layout", methods=["PUT"])
def save_layout():
    """Bulk save node positions."""
    data = request.get_json()
    if not data or "positions" not in data:
        return jsonify(error="positions required"), 400

    for node_key, pos in data["positions"].items():
        parts = node_key.rsplit("-", 1)
        if len(parts) != 2:
            continue
        node_type, node_id = parts[0], int(parts[1])

        layout = MapLayout.query.filter_by(node_type=node_type, node_id=node_id).first()
        if layout:
            layout.x = pos["x"]
            layout.y = pos["y"]
            layout.pinned = pos.get("pinned", True)
        else:
            layout = MapLayout(
                node_type=node_type, node_id=node_id,
                x=pos["x"], y=pos["y"], pinned=pos.get("pinned", True),
            )
            db.session.add(layout)

    db.session.commit()
    return jsonify(message="Saved")


@bp.route("/edges", methods=["POST"])
def create_edge():
    data = request.get_json()
    if not data:
        return jsonify(error="Request body required"), 400
    edge = MapEdge(
        source_type=data["source_type"],
        source_id=data["source_id"],
        target_type=data["target_type"],
        target_id=data["target_id"],
        label=data.get("label"),
        style=data.get("style"),
    )
    db.session.add(edge)
    db.session.commit()
    return jsonify(data={"id": edge.id}), 201


@bp.route("/edges/<int:edge_id>", methods=["DELETE"])
def delete_edge(edge_id):
    edge = db.get_or_404(MapEdge, edge_id)
    db.session.delete(edge)
    db.session.commit()
    return jsonify(message="Deleted")
