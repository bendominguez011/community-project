
"""
a bot that will automatically
update app once a day with anouncements """

from apscheduler.schedulers.blocking import BlockingScheduler
import selenium
from app.app import db
from app.app import Posts, Community
import datetime
import random

filename = "anouncements.txt"
anouncements = []

schedule = BlockingScheduler()

@schedule.scheduled_job('cron', day_of_week='mon-sun', hour=12)
def bot():

    """adding contents of the file to a list, so that a random
    choice can be made, then adding the choices back minus
    the random choice """

    with open(filename, "r") as file:
        for line in file:
            line = line.split('\n')[0]
            anouncements.append(line)

    anouncement = random.choice(anouncements)
    anouncements.remove(anouncement)

    with open(filename, "w+") as file:
        for a in anouncements:
            file.write(a)
            file.write('\n')

    """adding the contents to a post
    so that an anouncement can be made"""

    content = "Anouncement:\ncurrent update being made to the site and coming soon:\n{0}".format(anouncement)

    now = datetime.datetime.utcnow()
    day, month, year = now.day, now.month, now.year
    title = "Anouncement {0}/{1}/{2}".format(month, day, year)

    c = Community.query.all().pop()

    post = Posts(title=title, body=content, author=None, community=c)

    db.session.add(post)
    db.session.commit()


"""
need to run command heroku ps:scale bot=1 to add one dyno to this process
"""
