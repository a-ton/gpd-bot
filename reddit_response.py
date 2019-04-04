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

class Error(Exception):
    """Base class"""
    pass

class LinkError(Error):
    """Could not parse the URL"""
    pass

class BlacklistedDev(Error):
    """This developer is blacklisted"""
    pass

class AppInfo:
    def getName(self):
        try:
            app_name = self.store_page.find("h1", class_="AHFaub").string
            return app_name
        except AttributeError:
            raise LinkError

    def getNumDownloads(self):
        i = 3
        while i < 13:
            installs = self.list_of_details[i].string
            if installs == None:
                i = i + 2
            else:
                try:
                    inst = installs.split("+")
                    int(inst[0].replace(',', ''))
                    i = 77
                except ValueError:
                    i = i + 2
        return installs

    def getRating(self):
        try:
            temp = self.store_page.find("div", class_="BHMmbe").string
            rating = temp + "/5"
        except AttributeError:
            rating = "No ratings yet"
        return rating

    def getDeveloper(self):
        dev = self.store_page.find("a", class_="hrTbp R8zArc").string
        if dev in Config.blacklisted_devs:
            raise BlacklistedDev
        return dev

    def getLastUpdateDate(self):
        i = 1
        while i < 13:
            updated = self.list_of_details[i].string
            if updated == None:
                i = i + 2
            else:
                if "201" in updated:  # this code is gonna break in 2020 lol
                    i = 77
                i = i + 2
        return updated

    def getSize(self):
        i = 3
        while i < 17:
            print(self.list_of_details[i].string)
            app_size = self.list_of_details[i].string
            if app_size:
                if "M" in app_size and app_size[0] != 'M':  # makes sure that it doesn't grab March
                    break
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
        return app_size

    def getCurrentPrice(self):
        try:
            temp = self.store_page.find("meta", itemprop="price")
            current_price = temp['content']
        except TypeError:
            return "incorrect link"
        if current_price == "0":
            current_price = "Free"
        return current_price

    def getFullPrice(self):
        try:
            full_price = self.store_page.find("span", class_="LV0gI").string
        except AttributeError:
            full_price = self.getCurrentPrice() + " (can't get price in USD)"
        return full_price

    def getIAPs(self):
        iap_element = self.store_page.find("div", class_="rxic6")
        if iap_element == None:
            IAP = "No"
        elif iap_element.string == None:
            IAP = "Yes"
        else:
            if "Offers" in iap_element.string:
                IAP = "Yes"
            else:
                IAP = "No"
        return IAP

    def getAds(self):
        iap_element = self.store_page.find("div", class_="rxic6")
        if iap_element == None:
            Ads = "No"
        elif iap_element.string == None:
            Ads = "Yes"
        else:
            if "Offers" in iap_element.string:
                both = self.store_page.find("div", class_="pQIMjf")
                if both == None:
                    Ads = "No"
                else:
                    Ads = "Yes"
            else:
                Ads = "Yes"
        return Ads

    def getIAPInfo(self):
        i = 3
        IAP_info = ""
        while i < 17:
            string = self.list_of_details[i].string
            if string == None:
                i = i + 2
                continue
            if '$' in string:
                IAP_info = ", "
                IAP_info += string
                i = 20
            i = i + 2
        return IAP_info

    def getDescription(self):
        desc_strings = self.store_page.find("div", jsname="sngebd").stripped_strings
        desc = ''
        totalChar = 0
        for s in desc_strings:
            desc += '>' + s + '  \n'
            totalChar += len(s)
            if totalChar >= 400:
                break
        return desc

    def __init__(self, submission, url):
        self.blacklist = False
        self.invalid = False
        self.submission = submission
        page = requests.get(url).text
        self.store_page = BeautifulSoup(page, "html.parser")
        self.list_of_details = self.store_page.findAll(attrs={"class": "htlgb"})
        try: 
            self.name = self.getName()
        except LinkError:
            self.invalid = True
        self.downloads = self.getNumDownloads()
        self.rating = self.getRating()
        try:
            self.developer = self.getDeveloper()
        except BlacklistedDev:
            self.blacklist = True
        self.last_update = self.getLastUpdateDate()
        self.size = self.getSize()
        self.current_price = self.getCurrentPrice()
        self.full_price = self.getFullPrice()
        self.IAPs = self.getIAPs()
        self.ads = self.getAds()
        if (self.IAPs == "Yes"):
            self.IAP_info = self.getIAPInfo()
        else:
            self.IAP_info = ""
        self.desc = self.getDescription()
    

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

# make an empty file for first run
f = open("postids.txt","a+")
f.close()
def logID(postid):
    f = open("postids.txt","a+")
    f.write(postid + "\n")
    f.close()

def crawl(s, u):
    print("Crawling...")
    app = AppInfo(s, u)
    if (app.blacklist):
        return "Sorry, deals from this developer have been blacklisted.\n\nHere is the full list of blacklisted devleopers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"
    if (app.invalid):
        return "incorrect link"
    flair(app.rating, app.downloads, s)
    return "Info for " + app.name + ":\n\n" + "Current price (USD): " + app.current_price + " was " + app.full_price + "  \nDeveloper: " + app.developer + "  \nRating: " + app.rating + "  \nInstalls: " + app.downloads + "  \n Size: " + app.size + "  \nLast updated: " + app.last_update + "  \nContains IAPs: " + app.IAPs + app.IAP_info + "  \nContains Ads: " + app.ads + "  \nShort description:\n\n\n\n" + app.desc + "  \n\n***** \n\nIf this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."

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
