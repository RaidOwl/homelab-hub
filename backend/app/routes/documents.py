from flask import Blueprint, jsonify, request

from ..models import db, Document, Hardware, VM, AppService, Storage, Network, Misc
from ..auth import admin_required

bp = Blueprint("documents", __name__, url_prefix="/api/docs")


@bp.route("", methods=["GET"])
def list_docs():
    """Return all documents as a flat list (frontend builds tree from parent_id).
    Optional query params:
    - entity_type: filter by linked entity type
    - entity_id: filter by linked entity id
    """
    query = Document.query
    
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")
    
    if entity_type:
        query = query.filter_by(linked_entity_type=entity_type)
    if entity_id:
        query = query.filter_by(linked_entity_id=int(entity_id))
    
    docs = query.order_by(Document.sort_order).all()
    return jsonify(data=[d.to_dict() for d in docs], count=len(docs))


@bp.route("/<int:doc_id>", methods=["GET"])
def get_doc(doc_id):
    doc = db.get_or_404(Document, doc_id)
    return jsonify(data=doc.to_dict())


@bp.route("", methods=["POST"])
@admin_required
def create_doc():
    data = request.get_json() or {}
    doc = Document(
        title=data.get("title", "Untitled"),
        content=data.get("content", ""),
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order", 0),
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify(data=doc.to_dict()), 201


@bp.route("/<int:doc_id>", methods=["PUT"])
@admin_required
def update_doc(doc_id):
    doc = db.get_or_404(Document, doc_id)
    data = request.get_json()
    if not data:
        return jsonify(error="Request body required"), 400
    doc.update_from_dict(data)
    db.session.commit()
    return jsonify(data=doc.to_dict())


@bp.route("/<int:doc_id>", methods=["DELETE"])
@admin_required
def delete_doc(doc_id):
    doc = db.get_or_404(Document, doc_id)
    # Orphan children to root level
    for child in doc.children:
        child.parent_id = None
    db.session.delete(doc)
    db.session.commit()
    return jsonify(message="Deleted"), 200


@bp.route("/linkable-items", methods=["GET"])
def get_linkable_items():
    """Return all items that can be linked to a document."""
    items = []
    
    # Hardware
    for hw in Hardware.query.order_by(Hardware.name).all():
        items.append({
            "type": "hardware",
            "id": hw.id,
            "name": hw.name,
            "label": f"🖥️ {hw.name}"
        })
    
    # VMs
    for vm in VM.query.order_by(VM.name).all():
        items.append({
            "type": "vm",
            "id": vm.id,
            "name": vm.name,
            "label": f"💿 {vm.name}"
        })
    
    # Apps/Services
    for app in AppService.query.order_by(AppService.name).all():
        items.append({
            "type": "app",
            "id": app.id,
            "name": app.name,
            "label": f"📦 {app.name}"
        })
    
    # Storage
    for storage in Storage.query.order_by(Storage.name).all():
        items.append({
            "type": "storage",
            "id": storage.id,
            "name": storage.name,
            "label": f"💾 {storage.name}"
        })
    
    # Networks
    for network in Network.query.order_by(Network.name).all():
        items.append({
            "type": "network",
            "id": network.id,
            "name": network.name,
            "label": f"🌐 {network.name}"
        })
    
    # Misc
    for misc in Misc.query.order_by(Misc.name).all():
        items.append({
            "type": "misc",
            "id": misc.id,
            "name": misc.name,
            "label": f"📌 {misc.name}"
        })
    
    return jsonify(data=items, count=len(items))


@bp.route("/<int:doc_id>/move", methods=["PATCH"])
@admin_required
def move_doc(doc_id):
    doc = db.get_or_404(Document, doc_id)
    data = request.get_json() or {}
    if "parent_id" in data:
        doc.parent_id = data["parent_id"]
    if "sort_order" in data:
        doc.sort_order = data["sort_order"]
    db.session.commit()
    return jsonify(data=doc.to_dict())
