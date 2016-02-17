from app import db
from models import Community, Posts, Comments, User

db.create_all()
u = User(username="ben", password="appleZ1")
c = Community(name="powerlifting", password=None, founder=u, FAQ=None, description=None)
post = Posts("How to Hook Grip with Mark Robb",
    "This is a video on how to hook grip with mark robb, https://www.youtube.com/watch?v=drGcGdSMeOg",
    author=u,
    community=c)
comment = Comments("Testing the new commenting feature!",
            author=u,
            post=post)
db.session.add_all([u, c, post, comment])
c = Community(name="Programming", password=None, founder=u, FAQ=None, description=None)
post = Posts("Rubber Ducky Code -- Intro to Flask",
            "An intro to the flask microframework, made for those just finished with Learn Python the \
            hard way and looking to get into web developement:: www.rubberduckycode.com",
            author = u,
            community = c)
post2 = Posts("Project Euler Solutions made in python",
            "Project euler solutions made in python can be found here https://github.com/bendominguez011/Project-Euler-Solutions",
            author=u,
            community=c)
comment1 = Comments("Testing the new commenting feature!",
            author=u,
            post=post)
comment2 = Comments("Testing the new commenting feature!",
            author=u,
            post=post2)
db.session.add_all([c, post, post2, comment1, comment2])

c = Community("Anouncements",
            password=None,
            founder=u,
            FAQ=None,
            description=None)

post = Posts("Upcoming updates", "New updates soon to come:\
A Voting system, where you can thumb's up/thumb's down or dislike/like, dont know which yet.\n\
Authenticating with google, so that you could sign in easily through your google account, however this update may be delayed.\n\
Updated templating. I know the site currently looks terrible, but I plan on adding some more Javascript once I become more familiar with the language.\n",
 author = u, community = c)
db.session.add_all([post, c])

db.session.commit()
