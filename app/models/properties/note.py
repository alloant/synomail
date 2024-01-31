from datetime import date

from flask import flash, session, current_app

from sqlalchemy import case, and_, or_, not_, select, type_coerce, literal_column, func, union
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from app import db

class NoteProp(object):
    #@hybrid_property
    #def date(self):
    #    return self.n_date

    #@date.expression
    #def date(cls):
    #    return cls.n_date

    @property
    def groups(self):
        return self.n_groups.split(',')
    
    @property
    def receivers(self):
        return ",".join([rec.alias for rec in self.receiver])

    @property
    def key(self):
        return self.keyto()

    def keyto(self,keyto=False,email=False):
        if self.flow == 'in':
            if email and self.sender.alias == 'cg':
                return f"{self.num}"
            else:
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
    def refs(self):
        return ",".join([f"{ref.keyto(True,True)}/{self.year-2000}" for ref in self.ref])

    @property
    def fullkeyto(self):
        return f"{self.keyto(True)}/{str(self.year)[-2:]}"

    @hybrid_property
    def fullkey(self):
        return f"{self.keyto()}/{str(self.year)[-2:]}"
    
    @hybrid_property
    def fullkey2(self):
        return self.sender.alias
        #return f"{self.keyto()}/{str(self.year)[-2:]}"

    @fullkey.expression
    def fullkey(cls):
        """
        return case(
            (cls.flow=='in', cls.alias_sender + " " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "cg", "Aes " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "asr", "cr-asr " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "ctr", "cr " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg.contains(","), "Aes-r " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            (cls.reg == "r", "Aes-r" + " " + cls.num.cast(db.String) + "/" + (cls.year % 100).cast(db.String)),
            else_="",
        )
        """
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
            (cls.sender_id.in_(session['cr']),'out'),
            else_='in'
        )
    
    @hybrid_method
    def is_done(self,user): #Use in state_cl and updateState for cl. We assume note is in for the ctr
        if user in self.received_by.split(','):
            return True
        else:
            return False

    @is_done.expression
    def is_done(cls,alias):
        return not_(cls.received_by.regexp_match(fr'\b{alias}\b'))

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
            return f"{current_app.config['SYNOLOGY_FOLDER_NOTES']}/Minutas/{self.sender.alias}/Minutas/{self.year}/{self.note_folder}"
        else:
            return f"{self.path}/{self.year}/{self.note_folder}"
            return f"{current_app.config['SYNOLOGY_FOLDER_NOTES']}/Notes/{self.year}/{self.reg} {self.flow}/{self.note_folder}"
    

    def is_read(self,user):
        if isinstance(user,str): # This is a ctr or des
            alias = user if user[:4] == 'des_' else user.split('_')[2]
            return alias in self.read_by.split(",")

        if user.date > self.n_date:
            return not user.alias in self.read_by.split(",")
        else:
            return user.alias in self.read_by.split(",")


    def rel_flow(self,reg):
        rg = reg.split('_')

        if rg[0] == 'cl':
            return 'in' if self.flow == 'out' else 'out'
        else:
            return self.flow

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
        db.session.commit()
        return inc

    def updateState(self,reg,user):
        rg = reg.split("_")
        if rg[0] == 'box': # Is the scr getting mail from cg, asr, ctr or r
            # Here we move to Archive and if the move is succesful we put state 2
            self.state = 2
        elif rg[0] == 'des': # Here states are only 2 or 3
            self.state += self.updateRead(f"des_{user.alias}")
        elif rg[0] == 'cl':
            if self.flow == 'out': # Note from cr to the ctr
                if self.is_done(rg[2]):
                    rst = self.received_by.split(",").remove(rg[2])
                    if not rst: rst = ""
                    self.received_by = rst
                else:
                    self.received_by += f",{rg[2]}"
            else:
                if self.state == 0: # sending to cr
                    self.state = 1
                elif self.state == 1: # taking it back before the scr archive it
                    self.state =0
        elif rg[0] in ['cr','pen']: # Here the states could be 4-6
            if self.flow == 'in': # Notes from cg,asr,r,ctr. They could be 5 or 6
                self.state = 6 if self.state == 5 else 5
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
        
        db.session.commit()
