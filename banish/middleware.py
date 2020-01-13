# Copyright 2008-2013 Yousef Ourabi

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from django.conf import settings
from django.http import HttpResponseForbidden
from django.core.exceptions import MiddlewareNotUsed
from django.core.cache import cache

from banish.models import Banishment


class BanishMiddleware(object):
    def __init__(self, get_response):
        """
        Middleware init is called once per server on startup - do the heavy
        lifting here.
        """
        # If disabled or not enabled raise MiddleWareNotUsed so django
        # processes next middleware.
        self.ENABLED = getattr(settings, 'BANISH_ENABLED', False)
        if not self.ENABLED:
            raise MiddlewareNotUsed(
                "django-banish is not enabled via settings.py"
            )

        self.get_response = get_response

        self.ABUSE_THRESHOLD = getattr(settings, 'BANISH_ABUSE_THRESHOLD', 75)
        self.USE_HTTP_X_FORWARDED_FOR = getattr(
            settings, 'BANISH_USE_HTTP_X_FORWARDED_FOR', True
        )
        self.PROTECTED_PATH = getattr(
            settings, 'BANISH_PROTECTED_PATH', ['/admin/login/'],
        )
        self.BANISH_MESSAGE = getattr(
            settings, 'BANISH_MESSAGE', 'You are banned.'
        )

        # Empty user agent is banned by default
        self.BANNED_AGENTS = [None]

        # Prefix All keys in cache to avoid key collisions
        self.BANISH_PREFIX = 'DJANGO_BANISH:'
        self.ABUSE_PREFIX = 'DJANGO_BANISH_ABUSE:'
        self.WHITELIST_PREFIX = 'DJANGO_BANISH_WHITELIST:'

        # Populate various 'banish' buckets
        for access in Banishment.objects.all():
            if access.kind == 'ip-address':
                cache_key = self.BANISH_PREFIX + access.condition
                cache.set(cache_key, 1, 3600 * access.count)
            elif access.kind == 'user-agent':
                self.BANNED_AGENTS.append(access.condition)
            elif access.kind == 'ip-address-whitelist':
                cache_key = self.WHITELIST_PREFIX + access.condition
                cache.set(cache_key, 1, 3600 * 12)

    def __call__(self, request):
        ip = self._get_ip(request)
        path = request.META["PATH_INFO"]
        user_agent = request.META['HTTP_USER_AGENT']

        # Check whitelist first, if not allowed, then check ban conditions
        if (path not in self.PROTECTED_PATH) or self.is_whitelisted(ip):
            return self.get_response(request)
        elif self.is_banned(ip) or self.watch_abuse(ip) or \
            (user_agent in self.BANNED_AGENTS):
            return HttpResponseForbidden(
                self.BANISH_MESSAGE, content_type="text/html"
            )
        return self.get_response(request)

    def _get_ip(self, request):
        if self.USE_HTTP_X_FORWARDED_FOR:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                return x_forwarded_for.partition(',')[0].strip()
        return request.META['REMOTE_ADDR']

    def is_banned(self, ip):
        # If a key BANISH MC key exists we know the user is banned.
        return cache.get(self.BANISH_PREFIX + ip)

    def is_whitelisted(self, ip):
        # If a whitelist key exists, return True to allow the request through
        return cache.get(self.WHITELIST_PREFIX + ip)

    def watch_abuse(self, ip):
        over_abuse_limit = False

        cache_key = self.ABUSE_PREFIX + ip
        abuse_count = cache.get(cache_key)
        if abuse_count is None:
            # time scale of statistics is 60 seconds
            cache.set(cache_key, 1, 60)
        else:
            if abuse_count > self.ABUSE_THRESHOLD:
                over_abuse_limit = True
                ban, created = Banishment.objects.get_or_create(
                    kind="ip-address", condition=ip
                )
                if not created:
                    ban.count += 1
                    ban.save(update_fields=['count'])
                # No need to update cache here, `post_save` signal will trigger it.
                logging.info("[BANISH] banned IP: %s", ip)
                return over_abuse_limit
            try:
                cache.incr(cache_key)
            except ValueError: # may cause by expiration of cache within 60 seconds
                pass

        return over_abuse_limit

