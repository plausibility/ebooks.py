# -*- coding: utf-8 -*-
from __future__ import print_function
import gevent.monkey
gevent.monkey.patch_all()

import gevent
import twitter

import time
import json
import re


# change here, change in setup.py
__version__ = "0.1.0"


class Ebooks(object):
    """
        auth - a dict with tuple/list information from the Twitter dev site:
            {("origin_account", "ebooks_account"): (OAUTH_TOKEN,
                                                    OAUTH_SECRET,
                                                    CONSUMER_KEY,
                                                    CONSUMER_SECRET)}
        dry - do everything, but don't actually *send* the tweets.
    """
    auth = None
    dry = False

    def __init__(self):
        if self.auth is None or len(self.auth) == 0:
            raise RuntimeError("No auth given.")
        self.names = {}
        self.t = {}
        self.seen = {}
        self.tweets = {}
        self.settings = {}
        for names, auth in self.auth.items():
            origin, ebooks = names
            self.add(origin, ebooks, auth)

    def add(self, origin, ebooks, auth):
        self.names[ebooks] = origin
        self.t[ebooks] = twitter.Twitter(auth=twitter.OAuth(*auth))
        self.seen[ebooks] = 0
        self.tweets[ebooks] = self.load(ebooks)
        if len(self.tweets[ebooks]) > 0:
            self.seen[ebooks] = self.tweets[ebooks][-1]["id"]
        self.settings[ebooks] = self.t[ebooks].account.settings()

    def load(self, ebooks):
        try:
            with open("{0}.json".format(ebooks), "rb") as f:
                loaded = json.loads(f.read())
                return loaded["tweets"]
        except IOError:
            # We can't find the brain!
            return []

    def save(self, ebooks, tweets=None):
        if tweets is None:
            tweets = self.tweets[ebooks]
        self.debug(ebooks, "Saving brain")
        with open("{0}.json".format(ebooks), "wb") as f:
            json.dump({"tweets": tweets}, f, indent=4)

    def fetch(self, ebooks=None):
        if ebooks is None:
            ebooks = self.names.keys()
        for ebook in ebooks:
            origin = self.names[ebook]
            tweets = self.t[ebook].statuses.user_timeline(
                user_id=origin,
                since_id=self.seen[ebook],
                include_rts="false"
            )
            self.debug(ebook, "Found", len(tweets), "new tweets")
            self.seen[ebook] = tweets[-1]["id"]
            self.debug(ebook, "Last tweet:", self.seen[ebook])
            self.tweets[ebook].extend([{"id":tweet["id"], "text":tweet["text"]} for tweet in tweets])
            self.save(ebook)

    def debug(self, ebooks, *msg):
        print("[{0}] {1}".format(ebooks, " ".join(map(str, msg))))

    """
    def _fetch_tweets(self):
        tweets = self.t.search.tweets(q=" OR ".join(self.phrases), lang="en")
        for t in tweets['statuses']:
            if self.queue.qsize() >= self.max_queue:
                break
            # Why single rather than stacked? It's cleaner.
            if self._in_reply_to_us(t):
                continue
            if self._from_us(t):
                continue
            if self._is_retweet(t):
                continue
            if not self.ignore_display_names and self._is_display_name(t):
                continue
            if t['id'] in self.seen:
                continue

            self.seen.append(t['id'])
            self.queue.put_nowait(t)
        self._next_fetch = time.time() + self._cooldown_fetch

    def do_loop(self):
        # Actually start our produce loop.
        self.producer = gevent.spawn(self._produce)
        while True:
            if self.queue.empty():
                gevent.sleep(0)
            if self._next_tweet > time.time():
                gevent.sleep(0)
                continue
            task = self.queue.get()
            self.take_action(task['text'], task['user']['screen_name'], task['id'])
            self._next_tweet = time.time() + self._cooldown_tweet
    """