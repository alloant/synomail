# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField,DateField,IntegerField, RadioField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms_sqlalchemy.orm import QuerySelectField, QuerySelectMultipleField
from sqlalchemy import select

from app import db
from app.models.user import User
from app.models.note import Note

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class NoteForm(FlaskForm):
    num = IntegerField('Num',validators=[DataRequired()])
    year = IntegerField('Year',validators=[DataRequired()])
    sender = SelectField('Sender', validators=[DataRequired()])

    receiver = MultiCheckboxField('Receiver',coerce=str)
    #receiver = SelectMultipleField('Receiver', validators=[DataRequired()])
    n_groups = StringField('Groups', validators=[])
    n_date = DateField('Date', validators=[DataRequired()])
    content = StringField('Content', validators=[DataRequired()])
    proc = StringField('Procedure', validators=[])
    ref = StringField('References', validators=[])

    permanent = BooleanField('Only permanent')

    submit = SubmitField("Submit")
