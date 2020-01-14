# django-banish

### About this fork

This projects is simple and fast among all similar apps for Django. I like it but find it not compatible to Django 2.2 and Python 3.x.

So this fork has made some updates to improve its compatibity to latest version of Django, and to optimize its performance as far as possible, as well as a few features added.

It now can run on Python 3.x and Django 2.x.

---

django-banish is a Django middleware app to banish user agents by IP address or User Agent Header. It also supports basic abuse prevention by automatically banning users if they exceed a certain number of requests per minute, which is likely some form of attack or attempted denial of service.

Django-banish stores all 'banishments' in memory to avoid database lookups on every request. It requires memcached, especially for the IP abuse monitoring feature.

django-banish was previously called django-ipban and hosted on google-code. That code should be ignored - In 2010 it was dusted off and given a new life at github.

## Installation

Requirements:

* Python 3.x
* Django 2.x
* Memcache / Redis (with django_redis)

## Get django-banish 

Get the source:

Browse the source on GitHub: <https://github.com/davidchern/django-banish>

Clone with Git:

```shell
$ git clone git://github.com/davidchern/django-banish
```

## Setup

Install django-banish. Make sure it is on your PYTHONPATH or in your django project directory.

In your django project settings.py you must set the following options:

    1) Add 'banish.middleware.BanishMiddleware' to MIDDLEWARE_CLASSES

    2) Add 'banish' to INSTALLED_APPS

    3) Add BANISH_ENABLED = True to enable Django-Banish (handy if you lock yourself out, you can just set this to False)
    
    4) Add BANISH_PROTECTED_PATH = ['/admin/login/', '/user/login/'] for the paths to be protected.
    
    5) Add BANISH_USE_HTTP_X_FORWARDED_FOR = True to enable using IP address behind proxies.

    6) Optionally set BANISH_ABUSE_THRESHOLD (default is 75) to the threshold of requests per minute.

    7) Optionally set BANISH_MESSAGE (default is "You are banned.") to change default message for banned user.

## Issues

Find a bug? Want a feature? Submit an [issue here](https://github.com/davidchern/django-banish/issues). Patches welcome!

## License

django-banish is released under the Apache Software License, Version 2.0


## Authors

 * [Yousef Ourabi][1]
 
 * [David Chern][2]

 [1]: http://github.com/yourabi
 [2]: http://github.com/davidchern
