# main.py
from datetime import datetime, date
import re
import os

from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from flask_login import login_required, current_user

from sqlalchemy import or_, and_, func, not_, select, literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.sql import text

#from wtforms import SelectField
#from werkzeug.utils import secure_filename

#from docx import Document
#from tempfile import NamedTemporaryFile

from app import db
from .models.user import User
from .models.note import Note
from .models.file import File

from .models.nas.nas import create_folder, files_path, move_path, convert_office

from .forms.note import NoteForm

from .syneml import read_eml, write_eml

bp = Blueprint('register', __name__)


def nextNumReg(rg):
    # Get new number for the note. Here getting the las number in that register
    sender = aliased(User,name="sender_user")
    if rg[0] == 'min':
        num = db.session.scalar( select(func.max(literal_column("num"))).select_from(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.reg=='min',Note.year==datetime.today().year,Note.sender==current_user))) )
    elif rg[0] == 'cl':
        num = db.session.scalar( select(func.max(literal_column("num"))).select_from(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.year==datetime.today().year,literal_column(f"sender_user.alias = '{rg[2]}'"),Note.flow=='in'))) )
    else:
        num = db.session.scalar( select(func.max(literal_column("num"))).select_from(select(Note).join(Note.sender.of_type(sender)).where(and_(Note.reg==rg[2],Note.year==datetime.today().year,Note.flow=='out'))) )
    
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
    else: # it is a ctr making the first note of the year
        num = 1

    return num


def newNote(user,reg,ref = None):
    rg = reg.split('_')

    num = nextNumReg(rg)

    # Creating the note. We need to know the register it bellows. This note could have been created by a cr dr or a cl member
    if rg[0] == 'cl': # New note made by a cl member. It's a note for cr from ctr 
        ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
        nt = Note(num=num,sender_id=ctr.id,reg='ctr')
    elif rg[0] == 'min':
        nt = Note(num=num,sender_id=user.id,reg=rg[0])
    else: # Note created by a cr dr
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

    db.session.add(nt)
    rst = db.session.commit()

