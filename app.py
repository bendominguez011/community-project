import os
import types
from flask import Flask, Response
from flask import current_app, render_template, url_for, flash, session, request, redirect, g, abort, send_from_directory
from flask.ext.login import LoginManager
from flask.ext.login import login_user, logout_user, current_user, login_required
#google imports
from oauth2client import client
import json
import httplib2
from apiclient import discovery
from forms import LoginForm, NewPostForm, JoinForm, NewCommunityForm, AddModeratorForm, SearchForm
from forms import time_choices
#end of google imports
from check_forms import check_password, check_special_and_spaces
from check_forms import FormNotValidError
from datetime import datetime
from werkzeug import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(7)
lm = LoginManager()
lm.init_app(app)
WTF_CRSF_ENABLED = True
SECRET_KEY = os.urandom(7)
lm.login_view = 'login'
lm.login_message = 'Please login tho'
POSTS_PER_PAGE = 3
FAQ_DIRECTORY = os.path.join(os.path.dirname(__file__), 'FAQ_uploads')

""" error handler views """
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal(error):
    return render_template('500.html'), 500
""" end of error handler views"""
""" authenticate with google views """

@app.route('/login/google')
def authenticate_with_google():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])
    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        drive_service = discovery.build('drive', 'v2', http_auth)
        files = drive_service.files.list().execute()
        return json.dumps(files)

@app.route('/oauth2callback')
def oauth2callback():
    flow = client.flow_from_clientsecrets(
    'client_secrets.json',
    scope='https://www.googleapis.com/auth/drive.metadata.readonly',
    #redirect_uri=url_for('oauth2callback', _external=True)
    redirect_uri='https://www.example.com/oauth2callback'
    )
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('authenticate_with_google'))

""" end of authenticate with google views """

""" logging in views """
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    g.search_form = SearchForm()
    g.join_form = JoinForm()

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    #this doesnt work, dont know why
    """if form.validate_on_submit():
        flash("Login requested for username='%s', password='%s', remember me='%s'" % (form.username.data, form.password.data, str(form.remember_me.data)))"""
    return render_template('login.html', title='login page', form=form)

@app.route('/login/check', methods=['GET', 'POST'])
def login_check():
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user:
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
    session.clear()
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    form = LoginForm()
    return render_template('signup.html', title='Sign up', form=form)

@app.route('/signup/check', methods=['GET', 'POST'])
def signup_check():
    try:
        check_special_and_spaces(request.form['username'])
    except FormNotValidError as e:
        flash(e.args[0])
        return redirect(url_for('signup'))
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

""" end of logging in views """

@app.route('/')
@app.route('/<int:page>')
def index(page=1):
    posts = None
    enough_posts = False
    if g.user and g.user.is_authenticated():
        user = g.user
        posts = user.render_all_community_posts().paginate(page, POSTS_PER_PAGE, False)
        enough_posts = len(user.render_all_community_posts().all()) > 3
    kwargs = {
        'posts': posts,
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

""" community views """
@app.route('/community')
def communities():
    communities = Community.query.all()
    return render_template('communities.html', communities=communities)

@app.route('/community/<community>')
@app.route('/community/<community>/<int:page>', methods=['GET', 'POST'])
def community(community, page=1):
    user = g.user
    c = Community.query.filter_by(name=community).first()
    if c is None:
        flash("community %s not found" % community)
        return redirect(url_for('index'))
    #checking if the user is logged in to avoid an AttributeError
    if user and user.is_authenticated():
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
            file = request.files['FAQ']
            extension = file.filename.split('.')[1]
            file_part = file.filename.split('.')[0]
            if extension == "txt" and file_part == request.form['name']:
                filename = secure_filename(file.filename)
                file.save(os.path.join(FAQ_DIRECTORY, filename))
            else:
                flash("Please follow instructions for submitting FAQ files")
                return redirect(url_for('create_community'))
        community = Community.query.filter_by(name=request.form['name']).first()
        if community is None:
            try:
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
    if not 'FOUNDER_MODE' in session:
        abort(404)
    assign_mod_form = AddModeratorForm()
    c = Community.query.filter_by(name=community).first()
    if assign_mod_form.validate_on_submit():
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user and c.is_joined(user):
            c.moderators.append(user)
            db.session.commit()
            return redirect(url_for('community', community=community))
        else:
            flash("user does not exist or not a part of the community")
    try:
        thirty_to_one_ratio = len(c.users.all())/len(c.moderators.all())
    except ZeroDivisionError:
        thirty_to_one_ratio = None
    if thirty_to_one_ratio > 30 or thirty_to_one_ratio is None:
        kwargs = {
            'community': community,
            'c': c,
            'assign_mod_form': assign_mod_form,
                }
        return render_template('add_moderators.html', **kwargs)
    else:
        flash("There needs to be at least 30 users per mod")
        return redirect(url_for('community', community=community))

@app.route('/community/<community>/FAQ')
def FAQ(community):
    c = Community.query.filter_by(name=community).first()
    try:
        file = c.FAQ
        contents = open(file, 'r')
    except IOError:
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
    try:
        delta = int(delta)
        check_delta = True
    except ValueError:
        check_delta = False
    if check_delta:
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
        delta = dict(time_choices).get(g.search_form.time_search.data)
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
    #anticipating an error if delta is passed as None, because no time filter is set
    try:
        delta = int(delta)
        check_delta = True
    except ValueError:
        check_delta = False
    c = Community.query.filter_by(name=community).first()
    if check_delta:
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
    return "post %i" % post_id

@app.route('/community/<community>/post/<int:post_id>/delete')
def delete_community_post(community, post_id):
    post = Posts.query.filter_by(id = post_id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('user_profile'))

""" end of community views """

if __name__ == '__main__':
    from models import User, Bcrypt, Posts, Community
    from models import db, bcrypt
    app.run(host='0.0.0.0', debug=True)
