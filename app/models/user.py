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

    email = db.Column(db.String(200), default='')
    
    active = db.Column(db.Boolean, default=True)
    admin_active = db.Column(db.Boolean, default=False)

    #notes = db.relationship('Note', backref='sender')

    def __repr__(self):
        return self.alias

    @property
    def groups(self):
        return self.u_groups.split(',') if self.u_groups else []

    @property
    def admin(self):
        if 'admin' in self.groups and self.admin_active:
            return True
        return False

