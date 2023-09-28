from app import db
from datetime import datetime

from app.models.nas.file import FileNas

class File(FileNas,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow())
    path = db.Column(db.String(150), default = '')
    permanent_link = db.Column(db.String(150), default = '')
    
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'))
   
    @property
    def name(self):
        return self.path.split("/")[-1]

    @property
    def type(self):
        if len(self.name.split(".")) == 1:
            return 'folder'
        elif self.name.split(".")[1] in ['odoc','osheet','oslide']:
            return 'synology'
        else:
            return 'file'
    
    @property
    def ext(self):
        if self.type == 'folder':
            return ""
        else:
            return self.name.split(".")[-1]

    def __repr__(self):
        return f'<File "{self.name}">'

    def __str__(self):
        return self.name

    
    @property
    def chain_link(self):
        if self.type == 'synology':
            return 'oo/r'
        else:
            return 'd/f'

    def getLinkSheet(self,text = None):
        link_text = text if text else self.name
        return f'=HYPERLINK("#dlink=/{self.chain_link}/{self.permanent_link}", "{link_text}")'

    def getLinkMessage(self,text = None):
        link_text = text if text else self.name
        return f'<https://nas.prome.sg:5001/{self.chain_link}/{self.permanent_link}|{link_text}>'

