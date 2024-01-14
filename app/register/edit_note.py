#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, redirect, session
from flask_login import current_user

from sqlalchemy import select
from sqlalchemy.orm import aliased

from app import db
from app.models import Note, User
from app.forms.note import NoteForm


def edit_note_view(request):
    page = request.args.get('page',1,type=int)
    
    note_id = request.args.get('note')
    #sender = aliased(User,name="sender_user")
    #note = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.id==note_id)).first()
    note = db.session.scalars(select(Note).where(Note.id==note_id)).first()
    
    form = NoteForm(request.form,obj=note)
    form.sender.choices = [note.sender]

    if note.flow == 'in' or note.reg == 'min':
        form.receiver.choices = [(user.alias,user.fullName) for user in db.session.scalars(select(User).where(User.u_groups.regexp_match(r'\bcr\b')).order_by(User.alias)).all()]
    else:
        form.receiver.choices = [(user.alias,user.fullName) for user in db.session.scalars(select(User).where(User.u_groups.regexp_match(fr'\b{note.reg}\b')).order_by(User.alias)).all()]
    
    
    if request.method == 'POST' and form.validate():
        error = False
        note.n_date = form.n_date.data
        note.year = form.year.data
        note.content = form.content.data
        note.content_jp = form.content_jp.data
        note.comments = form.comments.data
        note.proc = form.proc.data
        note.permanent = form.permanent.data
        #note.sender = form.sender.data
       
        for n,user in enumerate(reversed(note.receiver)):
            if not user.alias in form.receiver.data:
                note.receiver.remove(user)

        
        for user in form.receiver.data:
            rec = db.session.scalars(select(User).where(User.alias==user)).first()
            if not rec in note.receiver:
                note.receiver.append(rec)
        

        for ref in form.ref.data.split(","):
            if form.ref.data == "": break
            sender = aliased(User,name="sender_user")
            nr = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.fullkey==ref.strip())).first()
            if nr:
                note.ref.append(nr)
            else:
                flash(f"Note {ref} doesn't exist")
                error = True
        
        db.session.commit()
        
        if not error:
            return redirect(session['lasturl'])
    
    else:
        form.ref.data = ",".join([r.fullkey for r in note.ref]) if note.ref else "" 
        for rec in note.receiver:
            form.receiver.data.append(rec.alias)
        form.permanent.data = note.permanent
    
    return render_template('register/note_form.html', form=form, note=note, user=current_user)

