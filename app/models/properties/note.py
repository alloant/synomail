from datetime import date

from flask import flash

from sqlalchemy import case, and_, or_, not_, select, type_coerce, literal_column, func, union
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from app import db
#from ..file import File
from ..user import User

class NoteProp(object):
    @hybrid_property
    def date(self):
        dt = self.n_date
        for file in self.files:
            dt = file.date if dt < file.date else dt

        return dt

    @date.expression
    def date(cls):
        return cls.n_date
    
    """
    @date.expression
    def date(cls):
        return case(
            (func.count(select(File.id).where(File.note_id==cls.id).scalar_subquery())==0,cls.n_date),
            else_=func.max(select(File.date).where(File.note_id==cls.id).scalar_subquery(),cls.n_date)
        )
    """

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
            (literal_column(fr"sender_user.u_groups regexp '\\bcr\\b'"),'out'),
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
    def user_can_see(cls,user,reg):
        rg = reg.split('_')
        cond = [case((cls.permanent,'per' in user.groups),else_=True)]
        
        if rg[0] == 'box':
            cond.append(cls.state==1)
            cond.append(cls.reg!='min')
        elif rg[0] == 'des':
            cond.append(cls.state>1)
            cond.append(cls.state<4)
            cond.append(cls.reg!='min')
        elif rg[0] == 'pen':
            cond.append(cls.reg!='min')
            cond.append(cls.state>3)
            cond.append(or_(and_(cls.state==0,literal_column(f"sender_user.alias = 'user.alias'")),literal_column(f"receiver_user.alias = '{user.alias}'")))
        else:
            if rg[0] == 'cl':
                cond.append(or_(cls.state>3,cls.sender_id==user.id))
                cond.append(cls.reg=='ctr')
                if rg[1] == 'out': #it is a note from ctr to cg
                    cond.append(literal_column(f"sender_user.alias = '{rg[2]}'"))
                else:
                    cond.append(literal_column(f"receiver_user.alias = '{rg[2]}'"))
            elif rg[0] == 'min':
                cond.append(cls.reg=='min')
                cond.append(or_(literal_column(f"sender_user.alias = '{user.alias}'"),cls.received_by.contains(user.alias)))
                #cond.append(or_(literal_column(f"sender_user.alias = '{user.alias}'"),literal_column(f"receiver_user.alias = '{user.alias}'")))
            else:
                cond.append(or_(cls.state>3,cls.sender_id==user.id))
                if rg[1] != 'all':
                    cond.append(cls.reg==rg[2])
                    cond.append(cls.flow==rg[1])

        return and_(*cond)

    @property
    def note_folder(self):
        folder = self.fullkey.split("/")[0]
        
        name,num = folder.split(" ")
        num = f"0000{num}"[-4:]
        if self.reg == 'min':
            return f"Minuta_{num}"
        else:
            return f"{name}_{num}"
    
    @property
    def path_note(self):
        return f"{self.path}/{self.note_folder}"

        if self.reg == 'min':
            return f"{self.path}/{self.year}/{self.note_folder}"
            return f"/team-folders/Data/Minutas/{self.sender.alias}/Minutas/{self.year}/{self.note_folder}"
        else:
            return f"{self.path}/{self.year}/{self.note_folder}"
            return f"/team-folders/Data/Notes/{self.year}/{self.reg} {self.flow}/{self.note_folder}"
    
    @property
    def path_parent(self):
        if self.reg == 'min':
            return f"{self.path}/{self.year}"
            return f"/team-folders/Data/Minutas/{self.sender.alias}/Minutas/{self.year}"
        else:
            #return f"{self.path}/{self.year}/"
            return f"/team-folders/Data/Notes/{self.year}/{self.reg} {self.flow}"


    def is_read(self,user):
        if isinstance(user,str): # This is a ctr or des
            alias = user if user[:4] == 'des_' else user.split('_')[2]
            return alias in self.read_by.split(",")

        if user.date > self.n_date:
            return not user.alias in self.read_by.split(",")
        else:
            return user.alias in self.read_by.split(",")


    def is_involve(self,user):
        return user in self.receiver

    def rel_flow(self,reg):
        rg = reg.split('_')

        if rg[0] == 'cl':
            return 'in' if self.flow == 'out' else 'out'
        else:
            return self.flow

    def is_bold(self,reg,user):
        flow = 'out' if '_ctr_' in reg else 'in'
        
        if self.flow == flow:
            return not self.is_read(user)
        else:
            return self.state == 0

    def updateRead(self,user):
        rb = self.read_by.split(',') if self.read_by else []
        alias = user if isinstance(user,str) else user.alias

        if alias in rb:
            rb.remove(alias)
            inc = -1
        else:
            rb.append(alias)
            inc = 1
        
        self.read_by = ",".join(rb)
        return inc

    def updateState(self,reg,user,again=False):
        rg = reg.split("_")
        if rg[0] == 'box': # Is the scr getting mail from cg, asr, ctr or r
            # Here we move to Archive and if the move is succesful we put state 2
            self.state = 2
        elif rg[0] == 'des': # Here states are only 2 or 3
            self.state += self.updateRead(f"des_{user.alias}")
        elif self.reg in ['cg','asr','r','ctr']: #Here the states could be 4-6
            if self.rel_flow(reg) == 'in':
                if self.state < 6:
                    self.state += 1
                else:
                    self.state -= 1
            else: # Is out. Only to pass from 0 to 1
                if self.state == 0:
                    self.state = 1
                elif self.state == 1:
                    self.state = 0
        elif self.reg == 'min': #Minuta is different for sender and the rest
            if self.sender == user:
                if self.state == 0:
                    self.receiver.sort(reverse=True)
                    if len(self.receiver) > 0:
                        self.received_by = f"{self.receiver[0].alias}"
                    self.state = 4
                elif self.state == 4:
                    self.state = 0
                elif self.state == 2:
                    if again:
                        self.state = 4
                        self.read_by = self.sender.alias
                    else:
                        self.state = 6
            else:
                rb = self.read_by.split('_') if self.read_by != '' else []
                rb.append(user.alias)
                self.read_by = ",".join(rb)
                self.receiver.sort(reverse=True)
                has_next = False
                for rec in self.receiver:
                    if not rec.alias in rb:
                        self.received_by += f",{rec.alias}"
                        has_next = True
                        break
                
                if not has_next:
                    self.state = 2

