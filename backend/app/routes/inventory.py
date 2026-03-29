from flask import Blueprint, jsonify, request
from ..models import *
from ..models.base import db
import json

bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

ENTITY_MAP = {
    "hardware": Hardware,
    "vms": VM,
    "apps": AppService,
    "storage": Storage,
    "networks": Network,
    "misc": Misc,
}


@bp.route("", methods=["GET"])
def get_all_inventory():
    """Return all inventory items across all types."""
    result = {}
    for entity_type, model in ENTITY_MAP.items():
        result[entity_type] = [item.to_dict() for item in model.query.all()]
    return jsonify(data=result)


@bp.route("/search", methods=["GET"])
def search_inventory():
    """Search across all entity types by name."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(data=[], count=0)

    results = []
    pattern = f"%{q}%"
    for entity_type, model in ENTITY_MAP.items():
        matches = model.query.filter(model.name.ilike(pattern)).all()
        for item in matches:
            d = item.to_dict()
            d["_type"] = entity_type
            results.append(d)

    return jsonify(data=results, count=len(results))


@bp.route('/export', methods=['GET'])
def export_database():
    """Export all data from the database"""
    try:
        # Define the order of data to export to maintain relationships
        data = {
            'hardware': [h.to_dict() for h in Hardware.query.all()],
            'vms': [vm.to_dict() for vm in VM.query.all()],
            'apps': [app.to_dict() for app in AppService.query.all()],
            'storage': [s.to_dict() for s in Storage.query.all()],
            'networks': [n.to_dict() for n in Network.query.all()],
            'misc': [m.to_dict() for m in Misc.query.all()],
            'documents': [d.to_dict() for d in Document.query.all()]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/import', methods=['POST'])
def import_database():
    """Import data into the database"""
    try:
        import_data = request.get_json()

        # Clear existing data in dependency order
        db.session.query(Share).delete()  # Delete shares before storage
        db.session.query(AppService).delete()
        db.session.query(VM).delete()
        db.session.query(Hardware).delete()
        db.session.query(Storage).delete()
        db.session.query(Network).delete()
        db.session.query(Misc).delete()
        db.session.query(Document).delete()

        # Helper function to remove auto-generated fields
        def clean_item(item):
            item_copy = item.copy()
            # Remove fields that should be auto-generated
            item_copy.pop('id', None)
            item_copy.pop('created_at', None)
            item_copy.pop('updated_at', None)
            # Remove nested relationships (they'll be imported separately)
            item_copy.pop('shares', None)
            return item_copy

        # Import new data in dependency order
        # First, import hardware (no dependencies)
        if 'hardware' in import_data:
            for item in import_data['hardware']:
                hardware = Hardware(**clean_item(item))
                db.session.add(hardware)
        
        db.session.flush()  # Get IDs for hardware

        # Import VMs (depends on hardware)
        if 'vms' in import_data:
            for item in import_data['vms']:
                vm = VM(**clean_item(item))
                db.session.add(vm)
        
        db.session.flush()  # Get IDs for VMs

        # Import apps (depends on hardware and VMs)
        if 'apps' in import_data:
            for item in import_data['apps']:
                app = AppService(**clean_item(item))
                db.session.add(app)

        # Import storage (depends on hardware and VMs)
        storage_entries = []  # Track storage objects with their share data
        if 'storage' in import_data:
            for item in import_data['storage']:
                # Extract shares before cleaning
                shares_data = item.get('shares', [])
                cleaned_item = clean_item(item)
                storage = Storage(**cleaned_item)
                db.session.add(storage)
                storage_entries.append((storage, shares_data))

        db.session.flush()  # Get IDs for storage

        # Now import shares (depends on storage)
        for storage, shares_data in storage_entries:
            if not shares_data:
                continue
            for share_data in shares_data:
                cleaned_share = clean_item(share_data)
                cleaned_share['storage_id'] = storage.id  # Set the correct storage_id
                share = Share(**cleaned_share)
                db.session.add(share)

        # Import networks
        if 'networks' in import_data:
            for item in import_data['networks']:
                network = Network(**clean_item(item))
                db.session.add(network)

        # Import misc
        if 'misc' in import_data:
            for item in import_data['misc']:
                misc = Misc(**clean_item(item))
                db.session.add(misc)

        # Import documents
        if 'documents' in import_data:
            for item in import_data['documents']:
                document = Document(**clean_item(item))
                db.session.add(document)

        db.session.commit()
        return jsonify({'message': 'Database imported successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
