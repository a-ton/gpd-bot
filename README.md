#### The Google Play Deals Bot does two things for the /r/GooglePlayDeals subreddit:

* Responds to all app submissions on /r/GooglePlayDeals with information about the app found on the store page 
* Flairs deals when they are expired 
* Flairs deals with a new or popular tag

#### These are the current features but here are a few more I would like to implement:

* Logging (errors, ~post ids~)
* Getting links from text posts
* (more to come when I remember them)

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

#### Other stuff

In order to run the bot, you need to fill out the Config.py file but currently we don't need another version of the bot running around so that probably won't matter. I'm uploading this to github for better version control and also because a few users have wanted to view the source of the bot. Any help would be appreciated if you want to. (first time writing Python) **Feel free to submit issues for stuff you want to see added and I'll let you know if it's feasible!** Line 28
