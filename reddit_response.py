import time
import praw
import prawcore
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import urllib
import urllib.request
from dotenv import load_dotenv
import os
import json
load_dotenv()
reddit = praw.Reddit()
subreddit = reddit.subreddit(os.getenv('GPD_SUBREDDIT'))

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
        return self.store_page.find("h1", class_="Fd93Bb").get_text()

    def get_downloads(self):
        for item in self.expanded_details:
            if "Downloads" in item.text:
                downloads = item.text[len("Downloads"):]
                return downloads
        return "Couldn't get downloads"

    def get_rating(self):
        try:
            rating = self.store_page.find("div", class_="TT9eCd").get_text()
        except AttributeError:
            return "NA    "
        return rating[:-4] + "/5"

    def get_developer(self):
        dev = self.store_page.find("div", class_="Vbfug auoIOc")
        dev_url = dev.find("a").get("href")
        if dev.get_text() in json.load(os.environ["GPD_BLACKLISTED_DEVS"]):
            raise BlacklistedDev
        return "[" + dev.get_text() + "]" + "(https://play.google.com" + dev_url + ")"

    def get_update_date(self):
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
        try:
            sale_price = split_price[1]
        except IndexError:
            sale_price = "Buy"
        if sale_price == "Buy":
            sale_price = full_price
        if sale_price == "Install":
            sale_price = "Free"
        if full_price == "Install":
            full_price = "Free"
        return sale_price + " was " + full_price


    def get_play_pass(self):
        play_pass = self.store_page.find("a", class_="pFise")
        if play_pass:
            return "\n**Included with Play Pass**  "
        return ""

    def get_ads(self):
        check = self.store_page.findAll("span", class_="UIuSk")
        for item in check:
            if "Contains ads" in item.get_text():
                return "Yes"
        return "No"

    def get_iap_info(self):
        iap_info = "No"
        check = self.store_page.findAll("span", class_="UIuSk")
        for item in check:
            if "In-app purchases" in item.get_text():
                iap_info = "Yes"
        if iap_info == "Yes":
            for selenium_item in self.expanded_details:
                if "In-app purchases" in selenium_item.text:
                    iap_info += ", " + selenium_item.text[len("In-app purchases"):]
        return iap_info

    def get_permissions(self):
        perm_list = ""

        for perm in self.expanded_permissions:
            perm_list += ", "
            if perm_list == ", ":
                perm_list = perm_list[:-2]
            perm_list += perm.text

        if perm_list == "":
            perm_list = "No permmissisons requested"

        return "Permissions: " + perm_list + "  "

    def get_description(self):
        desc_strings = self.store_page.find("div", class_="bARER").stripped_strings
        desc = ''
        total_chars = 0
        total_lines = 0
        for string in desc_strings:
            desc += '>' + string + '  \n'
            total_chars += len(string)
            total_lines += 1
            if total_chars >= 400:
                break
            if total_lines >= 10:
                break
        return desc

    def __init__(self, submission, url):
        self.blacklist = False
        self.invalid = False
        self.submission = submission
        page = requests.get(url).text

        self.store_page = BeautifulSoup(page, "html.parser")
        self.name = self.getName()
        self.rating = self.get_rating()
        try:
            self.developer = self.get_developer()
        except BlacklistedDev:
            self.blacklist = True
        self.price_info = self.getPriceInfo()
        self.play_pass = self.get_play_pass()
        self.description = self.get_description()
        self.url = url
        self.ads = self.get_ads()

        self.selenium = webdriver.Firefox()
        self.selenium.get(url)
        time.sleep(5)
        details_button = self.selenium.find_element(By.XPATH, "/html/body/c-wiz[2]/div/div/div[1]/div/div[2]/div/div[1]/div[1]/c-wiz[3]/div/section/header/div/div[2]/button/i")
        details_button.click()
        time.sleep(1)

        self.expanded_details = self.selenium.find_elements(By.CLASS_NAME, "sMUprd")
        self.downloads = self.get_downloads()
        self.last_update = self.get_update_date()
        #self.size = self.getSize()
        self.iap_info = self.get_iap_info()

        permissions_button = self.selenium.find_element(By.CSS_SELECTOR, "span.TCqkTe")
        permissions_button.click()
        time.sleep(1)
        self.expanded_permissions = self.selenium.find_elements(By.CLASS_NAME, "aPeBBe")
        self.permissions = self.get_permissions()
        self.selenium.close()


def flair(app_rating, num_installs, sub):
    inst = num_installs.split("+")
    if inst[0] == "Couldn't":
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

    all_urls = []
    if submission.is_self:
        all_urls = re.findall('(?:(?:https?):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+', submission.selftext)
        if len(all_urls) == 0:
            print("NO LINK FOUND skipping: " + submission.title)
            logID(submission.id)
            return
    else:
        all_urls.append(submission.url)

    # remove duplicate URLs
    unique_urls = [*set(all_urls)]

    # find apps that we can respond to
    valid_apps = []
    required_url = ["http", "play.google"]
    disallowed_url = ["collection/cluster", "dev?id=", "store/search"]
    for url in unique_urls:
        # check if strings in required_url are part of url and if strings in disallowed_url do not exist in url
        if not all(x in url for x in required_url):
            continue
        if any(x in url for x in disallowed_url):
            continue
        app = AppInfo(submission, url)
        if app.blacklist:
            reply_text = "Sorry, deals from one or more of the developers in your post have been blacklisted. Here is the full list of blacklisted developers: https://www.reddit.com/r/googleplaydeals/wiki/blacklisted_devlopers"
            submission.mod.remove()
            submission.reply(body=reply_text).mod.distinguish()
            print("Removed (developer blacklist): " + submission.title)
            logID(submission.id)
            return
        if app.invalid:
            continue
        valid_apps.append(app)
        if len(valid_apps) >= 10:
            break

    if len(valid_apps) == 0:
        print("All invalid links, skipping: " + submission.title)
        logID(submission.id)
        return

    reply_text = ""

    if len(valid_apps) == 1:
        flair(app.rating, app.downloads, submission)

        reply_text = f"""Info for {app.name}:

Current price (USD): {app.price_info}  {app.play_pass}
Developer: {app.developer}
Rating: {app.rating}
Installs: {app.downloads}
Last updated: {app.last_update}
Contains IAPs: {app.iap_info}
Contains Ads: {app.ads}
{app.permissions}
Short description:

{app.description}

*****

If this deal has expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."""


    if len(valid_apps) > 1:
        reply_text = ""
        for app_num, app in enumerate(valid_apps):
            if app_num >= 10:
                break
            reply_text += f"Info for [{app.name}]({app.url}): Price (USD): {app.price_info} | Rating: {app.rating} | Installs: {app.downloads} | Updated: {app.last_update} | IAPs/Ads: {app.iap_info}/{app.ads}\n\n*****\n\n"
        if len(valid_apps) >= 10:
            reply_text += "...and more. Max of 10 apps reached.\n\n*****\n\n"
        reply_text += "If any of these deals have expired, please reply to this comment with \"expired\". ^^^Abuse ^^^will ^^^result ^^^in ^^^a ^^^ban."

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
