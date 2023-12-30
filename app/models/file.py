from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from .properties.file import FileProp
from .nas.file import FileNas
from app import db


class File(FileProp,FileNas,db.Model):
    __tablename__ = 'file'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, default=datetime.utcnow())
    path: Mapped[str] = mapped_column(db.String(150), default = '')
    permanent_link: Mapped[str] = mapped_column(db.String(150), default = '')
    note_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('note.id'))
    
    note: Mapped["Note"] = relationship(back_populates="files")
   

    def __repr__(self):
        return f'<File "{self.name}">'

    def __str__(self):
        return self.name