def sql_notes(reg, user, note = None, showAll = True):
    sender = aliased(User,name="sender_user")
    receiver = aliased(User,name="receiver_user")
    
    rg = reg.split('_')

    sql = select(Note).join(Note.sender.of_type(sender))
    sql = sql.outerjoin(Note.receiver.of_type(receiver))
    
    sql = sql.where(Note.user_can_see(user,reg))

    if note: #Here is the history of a note sql
        qr = text(f"with recursive R as ( \
                select note_id as n, ref_id as r from note_ref where note_id = {note} or ref_id = {note} \
                UNION \
                select note_ref.note_id,note_ref.ref_id from R,note_ref where note_ref.note_id = R.r or note_ref.ref_id = R.n \
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

    elif not showAll:
        sql = sql.where(Note.state<6)

    sql = sql.group_by(Note.id)

    if rg[0] in ['min','pen']:
        sql = sql.order_by(Note.state,Note.date.desc(), Note.num.desc())
    else:
        sql = sql.order_by(Note.date.desc(), Note.num.desc())

    return sql

def register_output(args,output,showAll):
    reg = args.get('reg','all')
    rg = reg.split("_")
    h_note = args.get('h_note') 
    
    sql = sql_notes(reg,current_user,h_note,showAll)
    
    state = args.get('state')
    cldone = args.get('cldone')
    read = args.get('read')
    ref = args.get('ref') 

    
    if read:
        nt = db.session.scalar(select(Note).where(Note.id==read))
        nt.updateRead(current_user)
        db.session.commit()
    elif cldone:
        ctr = db.session.scalar(select(User).where(User.alias==rg[2]))
        nt = db.session.scalar(select(Note).where(Note.id==cldone))
        nt.updateRead(ctr)
        db.session.commit()
    elif state:
        again = True if args.get('again') else False
        nt = db.session.scalar(select(Note).where(Note.id==state))
        nt.updateState(reg,current_user,again)
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
        nt = db.session.scalar(select(Note).where(Note.id==output['addfiles']))
        nt.updateFiles()

    # Find filter in fullkey, sender, receivers or content
    if 'filter_notes' in session:
        fn = [
            Note.fullkey.contains(session['filter_notes']),
            literal_column(f"""sender_user.alias = '{session["filter_notes"]}'"""),
            literal_column(f"""receiver_user.alias = '{session["filter_notes"]}'"""),
            Note.content.contains(session["filter_notes"])
        ]
        sql = sql.where(or_(*fn))

    return sql

def reg_title(reg,note=None):
    rg = reg.split('_')

    if rg[0] == 'des':
        return 'Despacho'
    elif rg[0] == 'pen':
        return 'My notes'
    elif rg[0] == 'box' and rg[1] == 'out':
        return 'Notes from cr to be sent to cg, asr, r and ctr'
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


@bp.route('/inbox_scr',methods=['POST','GET'])
@login_required
def inbox_scr():
    output = request.form.to_dict()
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
    page = request.args.get('page', 1, type=int)
    files = db.paginate(sql, per_page=30)
    prev_url = url_for('register.inbox_scr', page=files.prev_num) if files.has_prev else None
    next_url = url_for('register.inbox_scr', page=files.next_num) if files.has_next else None
    
    return render_template('register/inbox_scr.html',title="Files received from cg and r", files=files, page=page, prev_url=prev_url, next_url=next_url)


@bp.route('/register_new',methods=['POST','GET'])
@login_required
def register_new():
    note = request.args.get('note')
    reg = request.args.get('reg')
    rg = reg.split("_") 
    
    # To control the showAll button. We start as False in pendings and minutas
    showAll = request.args.get('showAll')
    if showAll != None:
        showAll = True if showAll == 'True' else False
    else:
        showAll = False if rg[0] in ['pen','min'] and not note else True

    page = request.args.get('page', 1, type=int)
   
    fn = []
    fn.append(Note.reg==rg[2])
    fn.append(Note.flow==rg[1])
    fn.append(Note.state==6)
    fn.append(Note.reg!='min')

 
    sender = aliased(User,name="sender_user")
    sql = select(Note).join(Note.sender.of_type(sender)).where(and_(*fn))
    sql = sql.order_by(Note.date.desc(), Note.num.desc())
    notes = db.paginate(sql, per_page=30)
    
    prev_url = url_for('register.register', reg=reg, page=notes.prev_num, showAll=showAll) if notes.has_prev else None
    next_url = url_for('register.register', reg=reg, page=notes.next_num, showAll=showAll) if notes.has_next else None
    
    session['lasturl'] = url_for('register.register',reg=reg,page=page)
    return render_template('register/register.html',title=reg_title(reg,note), notes=notes, reg=reg, page=page, prev_url=prev_url, next_url=next_url, user=current_user,showAll=showAll)


@bp.route('/register',methods=['POST','GET'])
@login_required
def register():
    note = request.args.get('note')
    reg = request.args.get('reg')
    rg = reg.split("_")


    # This is use when someone puts and invalid url without reg
    if not reg:
        if 'cr' in current_user.groups:
            return redirect(url_for('register.register',reg='pen_in_'))
        else:
            for gp in current_user.groups:
                if gp[:3] == 'cl_':
                    break
            
            return redirect(url_for('register.register',reg=f'cl_in_{gp[3:]}'))

    # Sending to last url when needed
    if reg == 'lasturl':
        return redirect(session['lasturl'])

    output = request.form.to_dict()

    if 'sendmail' in output: # We are sending mail
        sender = aliased(User,name="sender_user")
        tosendnotes = db.session.scalars(select(Note).join(Note.sender.of_type(sender)).where(Note.flow=='out',Note.state==1))
        
        for nt in tosendnotes:
            rst = nt.move(f'/team-folders/Data/Notes/{nt.year}/{nt.reg} out')
            rst = True
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

            db.session.commit()

    if 'upload' in output:
        files = request.files.getlist('files')
        for file in files:
            if file.filename.split('.')[-1] == 'eml':
                read_eml(file.read())
    
    # To control the showAll button. We start as False in pendings and minutas
    showAll = request.args.get('showAll')
    if showAll != None:
        showAll = True if showAll == 'True' else False
    else:
        showAll = False if rg[0] in ['pen','min'] and not note else True

    # If we have just clicked in showAll
    if 'notes_filter' in output:
        if output['notes_filter'] == "":
            if 'showAll' in output:
                showAll = True
            else:
                showAll = False

    # Security check. See if the user has access to that register
    if rg[0] == 'des':
        if not 'despacho' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    elif rg[0] in ['cr','min']:
        if not 'cr' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    elif rg[0] == 'cl':
        if not f'cl_{rg[2]}' in current_user.groups:
            return redirect(url_for('register.register', reg='all', page=1))
    
    # If have just put a new filter
    if 'notes_filter' in output:
        if session['filter_notes'] != output['notes_filter']:
            session['filter_notes'] = output['notes_filter']
            return redirect(url_for('register.register', reg=reg, page=1))
    elif not request.args.get('page'):
        session['filter_notes'] = ""
   
    # Getting the main sql for the register and doing other operations like new, edit...   
    sql = register_output(request.args,output,showAll)
   
    if 'read' in output:
        return redirect(session['lasturl'])

    page = request.args.get('page', 1, type=int)

    notes = db.paginate(sql, per_page=30)
    
    prev_url = url_for('register.register', reg=reg, page=notes.prev_num, showAll=showAll) if notes.has_prev else None
    next_url = url_for('register.register', reg=reg, page=notes.next_num, showAll=showAll) if notes.has_next else None
    
    #lasturl = request.url
    session['lasturl'] = url_for('register.register',reg=reg,page=page)
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

