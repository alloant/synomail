from app import db
from pathlib import Path

from .nas import get_info,rename_path, move_path, copy_path, convert_office, download_path, create_folder

class FileNas(object):
    def move_to_note(self,dest):
        rst = move_path(self.path,dest)
        if rst:
            self.path = rst['data']['display_path'].split('/')[-1]

    def move(self,dest,dest_original = None):
        rst = move_path(self.file_id,dest)
        if rst:
            if self.original_name and dest_original:
                move_path(self.original_id,dest_original)
            self.path = dest
            self.file_id = rst['id']
        
        return rst

    def copy(self,dest):
        return copy_path(f"{self.path}/{self.name}",f"{dest}/{self.name}")

    def convert(self):
        self.original_name = self.name
        self.original_id = self.file_id
        
        rst = convert_office(self.file_id)
        
        self.name = rst['name']
        self.file_id = rst['id']
        self.permanent_link = rst['permanent_link']

    def rename(self,new_name):
        rst = rename_path(self.file_id,new_name)

        if rst: self.name = new_name

    def download(self,dest = None):
        return download_path(self.file_id,dest)

