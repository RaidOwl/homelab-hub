from .base import db, BaseMixin


class Document(BaseMixin, db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.Text, nullable=False, default="Untitled")
    content = db.Column(db.Text, nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    linked_entity_type = db.Column(db.Text, nullable=True)  # e.g., "hardware", "vm", "app", "storage", "network", "misc"
    linked_entity_id = db.Column(db.Integer, nullable=True)

    children = db.relationship("Document", backref=db.backref("parent", remote_side="Document.id"), lazy="select")
