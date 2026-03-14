from flask import request, jsonify
from ..models import AppService, Hardware, VM, db
from ._crud_factory import create_crud_blueprint
from ..auth import admin_required

bp = create_crud_blueprint("apps", AppService)


def _set_default_hostname(app_service, data):
    """Set hostname to parent's hostname if not provided."""
    # Only set default if hostname is not provided or is empty
    if not data.get("hostname"):
        if app_service.hardware_id:
            hardware = db.session.get(Hardware, app_service.hardware_id)
            if hardware and hardware.hostname:
                app_service.hostname = hardware.hostname
        elif app_service.vm_id:
            vm = db.session.get(VM, app_service.vm_id)
            if vm and vm.hostname:
                app_service.hostname = vm.hostname


@bp.route("", methods=["POST"])
@admin_required
def create_app():
    data = request.get_json()
    if not data:
        return jsonify(error="Request body required"), 400
    app = AppService()
    app.update_from_dict(data)
    _set_default_hostname(app, data)
    db.session.add(app)
    db.session.commit()
    return jsonify(data=app.to_dict()), 201


@bp.route("/<int:item_id>", methods=["PUT"])
@admin_required
def update_app(item_id):
    app = db.get_or_404(AppService, item_id)
    data = request.get_json()
    if not data:
        return jsonify(error="Request body required"), 400
    app.update_from_dict(data)
    _set_default_hostname(app, data)
    db.session.commit()
    return jsonify(data=app.to_dict())
