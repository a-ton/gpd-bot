#### The Google Play Deals Bot does a few things for the /r/GooglePlayDeals subreddit:

* Responds to all app submissions on /r/GooglePlayDeals with information about the app found on the store page 
* Flairs deals when they are expired when users reply with "expired"
* Flairs deals with a new or popular tag based on the number of dowloads (New is <1,000 and popular is >10,000, and a 4 star rating)

#### These are the current features but here are a few more I would like to implement:

* Logging (errors) - Sort of implemented

### General workflow:

* reddit_response.py
  1. Monitors subreddit for new posts
  2. Scrape the google play link for info
  3. Reply to post and add flair
  
* msg_monitor.py
  1. Monitors inbox for unread comment replies
  2. Replies to comment, checks if it has expired, and flairs post
  3. Marks comment as read and moves on

### Needed modules

* PRAW 5.2.0+
* bs4

### Example response:
>Info for Lucid Launcher Pro:  
>Current price (USD): $1.49 was $2.99  
>Developer: Lucid Dev Team  
>Rating: 4.4/5  
>Installs: 10,000+  
>Size: 3.6M  
>Last updated: January 23, 2019  
>Contains IAPs: No  
>Contains Ads: No  
>Short description:

>>Lucid Launcher Pro unlocks various features for Lucid Launcher and will also receive updates earlier than the free version. If you want to request a feature please request at our Google+ page or Contact us via E-mail.  
>>Pro Version Unlocks:  
>>★Custom Search Text (Look at screenshots)  
>>★Ability to hide app label in favorites bar  
>>★More Page Transition Animations  
>>★Vertical Page Transitions  
>>★More Home Pages  
>>★Custom Sidebar Theme  

>(footer)

#### Other stuff

In order to run the bot, you need to fill out the Config.py file but currently we don't need another version of the bot running around so that probably won't matter. I'm uploading this to github for better version control and also because a few users have wanted to view the source of the bot. Any help would be appreciated if you want to contribute to the project. 

**Feel free to submit issues for ideas you have or issues with the bot!**
