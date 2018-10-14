import time
import praw
import prawcore
import requests
import Config
from bs4 import BeautifulSoup
reddit = praw.Reddit(client_id=Config.cid,
                     client_secret=Config.secret,
                     password=Config.password,
                     user_agent=Config.agent,
                     username=Config.user)
subreddit = reddit.subreddit(Config.subreddit)
def flair(app_rating, num_installs, sub):
    inst = num_installs.split("+")
    if (inst[0] == "Couldn't"):
        return
    elif int(inst[0].replace(',', '')) <= 500:
        sub.mod.flair(text='New app', css_class=None)
    elif int(inst[0].replace(',', '')) >= 10000 and int(app_rating[0:1]) >= 4:
        sub.mod.flair(text= 'Popular app', css_class=None)
footer = """

*****

^^^[Source](https://github.com/a-ton/gpd-bot)
^^^|
^^^[Suggestions?](https://www.reddit.com/r/GPDBot/comments/9o59m0/)"""
file = open("postids.txt","a+")
file.close()
def logID(postid):
    f = open("postids.txt","a+")
    f.write(postid + "\n")
    f.close()

def crawl(s, u):
    print("Crawling...")
    page = requests.get(u).text
    store_page = BeautifulSoup(page, "html.parser")

    list_of_details = store_page.findAll(attrs={"class": "htlgb"})

	# get app name
    try:
        app_name = store_page.find("h1", class_="AHFaub").string
    except AttributeError:
        return "incorrect link"


	# get the number of downloads
    i = 3
    while i < 13:
        installs = list_of_details[i].string
        if installs == None:
            i = i + 2
        else:
            try:
                inst = installs.split("+")
                int(inst[0].replace(',', ''))
                i = 77
            except ValueError:
                i = i + 2

	# get rating out of 5
    try:
        temp = store_page.find("div", class_="BHMmbe").string
        rating = temp + "/5"
    except AttributeError:
        rating = "No ratings yet"

	# get developer name
    dev = store_page.find("a", class_="hrTbp R8zArc").string
    if dev in Config.blacklisted_devs:
        return "Sorry, deals from " + dev + " have been blacklisted.\n\nHere is the full list of blacklisted devleopers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"

	# get last update date
    i = 1
    while i < 13:
        updated = list_of_details[i].string
        if updated == None:
            i = i + 2
        else:
            if "201" in updated:
                i = 77
            i = i + 2

    # get size of app
    i = 3
    while i < 13:
        app_size = list_of_details[i].string
        if app_size == None:
            i = i + 2
        else:
            if "M" in app_size:
                i = 77
            i = i + 2
    try:
        if app_size == None:
            app_size = "Not given"
        else:
            inst = app_size.replace('M', '')
            inst = inst.replace('.', '')
            int(inst)
    except ValueError:
        app_size = "Not given"

    # get current price
    temp = store_page.find("meta", itemprop="price")
    current_price = temp['content']
    if current_price == "0":
        current_price = "Free"

	# get full (normal) price
    try:
        full_price = store_page.find("span", class_="LV0gI").string
    except AttributeError:
        full_price = current_price + " (can't get price in USD)"

    # find IAPs
    iap_element = store_page.find("div", class_="rxic6")
    if iap_element == None:
        IAP = "No"
        Ads = "No"
    elif iap_element.string == None:
        IAP = "Yes"
        Ads = "Yes"
    else:
        if "Offers" in iap_element.string:
            IAP = "Yes"
            both = store_page.find("div", class_="pQIMjf")
            if both == None:
                Ads = "No"
            else:
                Ads = "Yes"
        else:
            Ads = "Yes"
            IAP = "No"

    # get IAP info
    if (IAP == "Yes"):
        i = 3
        IAP_info = ""
        while i < 17:
            string = list_of_details[i].string
            if string == None:
                i = i + 2
                continue
            if '$' in string:
                IAP_info = ", "
                IAP_info += string
                i = 20
            i = i + 2
    else:
        IAP_info = ""
    # get description
    desc_strings = store_page.find("div", jsname="sngebd").stripped_strings
    desc = ''
    for string in desc_strings:
        desc += '    ' + string + '\n'
    flair(rating, installs, submission)
    return "Info for " + app_name + ":\n\n" + "Current price (USD): " + current_price + " was " + full_price + "  \nDeveloper: " + dev + "  \nRating: " + rating + "  \nInstalls: " + installs + "  \n Size: " + app_size + "  \nLast updated: " + updated + "  \nContains IAPs: " + IAP + IAP_info + "  \nContains Ads: " + Ads + "  \nShort description:\n\n\n\n" + desc[0:400] + "...  \n\n***** \n\nIf this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."

def respond(submission):
    title_url = submission.url
    title_url = title_url.split('&')
    title_url = title_url[0]
    reply_text = crawl(submission, title_url)
    reply_text += footer
    if reply_text[0:6] == "Sorry,":
        submission.mod.remove()
        submission.reply(reply_text).mod.distinguish()
        print("Removed (developer blacklist): " + submission.title)
    elif reply_text == "incorrect link" + footer:
        print("INCORRECT LINK Skipping: " + submission.title)
    else:
        submission.reply(reply_text)
        submission.mod.approve()
        print("Replied to: " + submission.title)
    logID(submission.id)

while True:
    try:
        print("Initializing bot...")
        for submission in subreddit.stream.submissions():
            if submission.is_self:
                continue
            if submission.created < int(time.time()) - 86400:
                continue
            if submission.title[0:2].lower() == "[a" or submission.title[0:2].lower() == "[i" or submission.title[0:2].lower() == "[g":
                if submission.id in open('postids.txt').read():
                    continue
                for top_level_comment in submission.comments:
                    try:
                        if top_level_comment.author and top_level_comment.author.name == "GPDBot":
                            logID(submission.id)
                            break
                    except AttributeError:
                        pass
                else: # no break before, so no comment from GPDBot
                    respond(submission)
                    continue
    except (prawcore.exceptions.RequestException, prawcore.exceptions.ResponseException):
        print ("Error connecting to reddit servers. Retrying in 5 minutes...")
        time.sleep(300)

    except praw.exceptions.APIException:
        print ("rate limited, wait 5 seconds")
        time.sleep(5)
