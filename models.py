import os
import datetime
from app import app
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
import flask.ext.whooshalchemy as whoosh
import datetime

base_directory = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_directory, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['WHOOSH_BASE'] = os.path.join(base_directory, 'search.db')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

users_and_communities = db.Table('users',
    db.Column('user_id', db.Integer, db.ForeignKey('community.id')),
    db.Column('community_id', db.Integer, db.ForeignKey('user.id'))
    )

moderators_and_communities = db.Table('moderators',
    db.Column('user_id', db.Integer, db.ForeignKey('community.id')),
    db.Column('community_id', db.Integer, db.ForeignKey('user.id'))
    )
#database relationships:
#Many to many between Community and Users
#One to many between User and Posts
#One to many between Community and Posts

class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    private = db.Column(db.Boolean())
    password = db.Column(db.String(100))
    FAQ = db.Column(db.String())
    description = db.Column(db.String(140))
    time_founded = db.Column(db.DateTime)
    founder_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    posts = db.relationship('Posts', backref='community', lazy='dynamic')
    users = db.relationship('User', secondary=users_and_communities, backref='communities', lazy='dynamic')
    moderators = db.relationship('User', secondary=moderators_and_communities, backref='moderating', lazy='dynamic')


    def __init__(self, name, password, founder, FAQ, description):
        self.name = name
        self.password = password
        self.founder = founder
        self.time_founded = datetime.datetime.utcnow()
        self.FAQ = FAQ
        self.description = description
        if self.password:
            self.private = True
            self.password = bcrypt.generate_password_hash(self.password)
        else:
            self.private = False

    def is_joined(self, user):
        return self.users.filter_by(username=user.username).count() != 0

    def join(self, user):
        if not self.is_joined(user):
            self.users.append(user)
            db.session.commit()
            return self

    def leave(self, user):
        if self.is_joined(user):
            if self.is_moderator(user):
                self.remove_moderator(user)
            self.users.remove(user)
            db.session.commit()
            return self

    def is_moderator(self, user):
        return self.moderators.filter_by(username=user.username).count() != 0

    def assign_moderator(self, user):
        if self.is_joined(user):
            self.moderators.append(user)
            db.session.commit()
            return self

    def remove_moderator(self, user):
        if self.is_moderator(user):
            self.moderators.remove(user)
            db.session.commit()
            return self

    def find_top_users(self):
        users = self.users.all()
        top_users = []
        for user in users:
            top_users.append((user.posts.filter_by(community=self).count(), user))
        top_users = sorted(top_users, reverse=True)
        while len(top_users) < 3:
            top_users.append((None, None))
        return [top_users[0][1], top_users[1][1], top_users[2][1]]

    def __repr__(self):
        return '<Community %s>' % self.name

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(100))
    time_joined = db.Column(db.DateTime)
    posts = db.relationship('Posts', backref='author', lazy='dynamic')
    findings = db.relationship('Community', backref='founder', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.generate_password_hash(password)
        self.time_joined = datetime.datetime.utcnow()

    def get_id(self):
        return unicode(self.id)

    def render_all_community_posts(self):
        return Posts.query.join(Community).\
        join(Community.users).\
        filter(User.id==self.id).\
        order_by(Posts.time_created.desc())

    def __repr__(self):
        return '<User %r>' % self.username

class Posts(db.Model):

    __searchable__ = ['title']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    body = db.Column(db.String(200))
    time_created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'))

    def __init__(self, title, body, author, community):
        self.title = title
        self.body = body
        self.author = author
        self.community = community
        self.time_created = datetime.datetime.utcnow()

    @staticmethod
    def search_all(search):
        return Posts.query.whoosh_search(search)

    @staticmethod
    def search_by_community(search, community):
        return Posts.query.whoosh_search(search).\
        filter(Posts.community_id == community.id)

    @staticmethod
    def search_by_time_delta(func, delta, *args):
        past = datetime.date.today() - datetime.timedelta(delta)
        return func(*args).filter(Posts.time_created >= past)

    def __repr__(self):
        return '<Post %r>' % self.title

whoosh.whoosh_index(app, Posts)
