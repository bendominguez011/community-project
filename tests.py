import os
import unittest
import datetime
from app import app
from models import db
from models import User, Community, Posts, Comments, Vote
from models import base_directory
from flask import request, url_for
from flask import Response

response = Response()

class TestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_directory, 'test_app.db')
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_users_and_communities(self):
        u = User('ben', 'Password1')
        c1 = Community('community1', None, u, None, None)
        c2 = Community('community2', 'Password123', u, None, None)
        db.session.add_all([u, c1, c2])
        db.session.commit()
        c1.join(u)
        self.assertFalse(c1.is_moderator(u))
        c1.assign_moderator(u)
        self.assertEqual(u"%s" % u.id, u.get_id())
        self.assertEqual(u, c1.founder)
        self.assertEqual(u, c2.founder)
        self.assertFalse(u.password == 'Password1')
        self.assertTrue(u in c1.users.all())
        self.assertTrue(c1.is_joined(u))
        self.assertTrue(c1.is_moderator(u))
        c1.remove_moderator(u)
        self.assertFalse(c1.is_moderator(u))
        c1.assign_moderator(u)
        c1.leave(u)
        self.assertFalse(c2.password == 'Password123')
        self.assertFalse(c1.is_joined(u))
        self.assertFalse(c1.is_moderator(u))
        self.assertFalse(c1.private)
        self.assertTrue(c2.private)

    def test_top_users(self):
        user1 = User('user1', 'pw')
        user2 = User('user2', 'pw')
        user3 = User('user3', 'pw')
        community = Community('PL', None, user1, None, None)
        db.session.add_all([user1, user2, user3, community])
        db.session.commit()
        community.users.append(user1)
        community.users.append(user2)
        community.users.append(user3)
        db.session.commit()
        #user3 will have 2 posts, user1 will have 1, and user2 will have 0
        post1 = Posts('Title', 'Body', author=user3, community=community)
        post2 = Posts('Title', 'Body', author=user3, community=community)
        post3 = Posts('Title', 'Body', author=user1, community=community)
        db.session.add_all([post1, post2, post3])
        db.session.commit()
        self.assertEqual(community.find_top_users(),
        [user3, user1, user2]
        )

    def test_render_all_posts(self):
        user1 = User('user1', 'pw')
        user2 = User('user2', 'pw')
        c1 = Community('c1', None, founder=user1, FAQ=None, description=None)
        c2 = Community('c2', None, founder=user1, FAQ=None, description=None)
        db.session.add_all([user1, user2, c1, c2])
        db.session.commit()
        post1 = Posts('T1', 'Body', author=user1, community=c1)
        post2 = Posts('T2', 'Body', author=user2, community=c1)
        post3 = Posts('T3', 'Body', author=user1, community=c2)
        post4 = Posts('T4', 'Body', author=user2, community=c2)
        db.session.add_all([post1, post2, post3, post4])
        c1.join(user1)
        c2.join(user1)
        self.assertEqual(user1.render_all_community_posts().all(),
        [post4, post3, post2, post1])

    def test_comments(self):
        u = User('user', 'applez1')
        c = Community('Powerlifting', None, None, None, None)
        post = Posts('This is a Title', 'This is a body', author=u, community=c)
        comment1 = Comments("This is a comment", author=u, post=post)
        comment2 = Comments("This is a second comment", author=u, post=post)
        comments = post.comments.all()
        self.assertEqual([comment1, comment2], comments)

    def test_votes(self):
        u = User('user', 'applez1')
        c = Community('Powerlifting', None, None, None, None)
        post = Posts('This is a Title', 'This is a body', author=u, community=c)
        comment1 = Comments("This is a comment", author=u, post=post)
        v = Vote(u)
        self.assertEqual(u, v.user)
        v = Vote(u, post=post)
        self.assertEqual(v.post, post)
        v = Vote(u, comment=comment1)
        self.assertEqual(v.comment, comment1)
        v.vote(u, post, 1, post)
        self.assertEqual(post.value, 1)


if __name__ == '__main__':
    unittest.main()
