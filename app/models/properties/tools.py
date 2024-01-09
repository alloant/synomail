#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.models.note import Note
from app.models.user import User
from app import db

def get_note_id(fullkey):
    sender = aliased(User,name="sender_user")
    nt = db.session.scalar(select(Note).join(Note.sender.of_type(sender)).where(Note.fullkey==fullkey))

    return nt.fullkey,nt.id if nt else None
