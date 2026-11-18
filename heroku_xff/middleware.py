from contextlib import suppress
from ipaddress import ip_address

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class XForwardedForMiddleware:
    """
    Sets `REMOTE_ADDR` to the last `X-Forwarded-For` entry,
    the one Heroku's router appended and the only one a caller cannot choose.

    An entry that will not parse leaves `REMOTE_ADDR` as the socket peer,
    since whatever reads it is better served by a coarse address than by a 500.
    The router appends no port, so none is stripped:
    stripping one naively mangles an IPv6 address.

    It refuses to load anywhere but first in `MIDDLEWARE`,
    so nothing reads `REMOTE_ADDR` before it is set.
    """
    def __init__(self, get_response):
        path = f'{type(self).__module__}.{type(self).__qualname__}'
        if path in settings.MIDDLEWARE and settings.MIDDLEWARE[0] != path:
            raise ImproperlyConfigured(f'{path} must be first in MIDDLEWARE.')
        self.get_response = get_response

    def __call__(self, request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        appended = forwarded_for.rsplit(',', 1)[-1].strip()

        with suppress(ValueError):
            ip_address(appended)
            request.META['REMOTE_ADDR'] = appended

        return self.get_response(request)
