# main.py
from datetime import datetime
import re

from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func, not_, select, literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.sql import text

from wtforms import SelectField

from docx import Document
from tempfile import NamedTemporaryFile

from app import db
from app.models.user import User
from app.models.note import Note
from app.models.file import File

from app.models.nas.nas import create_folder, upload_path, convert_office, files_path, get_info

from app.forms.note import NoteForm

bp = Blueprint('register', __name__)

filter_notes = ""
lasturl = ""

def newNote(user,reg,ref = None):
    rg = reg.split('_')
    # Get new number for the note. Here getting the las number in that register
    sender = aliased(User,name="sender_user")
    if rg[0] == 'min':
        num = db.session.scalar( select(func.max(literal_column("num"))).select_from(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.reg=='min',Note.year==datetime.today().year,Note.sender==current_user))) )
    elif rg[0] == 'cl':
        num = db.session.scalar( select(func.max(literal_column("num"))).select_from(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.year==datetime.today().year,User.alias==rg[2],Note.flow=='in'))) )
    else:
        num = db.session.scalar( select(func.max(literal_column("num"))).select_from(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.year==datetime.today().year,Note.reg==rg[2],Note.flow=='out'))) )

    # Now adding +1 to num or start numeration of the year
    if num:
        num += 1
    elif rg[2] == 'cg':
        num = 1
    elif rg[2] == 'asr':
        num = 250
    elif rg[2] == 'ctr':
        num = 1000
    elif rg[2] == 'r':
        num = 2000
    elif rg[0] == 'min':
        num = 1


    # Creating the note. We need to know the register it bellows. This note could have been created by a cr dr or a cl member
    if rg[0] == 'cl': # New note made by a cl member. It's a note for cr from ctr 
        ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
        folder = ctr.alias
        nt = Note(num=num,sender_id=ctr.id,reg='ctr')
    elif rg[0] == 'min':
        folder = user.alias
        nt = Note(num=num,sender_id=user.id,reg=rg[0])
    else: # Note created by a cr dr
        folder = user.alias
        nt = Note(num=num,sender_id=user.id,reg=rg[2])
    
        if rg[2] in ['cg','asr']:
            rec = db.session.scalar(select(User).where(User.alias==rg[2]))
            nt.receiver.append(rec)
    
    if ref:
        for irf in ref.split(","):
            rf = db.session.scalar(select(Note).where(Note.id==irf))
            if rf.reg == 'min':
                for r in rf.ref:
                    nt.ref.append(r)
            else:
                nt.ref.append(rf)

    if rg[0] == 'min':
        nt.path = f"/team-folders/Data/Minutas/{folder}/Minutas/{datetime.now().year}"
    else:
        nt.path = f"/team-folders/Data/Minutas/{folder}/Notes"

    db.session.add(nt)
    rst = db.session.commit()
    
    # Now we create the folder in synology
    sender = aliased(User,name="sender_user")
    sql = select(Note).join(Note.sender.of_type(sender))

    new_note = db.session.scalars(sql.order_by(Note.id.desc())).first()
    
    rst = create_folder(new_note.path,new_note.note_folder)
    
    if rst:
        new_note.permanent_link = rst['permanent_link']
    db.session.add(nt)
    

def sql_notes(reg, user, note = None, showAll = True):
    sender = aliased(User,name="sender_user")
    receiver = aliased(User,name="receiver_user")

    sql = select(Note).join(Note.sender.of_type(sender))
    sql = sql.outerjoin(Note.receiver.of_type(receiver))
    
    sql = sql.where(Note.user_can_see(user,reg))
    rg = reg.split('_')

    if note:
        qr = text(f"with R as ( \
                select note_id as n, ref_id as r from note_ref where note_id = {note} or ref_id = {note} \
                UNION \
                select note_id,ref_id from R,note_ref where note_id = r or ref_id = n \
                ) \
                select n,r from R")
        
        dqrl = db.session.execute(qr).all()
        

        qrl = []
        for d in dqrl:
            qrl.append(d[0])
            qrl.append(d[1])
        
        if not qrl:
            nt = db.session.scalars(select(Note).where(Note.id==note)).first()
            qrl = [n.id for n in nt.ref]
            qrl.append(note)
        else:
            qrl = list(set(qrl))
        
        fn = []
        for n in qrl:
            fn.append(Note.id==n)
        
        sql = sql.where(or_(*fn))

    else:
        if rg[1] in ['in','out']: # Normal register cr or ctr
            if rg[0] == 'cl':
                flow = 'in' if rg[1] == 'out' else 'out'
            else:
                flow = rg[1]
            
            sql = sql.where(Note.flow==flow)

        if rg[0] == 'cr':
            sql = sql.where(Note.reg==rg[2])

        if rg[0] == 'cl':
            ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
            sql = sql.where(or_(Note.sender==ctr,Note.receiver.contains(ctr)))
        
        if rg[0] == 'pen':
            sql = sql.where(or_(literal_column(f"receiver_user.alias = '{current_user.alias}'")))

        if rg[0] == 'min':
            sql = sql.where(Note.reg==rg[0])

        if not showAll:
            sql = sql.where(Note.done==False)

    sql = sql.group_by(Note.id)

        
    sql = sql.order_by(Note.date.desc(), Note.num.desc())

    return sql

