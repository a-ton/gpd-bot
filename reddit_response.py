import time
import praw
import prawcore
import requests
import Config
import re
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
        iap_element = self.store_page.find("div", class_="bSIuKf")
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
        iap_element = self.store_page.find("div", class_="bSIuKf")
        if iap_element == None:
            Ads = "No"
        elif iap_element.string == None:
            Ads = "Yes"
        else:
            if "Offers" in iap_element.string:
                both = self.store_page.find("div", class_="aEKMHc")
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
        while i < 23:
            string = self.list_of_details[i].string
            if string == None:
                i = i + 2
                continue
            if "per item" in string:
                IAP_info = ", "
                IAP_info += string
                return IAP_info
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
            return
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

# make an empty file for first run
f = open("postids.txt","a+")
f.close()
def logID(postid):
    f = open("postids.txt","a+")
    f.write(postid + "\n")
    f.close()

def respond(submission):
    footer = """

*****

^^^[Source](https://github.com/a-ton/gpd-bot)
^^^|
^^^[Suggestions?](https://www.reddit.com/r/GPDBot/comments/9o59m0/)"""
    
    urls = []
    if submission.is_self:
        urls = re.findall('(?:(?:https?):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', submission.selftext)
        if len(urls) == 0:
            print("NO LINK FOUND skipping: " + submission.title)
            logID(submission.id)
            return

    # remove duplicate URLs
    unique_urls = []
    for url in urls:
        if url in unique_urls:
            continue
        else:
            unique_urls.append(url)

    # find apps that we can respond to
    valid_apps = []
    for url in unique_urls:
        app = AppInfo(submission, url)
        if app.invalid:
            print("Invalid url: " + url)
            continue
        valid_apps.append(app)
        if len(valid_apps) >= 10:
            break

    if not submission.is_self:
        app = AppInfo(submission, submission.url)

    if len(valid_apps) == 1:
        app = valid_apps[0]

    if submission.is_self and len(valid_apps) == 0:
        print("All invalid links, skipping: " + submission.title)
        logID(submission.id)
        return
        
    if len(valid_apps) > 1:
        reply_text = ""
        for app_num in range(10):
            app = valid_apps[app_num]
            if app.blacklist:
                reply_text = "Sorry, deals from one or more of the developers in your post have been blacklisted. Here is the full list of blacklisted developers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"
                submission.mod.remove()
                submission.reply(reply_text).mod.distinguish()
                print("Removed (developer blacklist): " + submission.title)
                logID(submission.id)
                return
            reply_text += "Info for [" + app.name + "](" + url + "): Price (USD): " + app.current_price + " was " + app.full_price + " | Rating: " + app.rating + " | Installs: " + app.downloads + " | Size: " + app.size + " | IAPs/Ads: " + app.IAPs + app.IAP_info + "/" + app.ads + "\n\n*****\n\n"
        if len(valid_apps) >= 10:
            reply_text += "...and more. Max of 10 apps reached.\n\n*****\n\n"
        reply_text += "If any of these deals have expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."
        reply_text += footer
        
        submission.reply(reply_text)
        submission.mod.approve()
        
        print("Replied to: " + submission.title)
        logID(submission.id)
        return

    if not app.invalid:
        flair(app.rating, app.downloads, submission)

    if app.blacklist:
        reply_text = "Sorry, deals from one or more of the developers in your post have been blacklisted. Here is the full list of blacklisted developers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"
        submission.mod.remove()
        submission.reply(reply_text).mod.distinguish()
        print("Removed (developer blacklist): " + submission.title)
    elif app.invalid:
        print("INCORRECT LINK Skipping: " + submission.title)
    else:
        reply_text = "Info for " + app.name + ":\n\n" + "Current price (USD): " + app.current_price + " was " + app.full_price + "  \nDeveloper: " + app.developer + "  \nRating: " + app.rating + "  \nInstalls: " + app.downloads + "  \nSize: " + app.size + "  \nLast updated: " + app.last_update + "  \nContains IAPs: " + app.IAPs + app.IAP_info + "  \nContains Ads: " + app.ads + "  \nShort description:\n\n\n\n" + app.desc + "  \n\n***** \n\nIf this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."
        reply_text += footer
        submission.reply(reply_text)
        submission.mod.approve()
        print("Replied to: " + submission.title)
    logID(submission.id)

while True:
    try:
        print("Initializing bot...")
        for submission in subreddit.stream.submissions():
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
        print ("Rate limited, waiting 5 seconds")
        time.sleep(5)
