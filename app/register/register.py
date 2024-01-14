#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import render_template, url_for, session, redirect
from flask_login import current_user

from sqlalchemy import select, and_, or_, literal_column
from sqlalchemy.orm import aliased

from app import db
from app.models import Note, User
from app.mail import send_email

from .tools import view_title, newNote

def register_filter(rg):
    fn = []
    if rg[0] in ['cr','pen']: # Register for cr or pendings
        if not 'permanente' in current_user.groups:
            fn.append(Note.permanent==False)
        fn.append(Note.reg!='min') # No minutas
        if rg[0] == 'cr':
            fn.append(Note.reg==rg[2]) # Type reg (cg,asr,r,ctr) 
            fn.append(Note.flow==rg[1]) # Flow is in/out
            fn.append(or_(Note.state>=5,Note.sender==current_user)) # Only notes after desacho or already sent unless I am the sender
        else: # Then we are in pendings
            if not session['showAll']:
                fn.append(Note.state < 6)
            fn.append(or_(Note.sender==current_user,Note.receiver.contains(current_user)))
    elif rg[0] == 'cl': # The register of a center
        ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
        fn.append(Note.reg!='min') # No minutas
        if rg[1] == 'in': # show notes to the ctr. Flow==out for database
            fn.append(Note.receiver.contains(ctr))
            fn.append(Note.state>=5)
        else:
            fn.append(Note.sender==ctr)
    elif rg[0] == 'min':
        fn.append(Note.reg=='min')
        fn.append(or_(Note.sender==current_user,Note.receiver.contains(current_user)))
    elif rg[0] == 'des':
        fn.append(Note.reg!='min')
        fn.append(Note.state>1)
        fn.append(Note.state<4)
    elif rg[0] == 'box':
        fn.append(Note.reg!='min')
        fn.append(Note.flow=='out')
        fn.append(Note.state==1)

    # Find filter in fullkey, sender, receivers or content
    if 'filter_notes' in session:
        fuser = db.session.scalar(select(User).where(User.alias == session['filter_notes']))
        ofn = [
            Note.fullkey.contains(session['filter_notes']),
            Note.content.contains(session["filter_notes"])
        ]
    
        if fuser:
            ofn.append(Note.sender == fuser)
            ofn.append(Note.receiver.contains(fuser))
        
        fn.append(or_(*ofn))

    return fn

def register_actions(output,args): # Actions like new note, update read/state, update files...
    note = args.get('note')
    reg = args.get('reg')
    page = args.get('page')
    rg = reg.split("_")

    # If the note was mark read
    read_id = args.get('read')
    if read_id:
        nt = db.session.scalar(select(Note).where(Note.id==read_id))
        nt.updateRead(current_user)
        return "read"

    # If the state of the note has change
    state_id = args.get('state')
    if state_id:
        nt = db.session.scalar(select(Note).where(Note.id==state_id))
        nt.updateState(reg,current_user)
        return "read"
  
    if "newout" in output:
        newNote(current_user,reg)
    elif "addfiles" in output:
        nt = db.session.scalar(select(Note).where(Note.id==output['addfiles']))
        nt.updateFiles()
    elif 'sendmail' in output:
        tosendnotes = db.session.scalars(select(Note).where(Note.flow=='out',Note.state==1))
        
        for nt in tosendnotes:
            rst = nt.move(f'/team-folders/Data/Notes/{nt.year}/{nt.reg} out')
            
            if not rst:
                continue

            if nt.reg in ['cg','r']: # We have to generate the eml
                rec = ",".join([rec.email for rec in nt.receiver])
                path = f"{current_user.local_path}/Outbox"
                write_eml(rec,nt,path)
                nt.state = 6

            if nt.reg == 'asr': # Note for asr. We just copy it to the right folder
                nt.copy('/team-folders/Data/Mail/Mail asr/Outbox')
                nt.state = 6
            
            if nt.reg == 'ctr': # note for a ctr. We just change the state
                nt.state = 6
                for rec in nt.receiver:
                    if rec.email:
                        send_email(f"New mail for {rec.alias}. {nt.comments}","",rec.email)

            db.session.commit()

    if not "notes_filer" in output and not page:
        session['filter_notes'] = ""
    
def register_view(output,args): # Use for all register in/out for cr and ctr, for pendings, for despacho and for outbox
    note = args.get('note')
    reg = args.get('reg')
    rg = reg.split("_") 

    # Sending to last url
    if reg == 'lasturl':
        return redirect(session['lasturl'])

    # Init this value if needed
    if not "filter_notes" in session:
        session["filter_notes"] = ""
    
    if not "showAll" in session:
        session["showAll"] = False
 
    # Security check for error and users without authority
    rdct = False
        
    if 'cr' in current_user.groups:
        if rg[0] == 'des' and not 'despacho' in current_user.groups:
            rdct = True
        
        if rg[0] == 'box' and not 'scr' in current_user.groups:
            rdct = True

        if rdct: 
            return redirect(url_for('register.register', reg='pen_in_', page=1))
    else:
        if rg[0] in ['cr','min','box','des']:
            rdct = True
        
        if not f"cl_{rg[2]}" in current_user.groups:
            rdct = True

        if rdct:
            for gp in current_user.groups:
                if gp[:3] == 'cl_':
                    break
            
            return redirect(url_for('register.register', reg=gp.replace("_","_in_"), page=1))
    
    # Actions
    register_actions(output,args)

    # First check the filter
    if "notes_filter" in output: 
        session['filter_notes'] = output['notes_filter']
        
        if output['notes_filter'] == "":
            if session['showAll']:
                session['showAll'] = False

    if "showAll" in output:
        session['showAll'] = output['showAll']


    fn = register_filter(rg)
    page = args.get('page', 1, type=int)
    sender = aliased(User,name="sender_user")
    sql = select(Note).join(Note.sender.of_type(sender))
    sql = sql.where(and_(*fn)).group_by(Note.id).order_by(Note.date.desc(), Note.num.desc())
    
    temp = db.session.scalars(sql).all()
    print(len(temp),'!!!!!!!!!!!!!!!')

    notes = db.paginate(sql, per_page=30)
    
    prev_url = url_for('register.register', reg=reg, page=notes.prev_num) if notes.has_prev else None
    next_url = url_for('register.register', reg=reg, page=notes.next_num) if notes.has_next else None
    
    session['lasturl'] = url_for('register.register',reg=reg,page=page)
    return render_template('register/main.html',title=view_title(reg,note), notes=notes, reg=reg, page=page, prev_url=prev_url, next_url=next_url, user=current_user)


