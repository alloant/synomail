from app import db
from datetime import datetime, date

from sqlalchemy import case, and_, or_, not_, select, type_coerce, literal_column, func, union
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.sql import text

from app.models.html.note import NoteHtml
from app.models.nas.note import NoteNas
from app.models.file import File
from app.models.user import User

#from app.models.note_nas import NoteNas
note_ref = db.Table('note_ref',
                db.Column('note_id', db.Integer, db.ForeignKey('note.id')),
                db.Column('ref_id', db.Integer, db.ForeignKey('note.id'))
                )

note_receiver = db.Table('note_receiver',
                db.Column('note_id', db.Integer, db.ForeignKey('note.id')),
                db.Column('receiver_id', db.Integer, db.ForeignKey('user.id'))
                )

class Note(NoteHtml,NoteNas,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer, default = 0)
    year = db.Column(db.Integer, default = datetime.utcnow().year)
    
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship("User", foreign_keys=[sender_id])

    receiver = db.relationship('User', secondary=note_receiver, backref='rec_notes')
    n_date = db.Column(db.Date, default=datetime.utcnow())
    content = db.Column(db.Text, default = '')
    proc = db.Column(db.String(15), default = '')
    ref = db.relationship('Note', secondary=note_ref, primaryjoin=note_ref.c.note_id==id, secondaryjoin=note_ref.c.ref_id==id, backref='notes') 
    permanent_link = db.Column(db.String(150), default = '')
    
    permanent = db.Column(db.Boolean, default=False)
    
    reg = db.Column(db.String(15), default = '')
    n_groups = db.Column(db.String(15), default = '')

    done = db.Column(db.Boolean, default=False)
    state = db.Column(db.Integer, default = 0)
    received_by = db.Column(db.String(150), default = '')
    read_by = db.Column(db.String(150), default = '')

    files = db.relationship('File', backref='Note')

    @hybrid_property
    def date(self):
        dt = self.n_date
        for file in self.files:
            dt = file.date if dt < file.date else dt

        return dt
    
    @date.expression
    def date(cls):
        return case(
            (func.count(select(File.id).where(File.note_id==cls.id).scalar_subquery())==0,cls.n_date),
            else_=func.max(select(File.date).where(File.note_id==cls.id).scalar_subquery(),cls.n_date)
            #else_=func.max(db.union(select(cls.n_date),select(File.date).where(File.note_id==cls.id)).scalar_subquery())
        )


    @property
    def groups(self):
        return self.n_groups.split(',')
    
    @property
    def receivers(self):
        return ",".join([rec.alias for rec in self.receiver])

    @property
    def key(self):
        return self.keyto()

    def keyto(self,keyto=False):
        if self.flow == 'in':
            return f"{self.sender.alias} {self.num}"
        elif 'cg' == self.reg:
            return f"Aes {self.num}"
        elif 'asr' == self.reg:
            return f"cr-asr {self.num}"
        elif 'r' == self.reg:
            if len(self.receiver) != 1 or not keyto:
                return f"Aes-r {self.num}"
            else:
                return f"Aes-{self.receiver[0].alias} {self.num}"
        elif 'ctr' == self.reg:
            if len(self.receiver) != 1 or not keyto:
                return f"cr {self.num}"
            else:
                return f"cr-{self.receiver[0].alias} {self.num}"
        elif 'min' == self.reg:
            return f"Minuta-{self.sender.alias} {self.num}"

    @property
    def fullkeyto(self):
        return f"{self.keyto(True)}/{str(self.year)[-2:]}"

    @hybrid_property
    def fullkey(self):
        return f"{self.keyto()}/{str(self.year)[-2:]}"

    @fullkey.expression
    def fullkey(cls):
        return case(
            (cls.flow=='in', literal_column("sender_user.alias") + " " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "cg", "Aes " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "asr", "cr-asr " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "ctr", "cr " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg.contains(","), "Aes-r " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "r", "Aes-r" + " " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            else_="",
        )
    
    @hybrid_property
    def flow(self) -> str:
        return 'out' if any(map(lambda v: v in self.sender.groups, ['cr'])) else 'in'

    @flow.expression
    def flow(cls):
        return case(
            (literal_column(fr"sender_user.u_groups regexp '\bcr\b'"),'out'),
            else_='in'
        )
    
    @hybrid_method
    def user_can_see(self, user: User,reg: str) -> bool:
        if 'per' in self.groups:
            return True if 'per' in user.groups else False
        elif self.reg in ['cg','asr','r']:
            return True if 'cr' in user.groups else False
        elif self.reg == 'ctr':
            if 'cr' in user.groups: return True
            if 'cl' in user.groups:
                ctr = user.alias.split(' ')[1]
                for senrec in [self.sender] + self.receiver:
                    if senrec.alias == ctr: return True
        
        return False

    @user_can_see.expression
    def user_can_see(cls, user: User, reg: str):
        rg = reg.split('_')
        if rg[0] == 'des':
            return and_(cls.flow == rg[1],cls.state < 3, cls.state > 0)
        elif rg[0] == 'cl':
            if f"cl_{rg[2]}" in user.groups:
                return case(
                    (cls.permanent,'per' in user.groups),
                    (and_(cls.state<3,cls.flow=='out'),False),
                    (literal_column(f"sender_user.alias = '{rg[2]}'"), True),
                    (literal_column(f"receiver_user.alias = '{rg[2]}'"), True),
                    else_=False,
                )
        elif 'cr' in user.groups: # is a member of cr
            return case(
                (cls.permanent,'per' in user.groups),
                (literal_column(f"sender_user.alias = '{user.alias}'"),True),
                (cls.state>=3,True),
                else_=False
            )
        
        return False


    def __repr__(self):
        return f'<{self.fullkeyto} "{self.content}">'

    def __str__(self):
         return self.fullkeyto

    def __eq__(self,other):
        if isinstance(other,Note):
            if self.fullkey == other.fullkey:
                return True

        return False
    
    @property
    def note_folder(self):
        folder = self.fullkey.split("/")[0]
        
        name,num = folder.split(" ")
        num = f"0000{num}"[-4:]
        if self.reg == 'min':
            return f"Minuta_{num}"
        else:
            return f"{name}_{num}"

    def path_note(self):
        if self.reg == 'min':
            return f"/team-folders/Data/Minutas/{self.sender.alias}/Minutas/{self.year}/{self.note_folder}"
        else:
            return f"/team-folders/Data/Notes/{self.year}/{self.reg} {self.flow}/{self.note_folder}"

    def is_read(self,user):
        return user.alias in self.read_by.split(",") or user.date > self.n_date

    def is_bold(self,reg,user):
        flow = 'out' if '_ctr_' in reg else 'in'
        
        if self.flow == flow:
            return not self.is_read(user)
        else:
            return self.state == 0



