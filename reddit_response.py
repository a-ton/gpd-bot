import time
import praw
import prawcore
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import Config
import re
import urllib
import urllib.request
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
    #  Get the name of the app from the store page
    def getName(self):
        return self.store_page.find("h1", itemprop="name").get_text()
    
    def getNumDownloads(self):
        for item in self.expanded_details:
            if "Downloads" in item.text:
                downloads = item.text[len("Downloads"):]
                return downloads
        return "Couldn't get downloads"
    
    def getRating(self):
        try:
            rating = self.store_page.find("div", class_="TT9eCd").get_text()
        except AttributeError:
            return "NA    "
        return rating[:-4] + "/5"

    def getDeveloper(self):
        dev = self.store_page.find("div", class_="Vbfug auoIOc")
        dev_url = dev.find("a").get("href")
        if dev.get_text() in Config.blacklisted_devs:
            raise BlacklistedDev
        return "[" + dev.get_text() + "]" + "(https://play.google.com" + dev_url + ")"

    def getLastUpdateDate(self):
        for item in self.expanded_details:
            if "Updated on" in item.text:
                return item.text[len("Updated on"):]
        return "Couldn't get update date"

    #def getSize(self):
    #    return "Currently unavailable"

    def getPriceInfo(self):
        try:
            temp = self.store_page.find("span", class_="VfPpkd-vQzf8d").get_text()
        except TypeError:
            return "incorrect link"
        split_price = temp.split(" ")
        full_price = split_price[0]
        sale_price = split_price[1]
        if sale_price == "Buy":
            sale_price = "(Couldn't get sale info)"
        if sale_price == "Install":
            sale_price = "Free"
        return sale_price + " was " + full_price
    

    def getPlayPass(self):
        play_pass = self.store_page.find("a", class_="pFise")
        if play_pass:
            return "\n**Included with Play Pass**  "
        return ""

    def getAds(self):
        check = self.store_page.findAll("span", class_="UIuSk")
        for item in check:
            if "Contains ads" in item.get_text():
                return "Yes"
        return "No"

    def getIAPInfo(self):
        IAP_check = "No"
        check = self.store_page.findAll("span", class_="UIuSk")
        for item in check:
            if "In-app purchases" in item.get_text():
                IAP_check = "Yes"
        if IAP_check == "Yes":
            for selenium_item in self.expanded_details:
                if "In-app purchases" in selenium_item.text:
                    IAP_check += ", " + selenium_item.text[len("In-app purchases"):]
        return IAP_check

    def getPermissions(self):
        perm_list = ""

        for perm in self.expanded_permissions:
            perm_list += ", "
            if perm_list == ", ":
                perm_list = perm_list[:-2]
            perm_list += perm.text

        if perm_list == "":
            perm_list = "No permmissisons requested"

        return "Permissions: " + perm_list + "  "

    def getDescription(self):
        desc_strings = self.store_page.find("div", class_="bARER").stripped_strings
        desc = ''
        totalChar = 0
        totalLines = 0
        for s in desc_strings:
            desc += '>' + s + '  \n'
            totalChar += len(s)
            totalLines += 1
            if totalChar >= 400:
                break
            if totalLines >= 10:
                break
        return desc

    def __init__(self, submission, url):
        self.blacklist = False
        self.invalid = False
        self.submission = submission
        page = requests.get(url).text
        
        self.store_page = BeautifulSoup(page, "html.parser")
        self.name = self.getName()
        self.rating = self.getRating()
        try:
            self.developer = self.getDeveloper()
        except BlacklistedDev:
            self.blacklist = True
        self.price_info = self.getPriceInfo()
        self.play_pass = self.getPlayPass()
        self.desc = self.getDescription()
        self.url = url
        self.ads = self.getAds()

        self.selenium = webdriver.Firefox()
        self.selenium.get(url)
        time.sleep(5)
        details_button = self.selenium.find_element(By.XPATH, "/html/body/c-wiz[2]/div/div/div[1]/div[2]/div/div[1]/div[1]/c-wiz[2]/div/section/header/div/div[2]/button")
        details_button.click()
        time.sleep(1)
        
        self.expanded_details = self.selenium.find_elements(By.CLASS_NAME, "sMUprd")
        self.downloads = self.getNumDownloads()
        self.last_update = self.getLastUpdateDate()
        #self.size = self.getSize()
        self.IAP_info = self.getIAPInfo()
        
        permissions_button = self.selenium.find_element(By.CSS_SELECTOR, "span.TCqkTe")
        permissions_button.click()
        time.sleep(1)
        self.expanded_permissions = self.selenium.find_elements(By.CLASS_NAME, "aPeBBe")
        self.permissions = self.getPermissions()
        self.selenium.close()
    

