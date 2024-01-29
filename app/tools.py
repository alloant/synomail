#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import select 
from app import db
from app.models import File, Note
from app.models.nas.nas import files_path, copy_path

def change_file_dates():
    files = db.session.scalars(select(File)).all()
    for file in files:
        print(file.id)
        nt= db.session.scalar(select(Note).where(Note.id==file.note_id))
        if nt:
            file.date = nt.n_date
    db.session.commit()

def find_files():
    year = 2023
    flow = 'out'
    notes = db.session.scalars(select(Note).where(Note.files==None,Note.year==year,Note.flow==flow))
    
    regs = ['cg','asr','ctr','r']
    regs = ['ctr']
    only_update = False

    for reg in regs:
        files_cg = files_path(f"/team-folders/Archive/{reg} {flow} {year}")
        
        for note in notes:
            if note.reg == reg:
                for file in files_cg:
                    if only_update: break
                    print(note.note_folder,file['path'])
                    if note.note_folder in file['path']:
                        if file['content_type'] == 'dir':
                            files_temp = files_path(f"/team-folders/Archive{file['path']}")
                            if not files_temp:
                                continue
                            for tfile in files_temp:
                                copy_path(f"/team-folders/Archive{tfile['path']}",f'/team-folders/Data/Notes/{year}/{reg} {flow}/{note.note_folder}/{tfile["path"].split("/")[-1]}')
                        else:
                            copy_path(f"/team-folders/Archive{file['path']}",f'/team-folders/Data/Notes/{year}/{reg} {flow}/{note.note_folder}/{file["path"].split("/")[-1]}')
            
                note.updateFiles()

    change_file_dates()
