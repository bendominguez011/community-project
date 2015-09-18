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
        #if a password is set, then the community is private, hash the password
        if self.password:
            self.private = True
            self.password = bcrypt.generate_password_hash(self.password)
        else:
            self.private = False
    #checks if a user is joined to a community, returns True if the user is, False if not
    def is_joined(self, user):
        return self.users.filter_by(username=user.username).count() != 0

    #if user is not already joined, add users user to the community
    def join(self, user):
        if not self.is_joined(user):
            self.users.append(user)
            db.session.commit()
            return self

    #if user is joined, removes user from the community
    def leave(self, user):
        if self.is_joined(user):
            if self.is_moderator(user):
                self.remove_moderator(user)
            self.users.remove(user)
            db.session.commit()
            return self

    #checks if a user is a moderator of a community
    def is_moderator(self, user):
        return self.moderators.filter_by(username=user.username).count() != 0

    #adds a user as a moderator, user must first be joined to the community, though.
    def assign_moderator(self, user):
        if self.is_joined(user):
            self.moderators.append(user)
            db.session.commit()
            return self

    #removes user as moderator if he/she is a moderator
    def remove_moderator(self, user):
        if self.is_moderator(user):
            self.moderators.remove(user)
            db.session.commit()
            return self

    #returns a list of tuples of the users that post the most in the community, and the number of posts
    def find_top_users(self):
        users = self.users.all()
        top_users = []
        for user in users:
            top_users.append((user.posts.filter_by(community=self).count(), user))
        top_users = sorted(top_users, reverse=True)
        #if there are less than 3 users that have posted in the community, add empty tuples to the list instead
        while len(top_users) < 3:
            top_users.append((None, None))
        #at index 0 is the top user, 1 the second, 2 the third, and then the 1 index after gives us their number of posts. so the function returns a tuple with order (user, num_of_posts)
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

    #return all community posts for every community a specific user is joined to, and then sort them by newest
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

    #search all posts in database for a query
    @staticmethod
    def search_all(search):
        return Posts.query.whoosh_search(search)

    #search all posts belonging to a given community in database for a query
    @staticmethod
    def search_by_community(search, community):
        return Posts.query.whoosh_search(search).\
        filter(Posts.community_id == community.id)

    #search by the time difference in days given, so if delta is 7, this function will search all posts in the past week
    #the function also takes either search_by_community or search_all with their arguments as arguments, so a user can filter by time and community
    @staticmethod
    def search_by_time_delta(func, delta, *args):
        past = datetime.date.today() - datetime.timedelta(delta)
        return func(*args).filter(Posts.time_created >= past)

    def __repr__(self):
        return '<Post %r>' % self.title

whoosh.whoosh_index(app, Posts)
