from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app import db

from .user import User
from .properties.note import NoteProp
from .html.note import NoteHtml
from .nas.note import NoteNas

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
        if 'cg' in self.sender.groups or 'r' in self.sender.groups:
            self.path = f"/team-folders/Data/Notes/{int(self.year)+2000}/{self.reg} in"
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
