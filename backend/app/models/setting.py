from .base import db

class NodeSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    node_type = db.Column(db.String, nullable=False)
    node_id = db.Column(db.Integer, nullable=False)
    label_visible = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (db.UniqueConstraint('node_type', 'node_id', name='_node_setting_uc'),)

    def __repr__(self):
        return f'<NodeSetting {self.node_type}-{self.node_id}>'
