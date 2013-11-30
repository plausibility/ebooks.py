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

class Ebooks(object):
    """ Turn your crummy Twitter feed into a top lel _ebooks bot.
        Note: the markov stuff is built into this class, ooh err.

        auth - a dict with tuple/list information from the Twitter dev site:
            {("origin_account", "ebooks_account"): (OAUTH_TOKEN,
                                                    OAUTH_SECRET,
                                                    CONSUMER_KEY,
                                                    CONSUMER_SECRET)}
        dry - do everything, but don't actually *send* the tweets.
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
        self.stop_word = "\n"
        self.markov = {}  # markov[ebook]
        # Ebooks junk
        self.length_cap = 140
        self.names = {}
        self.t = {}
        self.seen = {}
        self.tweets = {}
        self.settings = {}
        for names, auth in self.auth.items():
            origin, ebooks = names
            self.add(origin, ebooks, auth)

    # Markov junk
    def mk_add(self, ebooks, msg, chain_length):
        if len(msg) < 1:
            return
        buf = [self.stop_word] * chain_length
        self.debug(ebooks, "mk_add:", msg)
        for word in msg.split():
            self.markov[ebooks][tuple(buf)].append(word)
            del buf[0]
            buf.append(word)
        self.debug(ebooks, repr(self.markov[ebooks][tuple(buf)]), repr(buf))
        self.markov[ebooks][tuple(buf)].append(self.stop_word)

    def mk_gen(self, origin, msg=None, chain_length=None, max_words=None, recurse=0):
        """ Give this bad boy the `origin` name and it'll spit you out some
            random sentence. IDK man, markov chains are weird.

            Optionally, seed it with a `msg`.

            If `recurse` is a positive number, it will try up to n times to
            recurse again until it gets a different message.
        """
        #if ebooks in self.names.values():
        #    ebooks = [k for k, v in self.names.items() if v == ebooks][0]
        ebooks = [k for k, v in self.names.items() if v == origin][0]
        if msg is None:
            # This just does... anything, really.
            msg = random.choice(self.tweets[ebooks])["text"]
            self.debug(ebooks, "msg~:", msg)
        if chain_length is None:
            chain_length = self.chain_length
        if max_words is None:
            max_words = self.max_words
        buf = msg.split()[:chain_length]
        if len(msg.split()) > chain_length:
            message = buf[:]
        else:
            message = []
            for i in xrange(chain_length):
                try:
                    message.append(
                        random.choice(
                            self.markov[ebooks][
                                random.choice(self.markov[ebooks].keys())
                            ]
                        )
                    )
                except IndexError:
                    self.debug(ebooks, "Got an index error, chump.")
                    #self.debug(ebooks, self.markov[ebooks].keys())
                    continue
            self.debug(ebooks, "mk_gen seeder:", message)
        for i in xrange(max_words):
            try:
                next_word = random.choice(self.markov[ebooks][tuple(buf)])
            except IndexError:
                self.debug(ebooks, "Another index error:", repr(tuple(buf)), self.markov[ebooks][tuple(buf)])
                continue
            self.debug(ebooks, "broke through")
            if next_word == self.stop_word:
                self.debug(ebooks, "breakin'", i)
                break
            message.append(next_word)
            if len(" ".join(message + [next_word])) > self.length_cap:
                break
            del buf[0]
            buf.append(next_word)
            self.debug(ebooks, "buf[-1]", repr(buf[-1]), "message[-1]", repr(message[-1]))
        if msg == " ".join(message):
            if recurse > 0:
                return self.mk_gen(origin, msg=msg, chain_length=chain_length, max_words=max_words, recurse=recurse-1)
            self.debug(ebooks, "MSG IS THE SAME, OH DARN")
            return True
        message = filter(lambda s: s != "\n", message)  # Remove newlines
        message = " ".join(message)  # Join the list
        message = re.sub(r"(?:\.)?@([^\s]+)", r"#\1", message)  # Butcher mentions
        message = unescape_html(message)  # Escape HTML codes
        return message.strip()

    # Ebooks junk
    def add(self, origin, ebooks, auth):
        self.names[ebooks] = origin
        self.t[ebooks] = twitter.Twitter(auth=twitter.OAuth(*auth))
        self.seen[ebooks] = 0
        self.tweets[ebooks] = self.load(ebooks)
        #if len(self.tweets[ebooks]) > 0:
        #    self.seen[ebooks] = self.tweets[ebooks][-1]["id"]
        self.settings[ebooks] = self.t[ebooks].account.settings()
        # Markov junk
        self.markov[ebooks] = defaultdict(list)
        for tweet in self.tweets[ebooks]:
            self.mk_add(ebooks, tweet["text"], self.chain_length)

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
        print(u"[{0}] {1}".format(ebooks, u" ".join(map(unicode, msg))))

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