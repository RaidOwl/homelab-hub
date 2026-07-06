from .base import db, BaseMixin


class AppService(BaseMixin, db.Model):
    __tablename__ = "apps"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hardware_id = db.Column(db.Integer, db.ForeignKey("hardware.id", ondelete="SET NULL"), nullable=True)
    vm_id = db.Column(db.Integer, db.ForeignKey("vms.id", ondelete="SET NULL"), nullable=True)
    lxc_id = db.Column(db.Integer, db.ForeignKey("lxcs.id", ondelete="SET NULL"), nullable=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    hostname = db.Column(db.Text)
    ip_address = db.Column(db.Text)
    external_hostname = db.Column(db.Text)
    port = db.Column(db.Integer)
    https = db.Column(db.Boolean, default=False)
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)

    __table_args__ = (
        db.CheckConstraint(
            "(CASE WHEN hardware_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN vm_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN lxc_id IS NOT NULL THEN 1 ELSE 0 END) <= 1",
            name="ck_apps_single_parent",
        ),
    )
