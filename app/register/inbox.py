#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from datetime import date

from flask import render_template 
from flask_login import current_user

from sqlalchemy import select, and_
from sqlalchemy.orm import aliased

from app import db
from app.models import Note, File, User
from app.models.nas.nas import files_path, move_path

def inbox_view(output,args):
    if "importeml" in output:
        # Searching for eml to import
        path = f"{current_user.local_path}/Inbox"
        files = os.listdir(path)
        for file in files:
            if file.split('.')[-1] == 'eml':
                read_eml(f"{path}/{file}")
        
        # Searching for notes in from asr
        asr_files = files_path("/team-folders/Data/Mail/Mail asr")
        for file in asr_files:
            rst = move_path(file['display_path'],"/team-folders/Data/Mail/IN")
            if rst:
                filename = file['display_path'].split("/")[-1]
                path = f"/team-folder/Data/Mail/IN/{filename}"
                link = file['permanent_link']
                if filename.split(".")[-1] in ['xls','xlsx','docx','rtf']:
                    path,fid,link = convert_office(f"/team-folders/Data/Mail/IN/{filename}")
                    move_path(f"/team-folders/Data/Mail/IN/{filename}",f"/team-folders/Data/Mail/IN/Originals")

                fl = File(path=path,permanent_link=link,sender="asr",date=date.today())
            db.session.add(fl)

        # Searching for notes sent by the ctr. reg = ctr, flow = in and state = 1
        sender = aliased(User,name="sender_user")
        notes = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.reg=='ctr',Note.flow=='in',Note.state==1)))
        for note in notes:
            rst = note.move(f"/team-folders/Data/Notes/{note.year}/ctr in/")
            if rst:
                note.state = 2

        db.session.commit()

    elif "notesfromfiles" in output:
        files = db.session.scalars(select(File).where(File.note_id==None))
        involved_notes = []
        for file in files:
            gfk = file.guess_fullkey(output[f"number_{file.id}"])
            if gfk == "":
                continue

            content = output[f"content_{file.id}"]
            sender = aliased(User,name="sender_user")
            nt = db.session.scalar(select(Note).join(Note.sender.of_type(sender)).where(Note.fullkey==gfk))
            if nt:
                file.move_to_note(nt.path_note)
                nt.addFile(file)
                if not nt in involved_notes: involved_notes.append(nt)
            else: # We need to create the note
                num = re.findall(r'\d+',gfk)[0]                
                year = re.findall(r'\d+',gfk)[1]                
                if file.sender == 'cg@cardumen.org':
                    nt = Note(num=num,year=year,sender_id=36,reg='cg',state=2,content=content)
                else:
                    sender = db.session.scalar(select(User).where(User.email==file.sender))
                    nt = Note(num=num,year=year,sender_id=sender.id,reg='r',state=2,content=content)
                
                nt.addFile(file)
                if not nt in involved_notes: involved_notes.append(nt)
                db.session.add(nt)
        
        for note in involved_notes:
            note.updateFiles()

        db.session.commit()


    sql = select(File).where(File.note_id == None)
    page = args.get('page', 1, type=int)
    files = db.paginate(sql, per_page=30)
    prev_url = url_for('register.inbox_scr', page=files.prev_num) if files.has_prev else None
    next_url = url_for('register.inbox_scr', page=files.next_num) if files.has_next else None
    
    return render_template('inbox/main.html',title="Files received from cg and r", files=files, page=page, prev_url=prev_url, next_url=next_url)


