from .base import db, BaseMixin


class VM(BaseMixin, db.Model):
    __tablename__ = "vms"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("hardware.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    hostname = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    mac_address = db.Column(db.Text)
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Float)
    disk_gb = db.Column(db.Float)
    os = db.Column(db.Text)
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)

    apps = db.relationship("AppService", backref="vm", lazy="select")
    storage_pools = db.relationship("Storage", backref="vm", lazy="select")
