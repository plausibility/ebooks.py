ebooks.py
=========

Python based multiple-account-using, markov-tweeting, hamburger-eating CHAMPION OF THE WORLDDDD!

Todo
----

+ [ ] Add Py3k compatibility with Flask's `_compat.py` cheatorama.
+ [x] Get gevent-based tweeting actually going. (we're no longer using gevent)
+ [x] Move configuration into some sneaky attributes on the subclass (then use `inspect.getmembers()` to find them)
+ [x] Tidy shit up.
+ [x] Add example use file.

Example
-------

The general idea is that you subclass `ebooks.Ebooks`, then you can create an instance and call `e.loop()` to get into the tweet loop.

You inform ebooks.py what accounts to pull from and send to via attributes on the class that start with `t_`, as such:

```python
from ebooks import Ebooks

class MyBooks(Ebooks):
    t_someguy = {
        "auth": (OAUTH_TOKEN,
                 OAUTH_SECRET,
                 CONSUMER_KEY,
                 CONSUMER_SECRET),
        "chain_length": 2  # optional
    }

    t_some_other_guy = {
        # ...as above...
    }

    # These are all optional, with defaults shown:
    dry = False
    verbose = False

    chain_length = 2
    max_words = 30
    length_cap = 140

    timer_fetch = 60 * 5
    timer_tweet = 60 * 10

if __name__ == "__main__":
    e = MyBooks()
    e.loop()
```

In this example, you're pulling tweets from `@someguy` (as shown by `t_someguy`) and sending them to whatever account your OAuth tokens provide access to.
You can add multiple accounts (e.g. this will also ebooksify `@some_other_guy`) by simply adding more attributes.

Other settings are fairly self-explanatory, but here's some explanation regardless:

+ `dry` - this will do everything normally except for interacting with Twitter
+ `verbose` - debug info will be printed to stdout
+ `chain_length` - markov chain length (2 is fairly average)
+ `max_words` - how many words we're aiming for in the tweet (an upper bound).
+ `length_cap` - how long tweets can be
+ `timer_fetch` - how often (in seconds) we should fetch tweets
+ `timer_tweet` - how often (in seconds) we should send tweets