
import os, sys, logging
import types
from flask import Flask, Response
from flask import current_app, render_template, url_for, flash, session, request, redirect, g, abort, send_from_directory
from flask.ext.login import LoginManager
from flask.ext.login import login_user, logout_user, current_user, login_required
#google imports
#from oauth2client import client
import json
#import httplib2
#from apiclient import discovery
from forms import LoginForm, NewPostForm, JoinForm, NewCommunityForm, AddModeratorForm, SearchForm
from forms import time_choices
#end of google imports
from check_forms import check_password, check_special_and_spaces
from check_forms import FormNotValidError
from datetime import datetime
from werkzeug import secure_filename
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from secret import secret_key
from flask.ext.mobility.decorators import mobile_template


base_directory = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

search_enabled = os.environ.get('HEROKU') is None

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
if os.environ.get('DATABASE_URL') is not None:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI


app.secret_key = secret_key

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

from models import User, Community, Posts

lm = LoginManager()
lm.init_app(app)
WTF_CRSF_ENABLED = True
SECRET_KEY = os.urandom(7)
lm.login_view = 'login'
lm.login_message = 'Please login tho'
POSTS_PER_PAGE = 3
FAQ_DIRECTORY = os.path.join(os.path.dirname(__file__), 'FAQ_uploads')


app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

@app.route('/authenticate_with_google')
def authenticate_with_google():
    return render_template('google.html')

#render these templates when http status code is raised
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal(error):
    return render_template('500.html'), 500

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    #set instances of these forms globally, since they show up on the base template
    g.search_form = SearchForm()
    g.join_form = JoinForm()
    g.search_enabled = search_enabled

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    return render_template('login.html', title='login page', form=form)

@app.route('/login/check', methods=['GET', 'POST'])
def login_check():
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user:
        # checking if hash(passsword inputed) is equal to the hash of the password on the database for the given username
        # returns True or False
        check_hash = bcrypt.check_password_hash(user.password, request.form['password'])
        if check_hash == True:
            login_user(user)
        else:
            flash('password not correct')
            return redirect(url_for('login'))
    else:
        flash('Username does not exist')
        return redirect(url_for('login'))

    return redirect(url_for('user_profile'))

@app.route('/logout')
def logout():
    logout_user()
    # clear session for community base templates
    session.clear()
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    form = LoginForm()
    return render_template('signup.html', title='Sign up', form=form)

@app.route('/signup/check', methods=['GET', 'POST'])
def signup_check():
    # check to see if there are any spaces or special characters in the requested username
    try:
        check_special_and_spaces(request.form['username'])
    except FormNotValidError as e:
        flash(e.args[0])
        return redirect(url_for('signup'))
    # checks to see if password has at least one capital and one number
    try:
        check_password(request.form['password'])
    except FormNotValidError as e:
        flash(e.args[0])
        return redirect(url_for('signup'))
    username = request.form['username']
    find_user = User.query.filter_by(username=username).first()
    if find_user == None:
        username, password = username, request.form['password']
        user = User(username, password)
        db.session.add(user)
        db.session.commit()
        if 'remember_me' in session:
            remember_me = session['remember_me']
        else:
            remember_me = None
        login_user(user)
        return redirect(url_for('user_profile'))
    else:
        flash("Username already taken. Please try again")
        return redirect(url_for('signup'))



@app.route('/')
@app.route('/<int:page>')
def index(page=1):
    paginated_posts = None
    enough_posts = False
    if g.user and g.user.is_authenticated:
        user = g.user
        posts = user.render_all_community_posts()
        # this is for banner support, doesnt work yet as of now
        session['original_number_of_posts'] = len(posts.all())
        paginated_posts = posts.paginate(page, POSTS_PER_PAGE, False)
        enough_posts = len(posts.all()) > 3
    kwargs = {
        'posts': paginated_posts,
        'title': None,
        'enough_posts': enough_posts
    }
    return render_template('index.html', **kwargs)

@app.route('/user')
@app.route('/user/<int:page>')
@login_required
def user_profile(page=1):
    user = g.user
    kwargs = {
        'user': user,
        'posts': user.posts.paginate(page, POSTS_PER_PAGE, False).items,
        'enough_posts': len(user.posts.all()) > 3
    }
    return render_template('user.html', **kwargs)


