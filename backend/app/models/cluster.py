from .base import db, BaseMixin


class Cluster(BaseMixin, db.Model):
    __tablename__ = "clusters"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.Text)
    notes = db.Column(db.Text)

    nodes = db.relationship("Node", backref="cluster", lazy="select")
