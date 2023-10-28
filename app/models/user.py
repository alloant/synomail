# models.py

from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    password = db.Column(db.String(100), default='')
    password_nas = db.Column(db.String(100), default='')

    date = db.Column(db.Date, default=datetime.utcnow())
    name = db.Column(db.String(200), default='')
    alias = db.Column(db.String(20), unique=True)
    u_groups = db.Column(db.String(200), default=False)
    order = db.Column(db.Integer, default=0)

    email = db.Column(db.String(200), default='')
    description = db.Column(db.String(200), default='')
    
    local_path = db.Column(db.String(200), default='')
    
    active = db.Column(db.Boolean, default=True)
    admin_active = db.Column(db.Boolean, default=False)

    #notes = db.relationship('Note', backref='sender')

    def __repr__(self):
        return self.alias
    
    def __lt__(self,other):
        return self.order < other.order

    def __gt__(self,other):
        return self.order > other.order

    @property
    def groups(self):
        return self.u_groups.split(',') if self.u_groups else []

    @property
    def admin(self):
        if 'admin' in self.groups and self.admin_active:
            return True
        return False

    @property
    def fullName(self):
        rst = f"{self.alias}"
        if self.name: rst = f"{rst} - {self.name}"
        if self.description: rst = f"{rst} ({self.description})"

        return rst