def flair(app_rating, num_installs, sub):
    inst = num_installs.split("+")
    if (inst[0] == "Couldn't"):
        return
    try:
        val = int(inst[0].replace(',', ''))
    except (ValueError):
       return
    if val <= 500:
        sub.mod.flair(text='New app', css_class=None)
    elif val >= 100000 and int(app_rating[0:1]) >= 4:
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
^^^[Suggestions?](https://www.reddit.com/message/compose?to=Swimmer249)"""
    
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
        if not "http" in url or not "play.google" in url or "collection/cluster" in url:
            continue
        app = AppInfo(submission, url)
        if app.invalid:
            continue
        valid_apps.append(app)
        if len(valid_apps) >= 10:
            break

    if not submission.is_self:
        trimurl = submission.url.split("&")[0]
        if "collection/cluster" in trimurl:
            print("SKIPPING, COLLECTION: " + submission.title)
            logID(submission.id)
            return
        app = AppInfo(submission, trimurl)

    if len(valid_apps) == 1:
        app = valid_apps[0]

    if submission.is_self and len(valid_apps) == 0:
        print("All invalid links, skipping: " + submission.title)
        logID(submission.id)
        return
        
    if len(valid_apps) > 1:
        reply_text = ""
        for app_num in range(len(valid_apps)):
            if (app_num >= 10):
                break
            app = valid_apps[app_num]
            if app.blacklist:
                reply_text = "Sorry, deals from one or more of the developers in your post have been blacklisted. Here is the full list of blacklisted developers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"
                submission.mod.remove()
                submission.reply(body=reply_text).mod.distinguish()
                print("Removed (developer blacklist): " + submission.title)
                logID(submission.id)
                return
            reply_text += "Info for [%s](%s): Price (USD): %s | Rating: %s | Installs: %s | IAPs/Ads: %s/%s\n\n*****\n\n" % (app.name, app.url, app.price_info, app.rating, app.downloads, app.IAP_info, app.ads)
        if len(valid_apps) >= 10:
            reply_text += "...and more. Max of 10 apps reached.\n\n*****\n\n"
        reply_text += "If any of these deals have expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."
        reply_text += footer
        
        submission.reply(body=reply_text)
        
        print("Replied to: " + submission.title)
        logID(submission.id)
        return

    if not app.invalid:
        flair(app.rating, app.downloads, submission)

    if app.blacklist:
        reply_text = "Sorry, deals from one or more of the developers in your post have been blacklisted. Here is the full list of blacklisted developers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"
        submission.mod.remove()
        submission.reply(body=reply_text).mod.distinguish()
        print("Removed (developer blacklist): " + submission.title)
    elif app.invalid:
        print("INCORRECT LINK Skipping: " + submission.title)
    else:
        reply_text = """Info for %s:

Current price (USD): %s  %s
Developer: %s  
Rating: %s  
Installs: %s  
Last updated: %s  
Contains IAPs: %s  
Contains Ads: %s  
%s
Short description:  

%s  

***** 

If this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban.""" % (app.name, app.price_info, app.play_pass, app.developer, app.rating, app.downloads, app.last_update, app.IAP_info, app.ads, app.permissions, app.desc)
        reply_text += footer
        submission.reply(body=reply_text)
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
