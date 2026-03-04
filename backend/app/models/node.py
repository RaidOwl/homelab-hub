from .base import db, BaseMixin


class Node(BaseMixin, db.Model):
    __tablename__ = "nodes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    hostname = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    mac_address = db.Column(db.Text)
    cpu = db.Column(db.Text)
    cpu_cores = db.Column(db.Integer)
    ram_gb = db.Column(db.Float)
    os = db.Column(db.Text)
    cluster_id = db.Column(db.Integer, db.ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)

    vms = db.relationship("VM", backref="node", lazy="select",
                          foreign_keys="VM.node_id")
    apps = db.relationship("AppService", backref="node", lazy="select",
                           foreign_keys="AppService.node_id")
    storage_pools = db.relationship("Storage", backref="node", lazy="select",
                                    foreign_keys="Storage.node_id")
