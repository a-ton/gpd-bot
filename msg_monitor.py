import time
import praw
import prawcore 
import requests
import Config
from bs4 import BeautifulSoup
responded = 0
footer = "\n\n*****\n\n^^^[Source](https://github.com/a-ton/gpd-bot) ^^^| ^^^[Suggestions?](https://www.reddit.com/r/GPDBot/comments/68brod/)"
reddit = praw.Reddit(client_id=Config.cid,
                     client_secret=Config.secret,
                     password=Config.password,
                     user_agent=Config.agent,
                     username=Config.user)
def check_price(s, u):
    print("Checking price")
    page = requests.get(u).text
    store_page = BeautifulSoup(page, "html.parser")

    # get current price
    temp = store_page.find("meta", itemprop="price")
    current_price = temp['content']

	# get full (normal) price
    try:
        full_price = store_page.find("span", class_="LV0gI").string
        if full_price != current_price:
            return False
    except AttributeError:
        return True

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
                            print("not oops")
                        try:
                            if text.index("expired") > -1:
                                expired = True
                        except ValueError:
                            print("not about expiry")
                        if oops:
                            msg.mark_read()
                            msg.submission.mod.flair(text=None, css_class=None)
                            print("unflairing... responded to: " + msg.author.name)
                            msg.reply("Flair removed. Please report the user who originally marked this deal as expired." + footer)
                        elif expired:
                            msg.mark_read()
                            title_url = msg.submission.url
                            is_expired = check_price(msg.submission, title_url)
                            if is_expired:
                                msg.submission.mod.flair(text='Deal Expired', css_class='expired')
                                print("flairing... responded to: " + msg.author.name)
                                msg.reply("Deal marked as expired. Reply with \"oops\" if this is incorrect." + footer)
                            else:
                                print("not expired... responded to: " + msg.author.name)
                                msg.reply("This still appears to be a deal, not marked as expired." + footer)
            except AttributeError:
                print("error checking comment by: " + msg.author.name)
    except prawcore.exceptions.RequestException:
        print ("Error connecting to reddit servers. Retrying in 5 minutes...")
        time.sleep(300)

    except praw.exceptions.APIException:
        print ("rate limited, wait 5 seconds")
        time.sleep(5)
