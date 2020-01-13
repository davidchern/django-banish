# Copyright 2008-2010 Yousef Ourabi

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import datetime

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

BANISH_PREFIX = 'DJANGO_BANISH:'
ABUSE_PREFIX = 'DJANGO_BANISH_ABUSE:'
WHITELIST_PREFIX = 'DJANGO_BANISH_WHITELIST:'


class Banishment(models.Model):

    # Flush out time constrained banned in future revisions
    # ban_start = models.DateField(help_text="Banish Start Date.")
    # ban_stop = models.DateField(help_text="Banish Stop Date.")
    # ban_is_permanent = models.BooleanField(help_text="Is Ban Permanent?")

    BAN_TYPES = (
        ('ip-address', 'Banned IP Address'),
        ('user-agent', 'Banned User Agent'),
        ('ip-address-whitelist', 'Whitelist IP Address'),
    )

    kind = models.CharField(
        max_length=20,
        choices=BAN_TYPES,
        default=0,
        db_index=True,
        help_text="Type of User Ban/Whitelist to store"
    )

    condition = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Enter an IP to ban/whitelist, or a User Agent to ban'
    )

    count = models.PositiveSmallIntegerField(default=1, help_text='Banned count')

    def __str__(self):
        return "%s %s" % (self.get_kind_display(), self.condition)

    def is_current(self):
        """
        Determine if this banishment is current by comparing
        dates
        """
        if self.permanent or self.stop > datetime.date.today(): 
            return True
        return False

    class Meta:
        #permissions = (("can_manage_access", "Can Manage Access"),)
        verbose_name = "User Access"
        verbose_name_plural = "User Access"
        db_table = 'banishments'


def _generate_cache_key(instance):
    if instance.kind == 'ip-address-whitelist':
        cache_key = WHITELIST_PREFIX + instance.condition
        count = 12
    if instance.kind == 'ip-address':
        cache_key = BANISH_PREFIX + instance.condition
        count = instance.count
    abuse_key = ABUSE_PREFIX + instance.condition
    return (cache_key, abuse_key, count)


def _update_cache(sender, instance, **kwargs):
    # add a whitelist entry and remove any abuse counter for an IP
    cache_key, abuse_key, count = _generate_cache_key(instance)
    cache.set(cache_key, 1, 3600 * count)
    cache.delete(abuse_key)


def _delete_cache(sender, instance, **kwargs):
    cache_key, abuse_key, _ = _generate_cache_key(instance)
    cache.delete(cache_key)


post_save.connect(_update_cache, sender=Banishment)
post_delete.connect(_delete_cache, sender=Banishment)
