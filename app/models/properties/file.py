import re
from datetime import date

from sqlalchemy import select

from app import db
from app.models.user import User

class FileProp(object):
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

    @property
    def guess_number(self):
        if ";" in self.subject:
            temp = self.subject.split(";")[0]
            if "/" in temp:
                temp = re.findall(r'\d+',temp)
                if len(temp) > 1:
                    return f"{int(temp[0])}/{int(temp[1])}"

        temp = re.findall(r'\d+',self.path.split('/')[-1])
        
        if temp:
            return f"{int(temp[0])}/{date.today().year-2000}"

    def guess_fullkey(self,key = None):
        sender = db.session.scalar(select(User).where(User.email==self.sender))
        if sender:
            prot = sender.alias
        else:
            return ""

        if key:
            return f"{prot} {key}"

        if ";" in self.subject:
            temp = self.subject.split(";")[0]
            if "/" in temp:
                temp = re.findall(r'\d+',temp)
                if len(temp) > 1:
                    return f"{prot} {temp[0]}/{temp[1]}"

        temp = re.findall(r'\d+',self.path.split('/')[-1])
        
        if temp:
            return f"{prot} {temp[0]}/{date.today().year-2000}"

    @property
    def guess_content(self):
        if ";" in self.subject:
            temp = self.subject.split(";")
            if "/" in temp[0]:
                num = re.findall(r'\d+',temp[0])
                if len(num) > 1 and temp[1] != '_':
                    return temp[1]

        return ""
    
    @property
    def guess_ref(self):
        ids = []
        if ";" in self.subject:
            temp = self.subject.split(";")
            if len(temp) < 3:
                return ""

            if "/" in temp[0]:
                num = re.findall(r'\d+',temp[0])
                if len(num) > 1 and temp[1] != '_':
                    refs = temp[2]
                    for ref in refs.split(","):
                        rf = ref.replace(" ","")
                        n = re.findall(r'\d+',rf)
                        r = re.findall(r'\D+',rf)
                        tid = None
                        if len(r) == 1: # only / is there, it is from cg
                            tid = get_note_id(f"cg {n[0]}/{n[1]}")
                        else:
                            sd = r[0].split("-")[0]
                            rst = db.session.scalar(select(User).where(User.alias==sd))
                            if rst:
                                tid = get_note_id(f"{sd} {n[0]}/{n[1]}")
                        
                        if tid:
                            ids.append(tid)

        return ids

