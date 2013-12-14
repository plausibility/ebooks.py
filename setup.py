from setuptools import setup


def long_desc():
    with open('README.rst', 'rb') as f:
        return f.read()

kw = {
    "name": "ebooks",
    "version": "0.1.2",
    "description": '',
    "long_description": long_desc(),
    "url": "https://github.com/plausibility/ebooks.py",
    "author": "plausibility",
    "author_email": "chris@gibsonsec.org",
    "license": "MIT",
    "packages": [
        "ebooks"
    ],
    "install_requires": [
        "gevent",
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