@app.route('/community/<community>/new', methods=['GET', 'POST'])
@login_required
def create_new_post(community):
    postform = NewPostForm()
    c = Community.query.filter_by(name=community).first()
    if postform.validate_on_submit():
        user = g.user
        post = Posts(title=request.form['title'], body=request.form['body'], author=user, community=c)
        # users can only post if they a part of the community
        if c.is_joined(user):
            db.session.add(post)
            db.session.commit()
        else:
            flash('User must be a part of the community to create a post')
        return redirect(url_for('community', community=community))
    kwargs = {
        'postform': postform,
        'community': community,
        'c': c
    }
    return render_template('new_post.html', **kwargs)


@app.route('/community')
def communities():
    # renders a list of communities
    communities = Community.query.all()
    return render_template('communities.html', communities=communities)

@app.route('/community/<community>')
@app.route('/community/<community>/<int:page>', methods=['GET', 'POST'])
def community(community, page=1):
    user = g.user
    # get community instance from the name of the community in the url
    c = Community.query.filter_by(name=community).first()
    if c is None:
        flash("community %s not found" % community)
        return redirect(url_for('index'))
    #checking if the user is logged in to avoid an AttributeError
    if user and user.is_authenticated:
        session['user'] = user.username
        session['joined'] = c.is_joined(user)
    if c.founder == user:
        session['FOUNDER_MODE'] = 'FOUNDER_MODE'
    kwargs = {
        'community': community,
        'c': c,
        'enough_posts': len(c.posts.all()) > POSTS_PER_PAGE,
        'posts': c.posts.paginate(page, POSTS_PER_PAGE, False)
    }
    return render_template('community_posts.html', **kwargs)

@app.route('/community/<community>/join', methods=['GET', 'POST'])
@login_required
def join_community(community):
    c = Community.query.filter_by(name=community).first()
    c.join(g.user)
    return redirect(url_for('community', community=community))

@app.route('/community/<community>/leave', methods=['GET', 'POST'])
@login_required
def leave_community(community):
    c = Community.query.filter_by(name=community).first()
    c.leave(g.user)
    return redirect(url_for('community', community=community))

@app.route('/newcommunity', methods=['GET', 'POST'])
@login_required
def create_community():
    form = NewCommunityForm()
    filename = None
    if form.validate_on_submit():
        if request.files['FAQ']:
            # split the file into its extension and filename
            file = request.files['FAQ']
            extension = file.filename.split('.')[1]
            file_part = file.filename.split('.')[0]
            # user must submit a .txt file that has the same filename as the name of the community being created
            if extension == "txt" and file_part == request.form['name']:
                # secure and save the file to the directory FAQ_DIRECTORY so it can be retrieved later
                filename = secure_filename(file.filename)
                file.save(os.path.join(FAQ_DIRECTORY, filename))
            else:
                flash("Please follow instructions for submitting FAQ files")
                return redirect(url_for('create_community'))
        community = Community.query.filter_by(name=request.form['name']).first()
        if community is None:
            try:
                #check to make sure no spaces or special characters
                #check to make sure (if there is a password) that there is at least one capital and one number
                check_special_and_spaces(request.form['name'])
                check_special_and_spaces(request.form['password'])
            except FormNotValidError as e:
                flash(e.args[0])
                return redirect(url_for('create_community'))
            kwargs = {
                'name': request.form['name'],
                'password': request.form['password'],
                'founder': g.user,
                'FAQ': str(filename),
                'description': request.form['description']
            }
            c = Community(**kwargs)
            db.session.add(c)
            db.session.commit()
            communities = Community.query.all()
            return render_template('communities.html', communities=communities)
        else:
            flash("community already exists")
    return render_template('create_community.html', form=form)

@app.route('/community/<community>/top_users')
def top_users(community):
    c = Community.query.filter_by(name=community).first()
    # returns a list of users that have the most posts in the community
    users = c.find_top_users()
    kwargs = {
        'users': users,
        'community': community,
        'c': c
    }
    return render_template('topusers.html', **kwargs)

