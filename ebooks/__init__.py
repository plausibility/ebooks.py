# -*- coding: utf-8 -*-
from __future__ import print_function
import gevent.monkey
gevent.monkey.patch_all()

import gevent
import twitter

from collections import defaultdict
import random
import time
import json
import re

try:
    # Python2
    import HTMLParser
    unescape_html = HTMLParser.HTMLParser().unescape
except ImportError:
    # Python3
    import html.parser
    unescape_html = html.parser.HTMLParser().unescape

# change here, change in setup.py
__version__ = "0.1.1"

class Stop(object):
    # Why did I do this? I just like using my terminal.
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_stop_word"):
            cls._stop_word = super(Stop, cls).__new__(cls, *args, **kwargs)
        return cls._stop_word
    def __str__(self):
        return "<stop>"
    __repr__ = __str__

class Ebooks(object):
    """ Turn your crummy Twitter feed into a top lel _ebooks bot.

        Note: the markov stuff is built into this class, ooh err.
        It's available under _markov_*, but be warned - I might change
        those whenever I get temperamental about my code.

        auth - a dict with tuple/list information from the Twitter dev site:
            {("origin_account", "ebooks_account"): (OAUTH_TOKEN,
                                                    OAUTH_SECRET,
                                                    CONSUMER_KEY,
                                                    CONSUMER_SECRET)}
        dry - do everything, but actually interacting with Twitter.
        verbose - what it says on the tin, debug actually prints stuff.
        chain_length - the quality of the markov output.
            1 is complete gibberish
            2 is reasonably adequate
            3 is perfect (when it works at all)
    """
    auth = None
    dry = False
    verbose = False

    chain_length = 2
    max_words = 30

    def __init__(self):
        if self.auth is None or len(self.auth) == 0:
            raise RuntimeError("No auth given.")
        # Markov junk
        self.stop_word = Stop()
        self.markov = {}  # markov[ebook]
        # Ebooks junk
        self.length_cap = 140
        self.horse()

    def horse(self):
        self.names = {}
        self.t = {}
        self.seen = {}
        self.tweets = {}
        self.settings = {}
        for names, auth in self.auth.items():
            origin, ebooks = names
            self.add(origin, ebooks, auth)

    def _markov_split(self, message, chain_length):
        words = message.split()
        if len(words) < chain_length:
            return
        words.append(self.stop_word)
        for i in xrange(len(words) - chain_length):
            yield words[i:i + chain_length + 1]

    def _markov_add(self, ebooks, message, chain_length):
        s = self.markov[ebooks]
        for words in self._markov_split(message, chain_length):
            key = tuple(words[:-1])
            s.setdefault(key, [])
            s[key].append(words[-1])
        return s

    def _markov_gen(self, ebooks, seed=None, chain_length=None):
        if seed is None:
            seed = random.choice(self.tweets[ebooks])["text"]
        if chain_length is None:
            chain_length = self.chain_length
        key = seed.split()[:chain_length]
        gen_words = []
        self.debug(ebooks, seed, key, chain_length)
        for i in xrange(self.max_words):
            gen_words.append(key[0])
            if len(" ".join(gen_words)) > self.length_cap:
                # TODO: this makes the chain crap. What can we do?
                gen_words.pop(-1)
                break
            try:
                next_word = self.markov[ebooks][tuple(key)]
            except KeyError:
                # bail bail bail bail!
                break
            if not next_word:
                break
            next = random.choice(next_word)
            key = key[1:] + [next]
            if next is self.stop_word:
                gen_words.append(key[0])
                break
        message = " ".join(gen_words)  # Join the list
        message = re.sub(r"(?:\.)?@([^\s]+)", r"#\1", message)  # Butcher mentions
        message = unescape_html(message)  # Escape HTML codes
        return message.strip()

    # Ebooks junk
    def add(self, origin, ebooks, auth):
        self.names[ebooks] = origin
        self.t[ebooks] = None if self.dry else twitter.Twitter(auth=twitter.OAuth(*auth))
        self.seen[ebooks] = 0
        self.tweets[ebooks] = self.load(ebooks)
        if len(self.tweets[ebooks]) > 0:
            self.seen[ebooks] = self.tweets[ebooks][-1]["id"]
        self.settings[ebooks] = None if self.dry else self.t[ebooks].account.settings()
        # Markov junk
        self.markov[ebooks] = {}
        for tweet in self.tweets[ebooks]:
            self._markov_add(ebooks, tweet["text"], self.chain_length)

    def load(self, ebooks):
        origin = self.names[ebooks]
        try:
            with open("{0}.json".format(origin), "rb") as f:
                loaded = json.loads(f.read())
                self.seen[ebooks] = loaded["seen"]
                return loaded["tweets"]
        except IOError:
            # We can't find the brain!
            return []

    def save(self, ebooks, tweets=None):
        if tweets is None:
            tweets = self.tweets[ebooks]
        origin = self.names[ebooks]
        self.debug(ebooks, "Saving brain of:", origin)
        with open("{0}.json".format(origin), "wb") as f:
            json.dump({"tweets": tweets, "seen": self.seen[ebooks]}, f, indent=4)

    def fetch(self, ebooks=None):
        if ebooks is None:
            ebooks = self.names.keys()
        for ebook in ebooks:
            origin = self.names[ebook]
            bits = {"screen_name": origin, "include_rts": "false", "count": 200}
            if self.seen[ebook]:
                bits["since_id"] = self.seen[ebook]
            self.debug(ebook, "**bits:?", bits)
            tweets = self.t[ebook].statuses.user_timeline(**bits)
            self.debug(ebook, "Found", len(tweets), "new tweets")
            if len(tweets) > 0:
                self.seen[ebook] = tweets[0]["id"]
            self.debug(ebook, "Last tweet:", self.seen[ebook])
            self.tweets[ebook].extend([{"id":tweet["id"], "text":tweet["text"]} for tweet in tweets])
            self.save(ebook)

    def debug(self, ebooks, *msg):
        if not self.verbose:
            return
        print(u"[@{0}] {1}".format(ebooks, u" ".join(map(unicode, msg))))

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