import os


def _env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


cid = _env("REDDIT_CLIENT_ID", required=True)
secret = _env("REDDIT_CLIENT_SECRET", required=True)
agent = _env("REDDIT_USER_AGENT", "python:gpd-bot:1.0 (by /u/GPDBot)")
user = _env("REDDIT_USERNAME", required=True)
password = _env("REDDIT_PASSWORD", required=True)
subreddit = _env("REDDIT_SUBREDDIT", "googleplaydeals")
postids_file = _env("POSTIDS_FILE", "postids.txt")
firefox_binary = _env("FIREFOX_BINARY")
blacklisted_devs = [
    item.strip()
    for item in _env("BLACKLISTED_DEVS", "").split(",")
    if item.strip()
]