@app.route('/community/<community>/add_moderators', methods=['GET', 'POST'])
@login_required
def add_moderators(community):
    # if the user is not the founder, raise 404 error
    if not 'FOUNDER_MODE' in session:
        abort(404)
    assign_mod_form = AddModeratorForm()
    c = Community.query.filter_by(name=community).first()
    if assign_mod_form.validate_on_submit():
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        # check if user exists and if they are joined to the community to are going to be a mod of
        if user and c.is_joined(user):
            c.moderators.append(user)
            db.session.commit()
            return redirect(url_for('community', community=community))
        else:
            flash("user does not exist or not a part of the community")
    try:
        #moderators can only be added for every 30 users in the comunity, unless there are no moderators yet
        thirty_to_one_ratio = len(c.users.all())/len(c.moderators.all())
    except ZeroDivisionError:
        thirty_to_one_ratio = None
    if thirty_to_one_ratio > 30 or thirty_to_one_ratio is None:
        kwargs = {
            'community': community,
            'c': c,
            #if >30:1 ratio for users to moderators, send through th eassin mod form
            'assign_mod_form': assign_mod_form,
                }
        return render_template('add_moderators.html', **kwargs)
    else:
        flash("There needs to be at least 30 users per mod")
        return redirect(url_for('community', community=community))

@app.route('/community/<community>/FAQ')
def FAQ(community):
    c = Community.query.filter_by(name=community).first()
    #check safely if FAQ file exists
    try:
        file = c.FAQ
        # open the file as read only and set to an object
        contents = open(file, 'r')
    except IOError or TypeError:
        flash("No FAQ for community %s" % c.name)
        return redirect(url_for('community', community=community))
    kwargs = {
        'community': community,
        'c': c,
        'contents': contents
    }
    return render_template('FAQ.html', **kwargs)


@app.route('/search/<query>/<delta>')
def search_all(query, delta):
    #convert delta to int/check if its unicode
    # if its unicode then no time filter was set
    #anticipating an error if delta is passed as None, because no time filter is set
    try:
        delta = int(delta)
        check_delta = True
    except ValueError:
        check_delta = False
    if check_delta:
        # if delta is an int search this way
       results = Posts.search_by_time_delta(Posts.search_all, delta, query)
       flash("searched by time delta")
    else:
        results = Posts.search_all(query)
        flash("searched all posts")
    return render_template('all_results.html', results=results)

@app.route('/community/<community>/search', methods=['GET', 'POST'])
def search_community(community):
    if not g.search_form.validate_on_submit():
        return redirect(url_for('community', community=community))
    if request.method == 'POST':
        #get their choice for the time filter
        delta = dict(time_choices).get(g.search_form.time_search.data)
        #safely check if community search is selected
        # if filter by community is not selected, search all
        if bool(request.form.get('community_search', None)) is False:
            return redirect(url_for('search_all', query=request.form['search'], delta=delta))
        kwargs = {
            'community': community,
            'query': request.form['search'],
            'delta': delta
        }
        return redirect(url_for('search_community_results', **kwargs))

@app.route('/community/<community>/search/<query>/<delta>')
def search_community_results(community, query, delta):
    #same thing as above, check if delta is an int or unicode
    try:
        delta = int(delta)
        check_delta = True
    except ValueError:
        check_delta = False
    c = Community.query.filter_by(name=community).first()
    if check_delta:
        # same thing, if time filter is present search by time delta
       results = Posts.search_by_time_delta(Posts.search_by_community, delta, query, c)
       flash("searched by time delta")
    else:
        results = Posts.search_by_community(query, c)
        flash("searched all posts")
    kwargs = {
        'community': community,
        'c': c,
        'results': results,
        'query': query
    }
    return render_template('community_results.html', **kwargs)

@app.route('/community/<community>/post/<int:post_id>')
def show_community_post(community, post_id):
    c = Community.query.filter_by(name=community).first()
    post = Posts.query.get(post_id)
    return render_template("show_post.html", c=c, post=post)

@app.route('/community/<community>/post/<int:post_id>/delete')
def delete_community_post(community, post_id):
    post = Posts.query.filter_by(id = post_id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('user_profile'))
