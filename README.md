# in progress web app
This is an in-progress and nameless 😢 web app I worked on this summer. It works much like reddit, users can join or create communities and post to them. Users are able to create accounts and login and are rendered a feed of new posts from communities they are joined to.
* Database migrations uses Alembic
* Frontend uses Bootstrap


#included modules
* [Flask and Werkzeug](http://flask.pocoo.org) for the base
* [Flask-Login](https://flask-login.readthedocs.org/en/latest/) -- user logins
* [Flask-WTF](https://flask-wtf.readthedocs.org/en/latest/) -- form validation
* [Flask-SQLAlchemy](https://pythonhosted.org/Flask-SQLAlchemy/) -- database ORM made for python
* [Flask-Bcrypt](https://flask-bcrypt.readthedocs.org/en/latest/) -- bcrypt hashing
* [Flask-WhooshAlchemy](https://github.com/gyllstromk/Flask-WhooshAlchemy) -- searching posts

#setting up

clone the repository and set up the flask virtual environment
```
$ mkdir community_project
$ git clone https://github.com/bendominguez011/no-name-web-app.git
$ pip install virtualenv
$ virtualenv flask
```
install the required extensions
```
$ flask/bin/pip install flask
$ flask/bin/pip install flask-login
$ flask/bin/pip install flask-wtf
$ flask/bin/pip install flask-sqlalchemy
$ flask/bin/pip install flask-whooshalchemy
$ flask/bin/pip install flask-bcrypt
```
install Bootstrap however you like, though it has to be under the static folder


#alembic migration commands

[alembic documentation](https://alembic.readthedocs.org/en/latest/tutorial.html#running-our-first-migration) for specific instructions on how to run migrations
auto-generate is configured though, so no need to write your own migrations, just make sure your read over the migration script before upgrading. The command for auto-generating revisions is below.
```
$ alembic revision --autogenerate -m "what you changed"
```
