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

from app.models.nas.nas import create_folder, upload_path, convert_office, files_path

from app.forms.note import NoteForm

bp = Blueprint('register', __name__)

filter_notes = ""

def newNote(user,reg,num):
    folder = user.alias
    rg = reg.split('_')
    if '_ctr_' in reg:
        ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
        folder = ctr.alias
        nt = Note(num=num,sender_id=ctr.id,reg='ctr')
    else:
        nt = Note(num=num,sender_id=user.id,reg=rg[1])
    
        if rg[1] in ['cg','asr']:
            rec = db.session.scalar(select(User).where(User.alias==rg[1]))
            nt.receiver.append(rec)
    
    db.session.add(nt)
    
    sender = aliased(User,name="sender_user")
    sql = select(Note).join(Note.sender.of_type(sender))

    new_note = db.session.scalars(sql.order_by(Note.id.desc())).first()


    rst = db.session.commit()
    
    rst = create_folder(f"/team-folders/Data/Minutas/{folder}/Notes",f"{new_note.note_folder}")
    new_note.permanent_link = rst['permanent_link']
    
    """
    doc = Document('note.docx')
    file = NamedTemporaryFile()

    #doc.tables[0].cell(0,0).text = nt.ref
    doc.tables[0].cell(0,1).text = nt.fullkey

    doc.save(file)
    file.seek(0)
    file.name = f"{nt.key}.docx"
    
    rst_upload = upload_path(file,f"/team-folders/Data/Minutas/{user.alias}/Notes/{nt.key}")
    if rst_upload:
        print('Converting')
        path,f_id,p_link = convert_office(f"/team-folders/Data/Minutas/{user.alias}/Notes/{nt.key}/{file.name}",delete=True)
  
    nt.addFile(File(path=path,permanent_link=p_link))
    
    rst = db.session.commit()
    """

def sql_notes(reg,user,note = None):
    sender = aliased(User,name="sender_user")
    receiver = aliased(User,name="receiver_user")

    sql = select(Note).join(Note.sender.of_type(sender))
    sql = sql.outerjoin(Note.receiver.of_type(receiver))
    
    sql = sql.where(Note.user_can_see(user,reg))
   
    if reg in ['despacho','outbox']:
        pass
    #    fn = [
    #            and_(Note.flow=='in',not_(Note.read_by.regexp_match(r'\b.*,.*\b'))),
    #            and_(Note.flow=='out',not_(Note.read_by.regexp_match(r'\b.*\b'))),
    #        ]
    #    sql = sql.where(or_(*fn))
    if reg == 'all':
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

        else: # This is pendings
            sql = sql.where(Note.done==False)
            fn = [
                #literal_column(f"sender_user.alias = '{current_user.alias}'"),
                literal_column(f"receiver_user.alias = '{current_user.alias}'"),
            ]
            sql = sql.where(or_(*fn))
    else: # Normal register cr or ctr
        if "_" in reg:
            rg = reg.split("_")
            sql = sql.where(Note.reg==rg[1])
            

            if len(rg) == 3:
                ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
                if rg[0] == 'out':
                    rg[0] = 'in'
                    sql = sql.where(Note.sender==ctr)
                else:
                    rg[0] = 'out'
                    sql = sql.where(Note.receiver.contains(ctr))
 
            sql = sql.where(Note.flow==rg[0])


    sql = sql.group_by(Note.id)

        
    sql = sql.order_by(Note.date.desc(), Note.num.desc())

    return sql

def updateState(note,reg,alias,read_by):
    if '_ctr_' in reg:
        if note.flow == 'in': # Is a cl member sending
            if note.state == 0 and not alias in read_by:
                note.state = 1
            elif note.state == 1 and alias in read_by:
                note.state = 0
    elif note.flow == 'in':
        if reg == 'despacho' and note.state < 3:
            note.state += 1
        elif note.state == 3 and current_user in note.receivers:
            note.state = 4
    else: #Note out from a dr of cr
        if note.state == 0 and not alias in read_by:
            note.state = 3



def register_output(args,output):
    reg = args.get('reg','all')
    rg = reg.split("_")
    note = args.get('note') 
    mark = args.get('mark') 
    read = args.get('read')
    action = args.get('action')

    global filter_notes
    sql = sql_notes(reg,current_user,note)

    if mark:
        nt = db.session.scalars(sql.where(Note.fullkey==mark)).first()
        nt.done = 1 if nt.done == 0 else 0
        db.session.commit()

    elif read:
        nt = db.session.scalar(select(Note).where(Note.id==read))
        read_by = nt.read_by.split(",") if nt.read_by else []
        
        alias = current_user.alias
        if '_ctr_' in reg and nt.flow == 'in': # Sending mail to cr in cl register
            alias = rg[2]

        updateState(nt,reg,alias,read_by)

        if alias in read_by:
            read_by.remove(f"{alias}")
        else:
            read_by.append(f"{alias}")
        

        nt.read_by = ",".join(read_by)
        db.session.commit()
        
    elif "newout" in output:
        rst = db.session.scalars( select(func.max(literal_column("num"))).select_from(sql.where(Note.year==datetime.today().year)) ).first()
        
        if rst:
            rst += 1
        elif reg.split("_")[1] == 'cg':
            rst = 1
        elif reg.split("_")[1] == 'asr':
            rst = 250
        elif reg.split("_")[1] == 'ctr':
            rst = 1000
        elif reg.split("_")[1] == 'r':
            rst = 2000
        
        newNote(current_user,reg,rst)
    elif action == 'addfiles' or 'addfiles' in output:
        nt = db.session.scalar(sql.where(Note.id==output['addfiles']))
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
    if reg == 'all':
        if note:
            return 'Notes'
        else:
            return 'Pending notes'
    elif reg == 'despacho':
        return 'Despacho'
    elif reg == 'outbox':
        return 'Outbox'
    elif "_" in reg:
        rg = reg.split("_")
        if len(rg) == 2:
            fm = 'from' if rg[0] == 'in' else 'to'
            return f'Notes {fm} {rg[1]}'
        else:
            fm = 'from' if rg[0] == 'out' else 'to'
            return f'Notes {fm} {rg[2]}'

