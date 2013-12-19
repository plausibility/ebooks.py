# -*- coding: utf-8 -*-
from __future__ import print_function

from ._compat import (PY2, unicode_type, iterrange)

import twitter

from datetime import datetime
import inspect
import random
import time
import json
import re

if PY2:
    import HTMLParser
    unescape_html = HTMLParser.HTMLParser().unescape
else:
    import html.parser
    unescape_html = html.parser.HTMLParser().unescape

# change here, change in setup.py
__version__ = "0.2.2"


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

        t_* - how you add accounts, in the format of:
            t_foobar = {
                "auth": (OAUTH_TOKEN,
                         OAUTH_SECRET,
                         CONSUMER_KEY,
                         CONSUMER_SECRET),
            }
        dry* - do everything, except for actually interacting with Twitter.
        verbose - what it says on the tin, debug actually prints stuff.
        chain_length* - the quality of the markov output.
            1 is complete gibberish
            2 is reasonably adequate
            3 is perfect (when it works at all)
        timer_fetch - how often we should fetch tweets (in seconds)
        timer_tweet - how often we should send tweets (in seconds)
    """
    dry = False
    verbose = False

    chain_length = 2
    max_words = 30
    length_cap = 140

    timer_fetch = 60 * 5
    timer_tweet = 60 * 10

    def __init__(self):
        # if self.auth is None or len(self.auth) == 0:
        #     raise RuntimeError("No auth given.")
        self.stop_word = Stop()
        self.markov = {}
        self._next_tweet = 0
        self._next_fetch = 0
        if self.dry:
            self.debug("@", "we're dry")
        self.horse()

    def horse(self):
        # source info dictionaries
        self.sources = {}
        # twitter.Twitter instances
        self.t = {}
        # last seen tweet id
        self.seen = {}
        # list of tweets
        self.tweets = {}

        for name, info in inspect.getmembers(self):
            if not name.startswith("t_") or not name[2:].strip():
                continue
            source = name[2:].strip()
            if not "auth" in info or len(info["auth"]) != 4:
                self.debug(source, "no/invalid auth, not interested")
                continue
            self.debug(source, "interested!")
            info.setdefault("dry", self.dry)
            info.setdefault("ebooks", None)
            info.setdefault("chain_length", self.chain_length)
            self.sources[source] = info
            self.add(source, info["auth"], info["chain_length"], info=info)

    def add(self, source, auth, chain_length, info=None):
        self.t[source] = None if info["dry"] else twitter.Twitter(auth=twitter.OAuth(*auth))
        self.seen[source] = 0
        self.tweets[source] = self.load(source)
        self.markov[source] = {}
        self.recalibrate(source, chain_length)

    def recalibrate(self, source, chain_length=None):
        self.debug(source, "recalibrating")
        if chain_length is None:
            chain_length = self.sources[source]["chain_length"]
        self.markov[source] = {}
        for tweet in self.tweets[source]:
            self._markov_add(source, tweet["text"], chain_length)

    def _markov_split(self, message, chain_length):
        words = message.split()
        if len(words) < chain_length:
            return
        words.append(self.stop_word)
        for i in iterrange(len(words) - chain_length):
            yield words[i:i + chain_length + 1]

    def _markov_add(self, source, message, chain_length):
        s = self.markov[source]
        for words in self._markov_split(message, chain_length):
            key = tuple(words[:-1])
            s.setdefault(key, [])
            s[key].append(words[-1])
        return s

    def _markov_gen(self, source, seed=None, chain_length=None):
        if seed is None:
            seed = random.choice(self.tweets[source])["text"]
        if chain_length is None:
            chain_length = self.sources[source]["chain_length"]
        key = seed.split()[:chain_length]
        gen_words = []
        self.debug(source, seed, key, chain_length)
        # max_words - 1 makes the chain nicer and not 2long2tweet.
        for i in iterrange(self.max_words -1):
            gen_words.append(key[0])
            if len(" ".join(gen_words)) > self.length_cap:
                self.debug(source, "adding", gen_words[-1], "is 2long2tweet")
                gen_words.pop(-1)
                break
            try:
                next_word = self.markov[source][tuple(key)]
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
        message = " ".join(gen_words)
        if message == seed:
            self.debug(source, "aw flip, it's the same.")
        # This will butcher mentions
        message = re.sub(r"(?:\.)?@([^\s]+)", r"#\1", message)
        message = unescape_html(message)
        return message.strip()

    def load(self, source):
        try:
            with open("{0}.json".format(source), "rb") as f:
                # Py3k compat.
                loaded = json.loads(f.read().decode("utf-8"))
                self.seen[source] = loaded["seen"]
                return loaded["tweets"]
        except IOError:
            # We can't find the brain!
            return []

    def save(self, source, tweets=None, indent=None):
        if tweets is None:
            tweets = self.tweets[source]
        self.debug(source, "saving brain")
        with open("{0}.json".format(source), "wb") as f:
            data = {"source": source, "tweets": tweets, "seen": self.seen[source]}
            if PY2:
                json.dump(data, f, indent=indent)
            else:
                f.write(bytes(json.dumps(data, indent=indent), "UTF-8"))

    def fetch(self, sources=None):
        if sources is None:
            sources = self.sources.keys()
        self.debug("@", "fetching ", len(sources), "accounts")
        for source in sources:
            if self.t[source] is None:
                self.debug(source, "no twitter inst. wut?")
                continue
            bits = {"screen_name": source, "include_rts": "false", "count": 200}
            if self.seen[source]:
                bits["since_id"] = self.seen[source]
            self.debug(source, "**bits:?", bits)
            tweets = self.t[source].statuses.user_timeline(**bits)
            self.debug(source, "found", len(tweets), "new tweets")
            self.debug(source, "last tweet:", self.seen[source])
            self.tweets[source].extend([
                {"id":tweet["id"], "text":tweet["text"]}
                for tweet in tweets
                if tweet["id"] > self.seen[source]
            ])
            if len(tweets) > 0:
                self.seen[source] = tweets[0]["id"]
            self.save(source)
            self.recalibrate(source)

    def tweet(self, sources=None):
        if sources is None:
            sources = self.sources.keys()
        self.debug("@", "tweeting to", len(sources), "accounts")
        for source in sources:
            if self.t[source] is None:
                self.debug(source, "no twitter inst. wtf?")
                continue
            status = self._markov_gen(source)
            self.debug(source, "tweeting:", status)
            self.t[source].statuses.update(status=status)

    def loop(self):
        while True:
            if time.time() > self._next_fetch:
                self.debug("@", "fetch time!")
                self.fetch()
                self._next_fetch = time.time() + self.timer_fetch
            if time.time() > self._next_tweet:
                self.debug("@", "tweet time!")
                self.tweet()
                self._next_tweet = time.time() + self.timer_tweet
            time.sleep(1)

    def debug(self, source, *msg):
        if not self.verbose:
            return
        print(unicode_type("[{0!s} @{1}] {2}").format(datetime.now(), source, unicode_type(" ").join(map(unicode_type, msg))))