def updateState(note,reg,alias,read_by):
    rg = reg.split("_")
    inc = 1 if not alias in read_by else -1

    if rg[0] == 'des':
        note.state += inc if rg[1] == 'in' else 2*inc
    elif rg[0] in ['cr','pen'] and rg[1] == 'in':
        if note.state == 3 and current_user in note.receivers:
            note.state = 4
    elif rg[0] == 'cr' and rg[1] == 'out' and note.state < 2:
        note.state += inc
    elif rg[0] == 'cl' and rg[1] == 'in' and note.state == 4:
        note.state = 5
    elif rg[0] == 'cl' and rg[1] == 'out' and note.state < 2:
        note.state += inc


def register_output(args,output,showAll):
    reg = args.get('reg','all')
    rg = reg.split("_")
    h_note = args.get('h_note') 
    ref = args.get('ref') 
    note = args.get('note') 
    mark = args.get('mark') 
    read = args.get('read')
    action = args.get('action')

    
    global filter_notes
    global lasturl

    sql = sql_notes(reg,current_user,h_note,showAll)


    if mark:
        nt = db.session.scalars(sql.where(Note.id==mark)).first()
        nt.done = 1 if nt.done == 0 else 0
        db.session.commit()
    elif read:
        nt = db.session.scalar(select(Note).where(Note.id==read))
        
        read_by = nt.read_by.split(",") if nt.read_by else []
        
        alias = current_user.alias
        if rg[0] == 'cl' and rg[1] == 'out':
            alias = rg[2]
        elif rg[0] == 'des':
            alias = f"des_{alias}"

        print(nt,reg,alias,read_by)
        updateState(nt,reg,alias,read_by)
        
        
        if alias in read_by:
            read_by.remove(f"{alias}")
        else:
            read_by.append(f"{alias}")

        nt.read_by = ",".join(read_by)
        db.session.commit()
    elif "newout" in output:
        newNote(current_user,reg)
    elif ref:
        if rg[0] == 'min': # I am in minutas creating a note
            minuta = db.session.scalar(select(Note).where(Note.id==ref))
            refs = [str(minuta.id)]
            for rf in minuta.ref:
                refs.append(str(rf.id))
            newNote(current_user,reg,",".join(refs))
        else: # Creating a minuta from a note
            newNote(current_user,reg,ref)
    elif 'addfiles' in output:
        nt = db.session.scalar(sql.where(Note.id==output['addfiles']))

        if not nt.permanent_link:
            rst = get_info(nt.path_note())
            folder = None
            if not rst:
                rst = create_folder(nt.path,nt.note_folder)
                if rst:
                    folder = rst['permanent_link']
            elif 'data' in rst:
                folder = rst['data']['permanent_link']

            if folder:
                nt.permanent_link = folder
                db.session.commit()
            else:
                flash(f'Could not create folder {nt.path_note()}')

        files = files_path(nt.path_note())
        
        ntfiles = []
        for file in nt.files:
            ntfiles.append(file.path)
        
        if files:
            for file in files:
                if not file['display_path'] in ntfiles:
                    nt.addFile(File(path=file['display_path'],permanent_link=file['permanent_link']))
        
            db.session.commit()

    if filter_notes:
        fn = [
            Note.fullkey.contains(filter_notes),
            literal_column(f"sender_user.alias = '{filter_notes}'"),
            literal_column(f"receiver_user.alias = '{filter_notes}'"),
            Note.content.contains(filter_notes)
        ]
        sql = sql.where(or_(*fn))

    return sql