@bp.route('/register',methods=['POST','GET'])
@login_required
def register():
    page = request.args.get('page', 1, type=int)
    note = request.args.get('note')
    reg = request.args.get('reg')
    wantedurl = request.args.get('wantedurl')

    global filter_notes
    output = request.form.to_dict()

    rg = reg.split("_")

    if reg == 'despacho':
        if not 'despacho' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    elif len(rg) == 2:
        if not 'cr' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    elif len(rg) == 3:
        if not f'cl_{rg[2]}' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    
    if 'notes_filter' in output:
        if filter_notes != output['notes_filter']:
            filter_notes = output['notes_filter']
            return redirect(url_for('register.register', reg=reg, page=1))
    elif not request.args.get('page'):
        filter_notes = ""
   
    
    sql = register_output(request.args,output)
   
    if reg == 'addfiles' or 'read' in output:
        return redirect(wantedurl)

    page = request.args.get('page', 1, type=int)


    notes = db.paginate(sql, per_page=30)

    prev_url = url_for('register.register', reg=reg, page=notes.prev_num, title=reg_title(reg)) if notes.has_prev else None
    next_url = url_for('register.register', reg=reg, page=notes.next_num, title=reg_title(reg)) if notes.has_next else None
    
    return render_template('register/register.html',title=reg_title(reg,note), notes=notes, reg=reg, page=page, prev_url=prev_url, next_url=next_url, user=current_user, wantedurl = request.url)

@bp.route('/edit_note', methods=['GET','POST'])
@login_required
def edit_note():
    wantedurl = request.args.get('wantedurl')
    page = request.args.get('page',1,type=int)
    wantedurl = f"{wantedurl}&page={page}"
    
    note_id = request.args.get('note')
    sender = aliased(User,name="sender_user")
    note = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.id==note_id)).first()

    form = NoteForm(request.form,obj=note)
    form.sender.choices = [note.sender]


    if note.flow == 'in':
        form.receiver.choices = [(user.alias,f"{user.alias} - {user.name}, ({user.u_groups})") for user in db.session.scalars(select(User).where(User.u_groups.regexp_match(r'\bcr\b')).order_by(User.alias)).all()]
    else:
        form.receiver.choices = [(user.alias,f"{user.alias} - {user.name}, ({user.u_groups})") for user in db.session.scalars(select(User).where(User.u_groups.regexp_match(fr'\b{note.reg}\b')).order_by(User.alias)).all()]
    
    
    if request.method == 'POST' and form.validate():
        error = False
        note.n_date = form.n_date.data
        note.year = form.year.data
        note.content = form.content.data
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
            return redirect(wantedurl)
    
    else:
        form.ref.data = ",".join([r.fullkey for r in note.ref]) if note.ref else "" 
        for rec in note.receiver:
            form.receiver.data.append(rec.alias)
        form.permanent.data = note.permanent

    return render_template('register/note_form.html', form=form, note=note, user=current_user)

@bp.route('/add_files',methods=['POST','GET'])
@login_required
def add_files():
    wantedurl = request.args.get('wantedurl')
    fullkey = request.args.get('note')
    output = request.form.to_dict()
    path = request.args.get('dir')
    
    if 'cancel_files' in output:
        return redirect(wantedurl)
    elif 'accept_files' in output:
        sender = aliased(User,name="sender_user")
        nt = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.fullkey==fullkey)).first()
        print(output) 
        for out in output:
            if out[:7] == 'choose_':
                nt.addFile(File(path=f"{path}/{out[7:]}",permanent_link=output[out]))
                #nt.addFile(File(name=files_to_choose[int(data[1])]['name'],path=path,type=files_to_choose[int(data[1])]['type'],permanent_link=files_to_choose[int(data[1])]['permanent_link']))
        db.session.commit()

        return redirect(wantedurl)

    
    if not path:
        path = "/mydrive"
        
    files_to_choose = files_path(path)

    parent_path = path[:path.rfind("/")]
    if parent_path:
        files_to_choose = [{'type':'dir','name':'../','display_path':parent_path}] + files_to_choose
    
    return render_template('register/file_chooser.html',files=files_to_choose)

