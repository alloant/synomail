#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from flask_login import UserMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship, aliased
from sqlalchemy import select, delete
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from app import db

from .properties.file import FileProp
from .nas.file import FileNas

from .properties.note import NoteProp
from .html.note import NoteHtml
from .nas.note import NoteNas

from .properties.user import UserProp

class File(FileProp,FileNas,db.Model):
    __tablename__ = 'file'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, default=datetime.utcnow())
    subject: Mapped[str] = mapped_column(db.String(150), default = '')
    path: Mapped[str] = mapped_column(db.String(150), default = '')
    permanent_link: Mapped[str] = mapped_column(db.String(150), default = '')
    sender: Mapped[str] = mapped_column(db.String(20), default = '')
    note_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('note.id'),nullable=True)
    
    note: Mapped["Note"] = relationship(back_populates="files")
   

    def __repr__(self):
        return f'<File "{self.name}">'

    def __str__(self):
        return self.name

    def get_user(self,field,value = None):
        if field == 'email':
            return db.session.scalar(select(User).where(User.email==self.sender))
        elif field == 'alias':
            return db.session.scalar(select(User).where(User.alias==value))
        else:
            return None

    def get_note_id(self,fullkey):
        print(fullkey,'!!!!!!!!!!!!')
        sender = aliased(User,name="sender_user")
        nt = db.session.scalar(select(Note).join(Note.sender.of_type(sender)).where(Note.fullkey==fullkey))
        print(nt,'$$$$$$$$$$$$$$')
        return nt.fullkey,nt.id if nt else None

note_ref = db.Table('note_ref',
                db.Column('note_id', db.Integer, db.ForeignKey('note.id')),
                db.Column('ref_id', db.Integer, db.ForeignKey('note.id'))
                )

note_receiver = db.Table('note_receiver',
                db.Column('note_id', db.Integer, db.ForeignKey('note.id')),
                db.Column('receiver_id', db.Integer, db.ForeignKey('user.id'))
                )

class Note(NoteProp,NoteHtml,NoteNas,db.Model):
    __tablename__ = 'note'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    num: Mapped[int] = mapped_column(db.Integer, default = 0)
    year: Mapped[int] = mapped_column(db.Integer, default = datetime.utcnow().year)
    
    sender_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user.id'))
    sender: Mapped["User"] = relationship(back_populates="outbox")

    receiver: Mapped[list["User"]] = relationship('User', secondary=note_receiver, backref='rec_notes')
    
    n_date: Mapped[datetime.date] = mapped_column(db.Date, default=datetime.utcnow())
    content: Mapped[str] = mapped_column(db.Text, default = '')
    content_jp: Mapped[str] = mapped_column(db.Text, default = '')
    proc: Mapped[int] = mapped_column(db.String(50), default = '')
    ref: Mapped[list["Note"]] = relationship('Note', secondary=note_ref, primaryjoin=note_ref.c.note_id==id, secondaryjoin=note_ref.c.ref_id==id, backref='notes') 
    path: Mapped[str] = mapped_column(db.String(150), default = '')
    permanent_link: Mapped[str] = mapped_column(db.String(150), default = '')
    comments: Mapped[str] = mapped_column(db.Text, default = '')
    
    permanent: Mapped[bool] = mapped_column(db.Boolean, default=False)
    
    reg: Mapped[str] = mapped_column(db.String(15), default = '')
    n_groups: Mapped[str] = mapped_column(db.String(15), default = '')

    done: Mapped[bool] = mapped_column(db.Boolean, default=False)
    state: Mapped[int] = mapped_column(db.Integer, default = 0)
    received_by: Mapped[str] = mapped_column(db.String(150), default = '')
    read_by: Mapped[str] = mapped_column(db.String(150), default = '')

    files: Mapped[list["File"]] = relationship(back_populates="note")

    def __init__(self, *args, **kwargs):
        super(Note,self).__init__(*args, **kwargs)
        self.sender = db.session.scalar(select(User).where(User.id==self.sender_id))  
        
        folder = self.sender.alias
        if self.sender.alias in ['cg','asr'] or 'r' in self.sender.groups:
            self.path = f"/team-folders/Data/Notes/{self.year}/{self.reg} in"
        elif self.reg == 'min':
            self.path = f"/team-folders/Data/Minutas/{folder}/Minutas/{datetime.now().year}"
        else:
            self.path = f"/team-folders/Data/Minutas/{folder}/Notes"

        rst = self.create_folder()

    def __repr__(self):
        return f'<{self.fullkeyto} "{self.content}">'

    def __str__(self):
         return self.fullkeyto

    def __eq__(self,other):
        if isinstance(other,Note):
            if self.fullkey == other.fullkey:
                return True

        return False

    def deleteFiles(self,files_id):
        db.session.execute(delete(File).where(File.id.in_(files_id)))

    def addFileArgs(self,*args,**kargs):
        print('HERERER')
        self.addFile(File(**kargs))

    @hybrid_property
    def alias_sender(self):
        return self.sender.alias

    @alias_sender.expression
    def alias_sender(cls):
        alsend = db.session.scalar(select(User.alias).where(User.id==cls.sender_id))
        return alsend
        return select(User.alias).where(User.id==cls.sender_id)
    
class User(UserProp,UserMixin, db.Model):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    password: Mapped[str] = mapped_column(db.String(500), default='')
    password_nas: Mapped[str] = mapped_column(db.String(500), default='')

    date: Mapped[datetime.date] = mapped_column(db.Date, default=datetime.utcnow())
    name: Mapped[str] = mapped_column(db.String(200), default='')
    alias: Mapped[str] = mapped_column(db.String(20), unique=True)
    u_groups: Mapped[str] = mapped_column(db.String(200), default=False)
    order: Mapped[str] = mapped_column(db.Integer, default=0)

    email: Mapped[str] = mapped_column(db.String(200), default='')
    description: Mapped[str] = mapped_column(db.String(200), default='')
    
    local_path: Mapped[str] = mapped_column(db.String(200), default='')
    
    active: Mapped[str] = mapped_column(db.Boolean, default=True)
    admin_active: Mapped[str] = mapped_column(db.Boolean, default=False)

    outbox: Mapped[list["Note"]] = relationship(back_populates="sender")

    def __repr__(self):
        return self.alias
    
    def __lt__(self,other):
        return self.order < other.order

    def __gt__(self,other):
        return self.order > other.order
