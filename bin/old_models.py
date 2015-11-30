"""
>>> from models import db
>>> db.create_all()
>>> from models import User
>>> user = User('ben', 'mjnoppQ12')
>>> user
<User 'ben'>
>>> user.password
'$2a$12$V5E2XMJGxNvI15dK0bcH3OAibkKtryio/RId3/1dSfH9kImJ/N6LK'
>>> user.id
>>> 
>>> print user.id
None
>>> plc = Community('powerlifting')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'Community' is not defined
>>> from models import Community
>>> plc = Community('powerlifting')
>>> plc
<Community 'powerlifting'>
>>> powerlifting.private
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'powerlifting' is not defined
>>> plc.private
False
>>> plc.user.append(user)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'Community' object has no attribute 'user'
>>> plc.users.append(user)
>>> plc.users
[<User 'ben'>]
>>> user.communities
[<Community 'powerlifting'>]
>>> 

"""

"""
>>> from models import db, User, Posts
>>> db.create_all()
>>> user = User.query.get(1)
>>> post1 = Posts('My first post', 'This is my first post today', user)
>>> user.posts
<sqlalchemy.orm.dynamic.AppenderBaseQuery object at 0x10259d090>
>>> user.posts.all()
[<Post 'My first post']"""

"""#This was my abstracted database I used for piping
class UserNotFoundError(Exception):
    pass 

class User(UserMixin):
    #abstracted database
    #username: password
    user_database = {
        "Ben": "pw",
        "MeekMills": "meekspassword"
    }
    
    def __init__(self, id):
        if not id in self.user_database:
            raise UserNotFoundError()
        self.id = id
        self.password = self.user_database[id]
        
    @classmethod
    def get(cls, id):
        try:
            return cls(id)
        except UserNotFoundError:
            return None
        """