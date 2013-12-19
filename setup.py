from setuptools import setup

kw = {
    "name": "ebooks",
    "version": "0.2.2",
    "description": 'Markov Twitter bot',
    "long_description": "Python based multiple-account-using, markov-tweeting, hamburger-eating CHAMPION OF THE WORLDDDD!",
    "url": "https://github.com/plausibility/ebooks.py",
    "author": "plausibility",
    "author_email": "chris@gibsonsec.org",
    "license": "MIT",
    "packages": [
        "ebooks"
    ],
    "install_requires": [
        "twitter"
    ],
    "zip_safe": False,
    "keywords": "twitter bot ebooks markov",
    "classifiers": [
        "Development Status :: 3 - Alpha",
        #"Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python"
    ]
}

if __name__ == "__main__":
    setup(**kw)