def reg_title(reg,note=None):
    rg = reg.split('_')

    if rg[0] == 'des':
        if rg[1] == 'in':
            return 'Despacho'
        else:
            return 'Outbox'
    elif rg[0] == 'pen':
        return 'My notes'
    elif rg[0] == 'cr':
        if rg[1] == 'all':
            return "Notes history"
        else:
            return f"Notes from {rg[2]}" if rg[1] == 'in' else f"Notes to {rg[2]}"
    elif rg[0] == 'cl':
        if rg[1] == 'all':
            return "Notes history"
        else:
            return f"Notes from {rg[2]} to cr" if rg[1] == 'out' else f"Notes from cr to {rg[2]}"
    elif rg[0] == 'min':
        return 'Minutas'

@bp.route('/',methods=['POST','GET'])
@bp.route('/register',methods=['POST','GET'])
@login_required
def register():
    page = request.args.get('page', 1, type=int)
    note = request.args.get('note')
    reg = request.args.get('reg')
    title = request.args.get('title')

    global filter_notes
    global lasturl

    if not reg:
        if 'cr' in current_user.groups:
            return redirect(url_for('register.register',reg='pen_in_'))
        else:
            for gp in current_user.groups:
                if gp[:3] == 'cl_':
                    break
            
            return redirect(url_for('register.register',reg=f'cl_in_{gp[3:]}'))
    
    if reg == 'lasturl':
        return redirect(lasturl)

    output = request.form.to_dict()
    
    rg = reg.split("_")
    
    if title:
        showAll = True if title=='True' else False
    else:
        showAll = False if rg[0] == 'pen' and not note else True
    
    if 'showAll' in output:
        showAll = True if output['showAll'] == 'on' else False

    if rg[0] == 'des':
        if not 'despacho' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    elif rg[0] in ['cr','min']:
        if not 'cr' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    elif rg[0] == 'cl':
        if not f'cl_{rg[2]}' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    
    if 'notes_filter' in output:
        if filter_notes != output['notes_filter']:
            filter_notes = output['notes_filter']
            return redirect(url_for('register.register', reg=reg, page=1))
    elif not request.args.get('page'):
        filter_notes = ""
   
    
    sql = register_output(request.args,output,showAll)
   
    if 'read' in output:
        return redirect(lasturl)

    page = request.args.get('page', 1, type=int)


    notes = db.paginate(sql, per_page=30)
    prev_url = url_for('register.register', reg=reg, page=notes.prev_num, title=showAll) if notes.has_prev else None
    next_url = url_for('register.register', reg=reg, page=notes.next_num, title=showAll) if notes.has_next else None
    
    #lasturl = request.url
    lasturl = url_for('register.register',reg=reg,page=page)
    return render_template('register/register.html',title=reg_title(reg,note), notes=notes, reg=reg, page=page, prev_url=prev_url, next_url=next_url, user=current_user,showAll=showAll)

@bp.route('/edit_note', methods=['GET','POST'])
@login_required
def edit_note():
    page = request.args.get('page',1,type=int)
    
    note_id = request.args.get('note')
    sender = aliased(User,name="sender_user")
    note = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.id==note_id)).first()

    form = NoteForm(request.form,obj=note)
    form.sender.choices = [note.sender]

    global lasturl

    if note.flow == 'in' or note.reg == 'min':
        form.receiver.choices = [(user.alias,user.fullName) for user in db.session.scalars(select(User).where(User.u_groups.regexp_match(r'\bcr\b')).order_by(User.alias)).all()]
    else:
        form.receiver.choices = [(user.alias,user.fullName) for user in db.session.scalars(select(User).where(User.u_groups.regexp_match(fr'\b{note.reg}\b')).order_by(User.alias)).all()]
    
    
    if request.method == 'POST' and form.validate():
        error = False
        note.n_date = form.n_date.data
        note.year = form.year.data
        note.content = form.content.data
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
            nr = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.fullkey==ref.strip())).first()
            if nr:
                note.ref.append(nr)
            else:
                flash(f"Note {ref} doesn't exist")
                error = True
        
        db.session.commit()
        
        if not error:
            return redirect(lasturl)
    
    else:
        form.ref.data = ",".join([r.fullkey for r in note.ref]) if note.ref else "" 
        for rec in note.receiver:
            form.receiver.data.append(rec.alias)
        form.permanent.data = note.permanent

    return render_template('register/note_form.html', form=form, note=note, user=current_user)

