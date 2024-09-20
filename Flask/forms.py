from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, EmailField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email
from models import Data, VolunteerProject


class ModelDataForm(FlaskForm):
    """Form for entering data."""
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)],
                       render_kw={'class': 'form-control', 'placeholder': 'Enter your full name'})
    method = SelectField('Payment Method', choices=[('Credit Card', 'Credit Card'), ('Debit Card', 'Debit Card')],
                         validators=[DataRequired()], render_kw={'class': 'form-control'})
    amount = DecimalField('Amount', validators=[DataRequired()],
                          render_kw={'class': 'form-control', 'placeholder': 'Enter amount'})
    card_num = StringField('Card Number', validators=[DataRequired(), Length(min=4, max=4)],
                           render_kw={'class': 'form-control', 'placeholder': 'Enter last 4 digits'})
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()],
                     render_kw={'class': 'form-control', 'type': 'date'})

class VolunteerForm(FlaskForm):
    """Form for volunteer sign up."""
    project = SelectField('Project', coerce=int, validators=[DataRequired()], render_kw={'class': 'form-control'})
    name = StringField('Volunteer Name', validators=[DataRequired(), Length(max=100)],
                       render_kw={'class': 'form-control', 'placeholder': 'Enter your full name'})
    email = EmailField('Email Address', validators=[DataRequired(), Email()],
                       render_kw={'class': 'form-control', 'placeholder': 'Enter your email address'})

class VolunteerProjectForm(FlaskForm):
    """Form for creating a new volunteer project."""
    title = StringField('Project Title', validators=[DataRequired(), Length(max=100)],
                        render_kw={'class': 'form-control', 'placeholder': 'Project Title'})
    description = TextAreaField('Project Description', validators=[DataRequired()],
                                 render_kw={'class': 'form-control', 'placeholder': 'Describe the project'})
    date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()],
                     render_kw={'class': 'form-control', 'type': 'date'})
