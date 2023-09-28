from app import db
from datetime import datetime

from sqlalchemy import and_, select, func, case
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from app.models.file import File


class NoteNas(object): 
    @property
    def message(self):
        message = f"Content: `{self.content}` \nLink: {self.messageLink()} \nAssigned to: *{self.dept}*"
        
        if self.ref != '':
            message += f"\nRef: _{self.ref}_"
        
        if self.comments != '':
            message += f"\nComment: _{self.comments}_"
 
        message +=  f"\nRegistry date: {self.date}"

        return message
    
    def addFile(self,file):
        self.files.append(file)

    def addFile_old(self,file):
        rst = file.copy(f"{self.path_note()}")
        print(rst) 
        if rst:
            if 'success' in rst:
                if 'permanent_link' in rst['data']:
                    self.files.append(File(name=file.name,path=self.path_note(),type=file.type,permanent_link=rst['data']['permanent_link']))
                else:
                    self.files.append(File(name=file.name,path=self.path_note(),type=file.type,permanent_link=rst['data']['link_id']))

    def sheetLink(self,text):
        if self.permanent_link:
            return f'=HYPERLINK("#dlink=/d/f/{self.permanent_link}", "{text}")'
        else:
            if self.files:
                return self.files[0].getLinkSheet(text)
            else:
                return ''

    def messageLink(self):
        if self.type == 'cg':
            text = f"{self.no}/{str(self.year)[2:]}"
        elif self.type == 'asr':
            text = f"asr {self.no}/{str(self.year)[2:]}"
        else:
            text = f"{self.source} {self.no}/{str(self.year)[2:]}"
        
        if self.permanent_link:
            return f'<https://nas.prome.sg:5001/d/f/{self.permanent_link}|{text}>'
        else:
            return self.files[0].getLinkMessage(text)

    def move(self,dest):
        logging.info(f"Moving {self.key} to {dest}")
        if self.folder_id:
            rst = move_path(self.folder_id,dest)
            if rst: 
                self.folder_path = f"{dest}/{Path(self.folder_path).stem}"
                self.folder_id = rst['id']
                return True
        else:
            cont = 0
            for file in self.files:
                cont += 1 if file.move(dest) else 0
            
            if cont == len(self.files):
                return True
            else:
                return False

    def copy(self,dest):
        logging.info(f"Copying {self.key} to {dest}")
        if self.folder_path:
            rst = copy_path(self.folder_path,f"{dest}/{Path(self.folder_path).stem}")
            if rst:
                return True
        else:
            cont = 0
            for file in self.files:
                cont += 1 if file.copy(dest) else 0
            
            if cont == len(self.files):
                return True
            else:
                return False


    def organice_files_to_despacho(self,path_dest,path_originals):
        key = self.get_key(full=True)
        #Change names of files
        if self.register == 'cr':
            for i,file in enumerate(self.files):
                if i == 0:
                    old_name = Path(file.name).stem
                    if self.source == 'r': key = f"r_{key}"
                    new_name = f"{key}.{file.ext}" if self.isref == 0 else f"{key}_ref.{file.ext}" 
                else:
                    new_name = f"{file.name.replace(old_name,key)}".strip().replace('&','and')

                file.rename(new_name)
        else:
            key = f"{self.register}{key}"

        
        # Moving files to inbox folder
        dest =f"{path_dest}"

        #Create a folder if needed
        if self.of_annex != '':
            rst = create_folder(dest,key)
            if not rst: return None
            dest = f"{dest}/{key}"
            self.folder_id = rst['id']
            self.folder_path = dest
            self.permanent_link = rst['permanent_link']
        
        # Convert the files to Synology office
        if self.flow == 'in' or self.type_from_no == 'ctr':
            for file in self.files:
                if file.ext in EXT:
                    file.convert()

        # Move the files to dest
        for file in self.files:
            file.move(dest,path_originals)


