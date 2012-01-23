from django.conf import settings
from django.contrib.auth.models import User
from django.utils import unittest

from mock import Mock
from mysql_pool.base import DatabaseWrapper, db_pool

from sqlalchemy import event

# Alright I'm tired and don't have the time to mock this out fully. I just
# wanted to write some integration tests to prove that this does what we
# want it to and nothing more. This means some hacks in your settings and
# mysql to make it behave the way we want.
#
# This is the wait timeout you've set on mysql, so it will kill any
# connections that are older than this
mysql_timeout = 5
#
# These are the names of the two databases connections you've set in
# settings.py so we can be sure that the two databases are using different
# pools and don't stomp on each other.
#
# These two pools can point to the same database, but should have a different
# signature. For example:
# DATABASES = {
#    'default': {
#        'NAME': 'zamboni',
#        'ENGINE': 'mysql_pool',
#        'USER': 'root',
#        'PASSWORD': '',
#        'HOST': '',
#        'OPTIONS':  {'init_command': 'SET storage_engine=InnoDB'},
#        'TEST_CHARSET': 'utf8',
#        'TEST_COLLATION': 'utf8_general_ci',
#    },
#    'test_mysql_pool': {
#        'NAME': 'zamboni',
#        'ENGINE': 'mysql_pool',
#        'USER': 'root',
#        'PASSWORD': '',
#        'HOST': '',
#        'OPTIONS':  {},
#        'TEST_CHARSET': 'utf8',
#        'TEST_COLLATION': 'utf8_general_ci',
#    },
#}
# If I was, smarter this would all be done in test setup.
#
databases = ['default', 'test_mysql_pool']
#
# Got these setup? Great, let's go.

class TestPool(unittest.TestCase):

    def setUp(self):
        # Make sure we start with nothing in the pool.
        db_pool.close()
        self.wrapper = DatabaseWrapper(Mock())

    def test_serialize(self):
        _keys = []
        for db in databases:
            _settings = self.wrapper._serialize(settings.DATABASES[db])
            _keys.append(_settings['sa_pool_key'])
        assert len(set(_keys)) == len(databases)

    def test_can_query(self):
        len(User.objects.all())
        assert len(db_pool.pools) == 1

    def test_multiple_queries(self):
        for x in range(3):
            len(User.objects.all())
        assert len(db_pool.pools) == 1

    def test_multiple_pool(self):
        for db in databases:
            User.objects.using(db).all()
        assert len(db_pool.pools) == 2


