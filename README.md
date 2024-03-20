#### The Google Play Deals Bot does a few things for the /r/GooglePlayDeals subreddit:

* Responds to all app submissions on /r/GooglePlayDeals with information about the app found on the store page
* Flairs deals when they are expired when users reply with "expired"
* Flairs deals with a new or popular tag based on the number of downloads (New is <1,000 and popular is >10,000, and a 4 star rating)
* Can also respond to self text posts that contain links to more than 1 app.

#### These are the current features but here are a few more I would like to implement:

* Logging (errors) - Sort of implemented

### General workflow:

* reddit_response.py
  1. Monitors subreddit for new posts
  2. Scrapes the google play link for information using bs4 and Selenium
  3. Reply to post and add flair

* msg_monitor.py
  1. Monitors inbox for unread comment replies
  2. Replies to comment, checks if it has expired, and flairs post
  3. Marks comment as read and moves on

### Needed modules

* PRAW 5.2.0+
* bs4
* selenium
* Firefox browser and selenium driver

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

### Running with Docker

The Docker image at [ghcr.io/a-ton/gpd-bot](ghcr.io/a-ton/gpd-bot) is built for ARMv7, ARM64v8 and AMD64, so it can be run on most hardware (including a Raspberry Pi).

You can run the following commands to clone the repo, change directories, and then copy and edit the `.env` file for use with the bot:
```bash
git clone https://github.com/a-ton/gpd-bot.git
cd gpd-bot
cp .env.example .env
nano .env

```

Using [Docker Compose](https://docs.docker.com/compose/) is the preferred method to run the bot.

The container can be brought up with by running `docker compose up -d` while in the root directory (where this README.md file is).

This will start the container in a detached mode. Output/logs can be viewed with `docker logs -f gpd-bot`.

#### Other stuff


In order to run the bot, you need to copy `.env.example`, rename to `.env`, and fill out the variables. Currently we don't need another version of the bot running around so that probably won't matter. I'm uploading this to github for better version control and also because a few users have wanted to view the source of the bot. Any help would be appreciated if you want to contribute to the project.

### Running with Docker

Uhhhhh until the PR is completed and polished, I'm gonna just brain dump.

Assuming you already have the repo cloned, navigate to the folder and copy the example `.env` file with the following (and modify it): `cp .env.example .env && nano .env`

`docker-compose` is preferred, and can be run with `docker compose up -d`. This will build the container locally, and then start it in a detached mode. Logs can be viewed with `docker logs -f gpd-bot`.

If you want to re-build the container, run the following sequence to tear down the old container, rebuild, and bring up the new container: `docker compose down && docker compose build && docker compose up -d`.

**Feel free to submit issues for ideas you have or issues with the bot!**
