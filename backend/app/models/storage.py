from .base import db, BaseMixin


class Storage(BaseMixin, db.Model):
    __tablename__ = "storage"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("hardware.id", ondelete="SET NULL"), nullable=True)
    vm_id = db.Column(db.Integer, db.ForeignKey("vms.id", ondelete="SET NULL"), nullable=True)
    node_id = db.Column(db.Integer, db.ForeignKey("nodes.id", ondelete="SET NULL"), nullable=True)
    name = db.Column(db.Text, nullable=False)
    storage_type = db.Column(db.Text)
    raid_type = db.Column(db.Text)
    drive_count = db.Column(db.Integer)
    raw_space_tb = db.Column(db.Float)
    usable_space_tb = db.Column(db.Float)
    filesystem = db.Column(db.Text)
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Relationship to shares
    shares = db.relationship("Share", back_populates="storage", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint(
            "NOT (hardware_id IS NOT NULL AND vm_id IS NOT NULL)",
            name="ck_storage_single_parent",
        ),
    )

    def to_dict(self):
        result = super().to_dict()
        result['shares'] = [share.to_dict() for share in self.shares]
        return result
