from .base import db, BaseMixin


class LXC(BaseMixin, db.Model):
    __tablename__ = "lxcs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("hardware.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    ctid = db.Column(db.Integer)
    hostname = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    mac_address = db.Column(db.Text)
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Float)
    disk_gb = db.Column(db.Float)
    os = db.Column(db.Text)
    unprivileged = db.Column(db.Boolean, default=True)
    onboot = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    apps = db.relationship("AppService", backref="lxc", lazy="select")
    storage_pools = db.relationship("Storage", backref="lxc", lazy="select")
