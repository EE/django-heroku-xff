"""Which forwarded entry becomes `REMOTE_ADDR`, and when it is left alone."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from heroku_xff.middleware import XForwardedForMiddleware


SOCKET_PEER = '10.0.0.1'
MIDDLEWARE_PATH = 'heroku_xff.middleware.XForwardedForMiddleware'
OTHER_MIDDLEWARE = 'django.middleware.common.CommonMiddleware'


def resolved_remote_addr(**extra):
    """`REMOTE_ADDR` as the view reads it."""
    seen = []
    request = RequestFactory().get('/', REMOTE_ADDR=SOCKET_PEER, **extra)
    XForwardedForMiddleware(lambda request: seen.append(request.META['REMOTE_ADDR']))(request)
    return seen[0]


def test_takes_the_entry_the_router_appended():
    """The caller wrote the first entry and the router the second, so the second wins."""
    assert resolved_remote_addr(
        HTTP_X_FORWARDED_FOR='203.0.113.9, 93.184.216.34',
    ) == '93.184.216.34'


def test_takes_the_appended_entry_whatever_range_it_falls_in():
    # `ipaddress` counts the RFC 5737 documentation ranges as private alongside RFC 1918,
    # so a gate on `is_private` reads right past the router's entry into the caller's.
    assert resolved_remote_addr(
        HTTP_X_FORWARDED_FOR='203.0.113.9, 198.51.100.7',
    ) == '198.51.100.7'


def test_takes_an_ipv6_client_address():
    assert resolved_remote_addr(HTTP_X_FORWARDED_FOR='2001:db8::1') == '2001:db8::1'


@pytest.mark.parametrize('appended', [
    'not-an-ip',
    # The router appends no port, so this is left unparsed rather than trimmed.
    '[2001:db8::1]:443',
])
def test_an_unparseable_appended_entry_falls_back_past_the_callers(appended):
    assert resolved_remote_addr(
        HTTP_X_FORWARDED_FOR=f'203.0.113.9, {appended}',
    ) == SOCKET_PEER


def test_a_request_that_missed_the_router_keeps_the_socket_peer():
    assert resolved_remote_addr() == SOCKET_PEER


def test_loads_first_in_middleware(settings):
    settings.MIDDLEWARE = [MIDDLEWARE_PATH, OTHER_MIDDLEWARE]
    XForwardedForMiddleware(lambda request: None)


def test_refuses_to_load_behind_another_middleware(settings):
    settings.MIDDLEWARE = [OTHER_MIDDLEWARE, MIDDLEWARE_PATH]
    with pytest.raises(ImproperlyConfigured, match='must be first in MIDDLEWARE'):
        XForwardedForMiddleware(lambda request: None)
