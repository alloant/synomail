#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import select 
from app import db
from .models.file import File
from .models.note import Note

def change_file_dates():
    from sqlalchemy import select
    files = db.session.scalars(select(File)).all()
    for file in files:
        nt= db.session.scalar(select(Note).where(Note.id==file.note_id))
        file.date = nt.n_date
    db.session.commit()

