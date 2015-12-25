from app import db
from models import Community, Posts, Comments, User

db.create_all()
u = User(username="ben", password="appleZ1")
c = Community(name="powerlifting", password=None, founder=u, FAQ=None, description=None)
post = Posts("How to Hook Grip with Mark Robb",
    "This is a video on how to hook grip with mark robb, https://www.youtube.com/watch?v=drGcGdSMeOg",
    author=u,
    community=c)
db.session.add_all([u, c, post])
c = Community(name="Programming", password=None, founder=u, FAQ=None, description=None)
db.session.add(c)
db.session.commit()
