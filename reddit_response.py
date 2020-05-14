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
    def getAPIResponse(self, url):
        temp = url.split('?')
        stripped_id = temp[1].split('&')
        app_id = stripped_id[0][3:]
        
        req_params = {"country": "US"}
        api = Config.permissions_api
        url = "https://api.appmonsta.com/v1/stores/android/details/%s.json" % app_id
        headers = {'Accept-Encoding': 'deflate, gzip'}
        response = requests.get(url,
                                auth=(api, ""),
                                params=req_params,
                                headers=headers,
                                stream=True).json()

        try:
            response["message"]
            raise LinkError
        except KeyError:
            return response

    def getName(self):
        return self.APIResponse["app_name"]

    def getNumDownloads(self):
        response = self.APIResponse
        if len(response["downloads"]) == 0:
            return "Not availible"
        else:
            return response["downloads"]

    def getRating(self):
        temp = self.APIResponse["all_rating"]
        if not isinstance(temp, float):
            return "No ratings yet!"
        rating = str(temp) + "/5"
        return rating

    def getDeveloper(self):
        return self.APIResponse["publisher_name"]

    def getLastUpdateDate(self):
        return self.APIResponse["status_date"]

    def getSize(self):
        return self.APIResponse["file_size"]

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
        iap_scripts = self.store_page.find_all('script', text=re.compile(r'"In-app purchases"'))
        if len(iap_scripts) > 0:
            return 'Yes'
        return 'No'

    def getAds(self):
        ads_scripts = self.store_page.find_all('script', text=re.compile(r'"Contains ads"'))
        if len(ads_scripts) > 0:
            return 'Yes'
        return 'No'

    def getIAPInfo(self):
        response = self.APIResponse
        if len(response["iap_price_range"]) == 0:
            return response["iap_price_range"]
        else:
            return ", " + response["iap_price_range"]

    def getPermissions(self):
        response = self.APIResponse
        perm_list = "Permissions: "

        try:
            if "read the contents of your USB storage" in response["permissions"]:
                perm_list += "Read/Modify Storage, "
        except KeyError: 
            return ""

        if "read your text messages (SMS or MMS)" in response["permissions"]:
            perm_list += "Read/Send SMS, "

        if "record audio" in response["permissions"]:
            perm_list += "Record Audio, "

        if ("precise location (GPS and network-based)" in response["permissions"]) or ("approximate location (network-based)" in response["permissions"]):
            perm_list += "Location Access, "

        if "take pictures and videos" in response["permissions"]:
            perm_list += "Access Camera, "

        if "view network connections" in response["permissions"]:
            perm_list += "View Wi-Fi Info, "

        if "retrieve running apps" in response["permissions"]:
            perm_list += "Device & App History, "

        if "find accounts on the device" in response["permissions"]:
            perm_list += "Read Identity & Contacts, "
        
        if perm_list == "Permissions: ":
            return "Permissions: No major permissions requested.  "

        return perm_list[:-2] + "  "

    def getDescription(self):
        desc_strings = self.store_page.find("div", jsname="sngebd").stripped_strings
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

        APISuccess = False
        while(not APISuccess):
            try:
                self.APIResponse = self.getAPIResponse(url)
                APISuccess = True
            except LinkError:
                self.invalid = True
                return
            except requests.exceptions.ConnectionError:
                print("API Connection Error, waiting 5 minutes...")
                time.sleep(300)
        
        self.store_page = BeautifulSoup(page, "html.parser")
        self.list_of_details = self.store_page.findAll(attrs={"class": "htlgb"}) 
        self.name = self.getName()
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
        if self.IAPs == "Yes":
            self.IAP_info = self.getIAPInfo()
        else:
            self.IAP_info = ""
        self.desc = self.getDescription()
        self.url = url
        self.permissions = self.getPermissions()
    

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
    elif val >= 10000 and int(app_rating[0:1]) >= 4:
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
        if not "http" in url:
            continue
        app = AppInfo(submission, url)
        if app.invalid:
            continue
        valid_apps.append(app)
        if len(valid_apps) >= 10:
            break

    if not submission.is_self:
        trimurl = submission.url.split("&")[0]
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
                submission.reply(reply_text).mod.distinguish()
                print("Removed (developer blacklist): " + submission.title)
                logID(submission.id)
                return
            reply_text += "Info for [%s](%s): Price (USD): %s was %s | Rating: %s | Installs: %s | Size: %s | IAPs/Ads: %s%s/%s\n\n*****\n\n" % (app.name, app.url, app.current_price, app.full_price, app.rating, app.downloads, app.size, app.IAPs, app.IAP_info, app.ads)
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
        reply_text = """Info for %s:

Current price (USD): %s was %s  
Developer: %s  
Rating: %s  
Installs: %s  
Size: %s  
Last updated: %s  
Contains IAPs: %s%s  
Contains Ads: %s  
%s
Short description:  

%s  

***** 

If this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban.""" % (app.name, app.current_price, app.full_price, app.developer, app.rating, app.downloads, app.size, app.last_update, app.IAPs, app.IAP_info, app.ads, app.permissions, app.desc)
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
