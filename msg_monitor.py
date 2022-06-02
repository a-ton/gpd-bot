import time
import praw
import prawcore 
import requests
import Config
from bs4 import BeautifulSoup
responded = 0
footer = "\n\n*****\n\n^^^[Source](https://github.com/a-ton/gpd-bot) ^^^| ^^^[Suggestions?](https://www.reddit.com/message/compose?to=Swimmer249)"
reddit = praw.Reddit(client_id=Config.cid,
                     client_secret=Config.secret,
                     password=Config.password,
                     user_agent=Config.agent,
                     username=Config.user)

print("Monitoring inbox...")
while True:
    try:
        for msg in reddit.inbox.stream():
            expired = False
            oops = False
            responded = 0
            # checks if bot has already replied (good if script has to restart)
            try:
                if isinstance(msg, praw.models.Comment):
                    for comment in msg.refresh().replies:
                        try:
                            if comment.author.name == "GPDBot":
                                responded = 1
                        except AttributeError:
                            responded = 0
                print("Message recieved")
            except AttributeError:
                print("error checking comment by: " + msg.author.name)
            # checks if the message body contains "expired" or "oops"
            try:
                if responded == 0:
                    if isinstance(msg, praw.models.Comment):
                        text = msg.body.lower()
                        try:
                            if text.index("oops") > -1:
                                oops = True
                        except ValueError:
                            pass
                        try:
                            if text.index("expired") > -1:
                                expired = True
                        except ValueError:
                            pass
                        if oops:
                            msg.mark_read()
                            msg.submission.mod.flair(text=None, css_class=None)
                            print("unflairing... responded to: " + msg.author.name)
                            msg.reply("Flair removed." + footer)
                        elif expired:
                            msg.mark_read()
                            title_url = msg.submission.url
                            msg.submission.mod.flair(text='Deal Expired', css_class='expired')
                            print("flairing... responded to: " + msg.author.name)
                            msg.reply("Deal marked as expired. Reply with \"oops\" if this is incorrect." + footer)
            except AttributeError:
                print("error checking comment by: " + msg.author.name)
    except (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException):
        print ("Error connecting to reddit servers. Retrying in 5 minutes...")
        time.sleep(300)

    except praw.exceptions.APIException:
        print ("rate limited, wait 5 seconds")
        time.sleep(5)
