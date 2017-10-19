import time
import praw
from requests.exceptions import ConnectionError, HTTPError, Timeout
import requests
import Config
from bs4 import BeautifulSoup
reddit = praw.Reddit(client_id=Config.cid,
                     client_secret=Config.secret,
                     password=Config.password,
                     user_agent=Config.agent,
                     username=Config.user)
subreddit = reddit.subreddit('googleplaydeals')
blacklisted_devs = ["Ray Software", "Han Chang Lin", "Itypenow Apps", "Imorjeny"]
footer = "\n\n*****\n\n^^^[Source](https://github.com/a-ton/gpd-bot) ^^^| ^^^[Suggestions?](https://www.reddit.com/r/GPDBot/comments/68brod/)"
file = open("postids.txt","a+")
file.close()
def logID(postid):
    f = open("postids.txt","a+")
    f.write(postid + "\n")
    f.close

def crawl(s, u):
    print("Crawling...")
    page = requests.get(u).text
    store_page = BeautifulSoup(page, "html.parser")

	# get app name
    try:
        app_name = store_page.find("div", class_="id-app-title").string
    except AttributeError:
        return "incorrect link"


	# get the number of downloads
    try:
        installs = store_page.find("div", itemprop="numDownloads").string.rstrip()
    except AttributeError:
        installs = "  Couldn't get # of installs (probably a new app)"

	# get rating out of 5
    temp = store_page.find("meta", itemprop="ratingValue")
    try:
        rating = temp['content']
        rating = rating[0:4] + "/5"
    except TypeError:
        rating = "No rating!"

	# get developer name
    dev = store_page.find("span", itemprop="name").string
    if dev in blacklisted_devs:
        return "Sorry, deals from " + dev + " have been blacklisted.\n\nHere is the full list of blacklisted devleopers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"

	# get last update date
    updated = store_page.find("div", itemprop="datePublished").string

	# get current price
    temp = store_page.find("meta", itemprop="price")
    current_price = temp['content']
    if current_price == "0":
        current_price = "Free"

	# get full (normal) price
    try:
        full_price = store_page.find("span", jsan="7.full-price").string
    except AttributeError:
        full_price = current_price + " (can't get price in USD)"

    # find IAPs
    iap_element = store_page.findAll(attrs={"class": "inapp-msg"})
    if len(iap_element) > 0:
        IAP = "Yes"
    else:
        IAP = "No"

    # get description
    desc = store_page.find("div", jsname="C4s9Ed").get_text()

    # get download size? web page doesn't show this info, only mobile. leaving in case they add it back
    #try:
    #    file_size_element = store_page.find(attrs={"itemprop": "fileSize"})
    #    file_size = file_size_element.getText()
    #except AttributeError:
    #    file_size = "this shit don't work"

	# mash all that info together into a comment (this is really ugly I know)
    return "Info for " + app_name + ":\n\n" + "Current price (USD): " + current_price + " was " + full_price + "  \nDeveloper: " + dev + "  \nRating: " + rating + "  \nInstalls: " + installs[2:100] + "  \nLast updated: " + updated + "  \nContains IAPs: " + IAP + "  \nShort description: " + desc[0:400] + "...  \n\nIf this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."

def respond(submission):
    title_url = submission.url
    reply_text = crawl(submission, title_url)
    reply_text += footer;
    if reply_text[0:6] == "Sorry,":
        submission.mod.remove()
        submission.reply(reply_text).mod.distinguish()
        print("Removed (developer blacklist): " + submission.title)
    elif reply_text == "incorrect link" + footer:
        print("INCORRECT LINK Skipping: " + submission.title)
    else:
        submission.reply(reply_text)
        print("Replied to: " + submission.title)
    logID(submission.id)

while True:
    try:
        print("Initializing bot...")
        for submission in subreddit.stream.submissions():
            responded = 0
            if submission.is_self:
                responded = 1
            elif submission.created < int(time.time()) - 86400:
                responded = 1
            elif submission.title[0:2].lower() == "[a" or submission.title[0:2].lower() == "[i" or submission.title[0:2].lower() == "[g":
                if submission.id in open('postids.txt').read():
                    responded = 1
                else:
                    for top_level_comment in submission.comments:
                        try:
                            if top_level_comment.author.name == "GPDBot":
                                responded = 1
                                logID(submission.id)
                                break
                        except AttributeError:
                            responded = 0
            if responded == 0:
                respond(submission)
    except (HTTPError, ConnectionError, Timeout):
        print ("Error connecting to reddit servers. Retrying in 5 minutes...")
        time.sleep(300)

    except praw.exceptions.APIException:
        print ("rate limited, wait 5 seconds")
        time.sleep(5)