from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import InputRequired


class CommentForm(FlaskForm):
    author = StringField(validators=[InputRequired()])
    text = TextAreaField(validators=[InputRequired()])


class ReplyForm(FlaskForm):
    author = StringField(validators=[InputRequired()])
    text = TextAreaField(validators=[InputRequired()])
