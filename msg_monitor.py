import time
import praw
import prawcore
from dotenv import load_dotenv
import os
load_dotenv()
footer = "\n\n*****\n\n^^^[Source](https://github.com/a-ton/gpd-bot) ^^^| ^^^[Suggestions?](https://www.reddit.com/message/compose?to=Swimmer249)"
reddit = praw.Reddit(client_id=os.getenv('GPD_CID'),
                     client_secret=os.getenv('GPD_SECRET'),
                     password=os.getenv('GPD_PASSWORD'),
                     user_agent=os.getenv('GPD_AGENT'),
                     username=os.getenv('GPD_USER'))

print("Monitoring inbox...")
while True:
    try:
        for msg in reddit.inbox.stream():
            # checks if bot has already replied (good if script has to restart)
            if isinstance(msg, praw.models.Comment):
                responded = False
                for comment in msg.refresh().replies:
                    if comment.author.name == "GPDBot":
                        responded = True
                        break
                if responded:
                    continue
            # checks if the message body contains "expired" or "oops"
            if isinstance(msg, praw.models.Comment):
                msg_text = msg.body.lower()
                oops = False
                expired = False
                try:
                    if msg_text.index("oops") > -1:
                        oops = True
                except ValueError:
                    pass
                try:
                    if msg_text.index("expired") > -1:
                        expired = True
                except ValueError:
                    pass
                reply_msg = ""
                if oops:
                    msg.submission.mod.flair(text=None, css_class=None)
                    print("unflairing... responded to: " + msg.author.name)
                    reply_msg = "Flair removed." + footer
                elif expired:
                    msg.submission.mod.flair(text='Deal Expired', css_class='expired')
                    print("flairing... responded to: " + msg.author.name)
                    reply_msg = "Deal marked as expired. Reply with \"oops\" if this is incorrect." + footer

                if reply_msg != "":
                    msg.mark_read()
                    msg.reply(body=reply_msg)
    except (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException):
        print ("Error connecting to reddit servers. Retrying in 5 minutes...")
        time.sleep(300)

    except praw.exceptions.APIException:
        print ("rate limited, wait 5 seconds")
        time.sleep(5)
