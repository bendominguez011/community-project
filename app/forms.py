from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired

time_choices = [('all posts', 'all'), ('past 24 hours', '1'), ('past week', '7'), ('past month', '31')]

class LoginForm(Form):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class NewPostForm(Form):
    title = StringField('title', validators=[DataRequired()])
    body = TextAreaField('body', validators=[DataRequired()])

class NewCommunityForm(Form):
    name = StringField('name', validators=[DataRequired()])
    password = StringField('password')
    FAQ = FileField('FAQ')
    description = TextAreaField('description', validators=[DataRequired()])

class AddModeratorForm(Form):
    username = StringField('username', validators=[DataRequired()])

class JoinForm(Form):
    join = SubmitField('join')
    leave = SubmitField('leave')

class SearchForm(Form):
    search = StringField('search', validators=[DataRequired()])
    community_search = BooleanField('community_search', default=True)
    time_search = SelectField('time_search', choices=time_choices)

class CommentForm(Form):
    content = StringField('comment', validators=[DataRequired()])
