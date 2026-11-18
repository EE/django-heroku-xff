# django-heroku-xff

On Heroku, `REMOTE_ADDR` is the router that forwarded the request, not the client.
The client is in `X-Forwarded-For`,
but most of that header is whatever the client chose to send:
the router *appends* the address it accepted the connection from to the header the request arrived with.
So `X-Forwarded-For: 192.0.2.1` sent from `198.51.100.7` reaches the app as

```
X-Forwarded-For: 192.0.2.1, 198.51.100.7
```

and only the last entry can be trusted.
Reading the first one, or accepting a request because any entry matches,
lets anyone claim any address by sending the header themselves.

This middleware puts the last entry into `REMOTE_ADDR`,
so an IP allow-list, a throttle or a log reading `REMOTE_ADDR` gets the client the router saw.

## Install

It is not on PyPI; depend on a commit of this repository:

```
django-heroku-xff @ git+https://github.com/EE/django-heroku-xff.git@<sha>
```

Put it first in `MIDDLEWARE`, in the settings module Heroku runs and nowhere else:

```python
MIDDLEWARE = ['heroku_xff.middleware.XForwardedForMiddleware'] + MIDDLEWARE
```

It refuses to load anywhere but first,
since a middleware ahead of it would read the router's address.

Leave it out of local and test settings:
with no router in front, the last entry is as much the client's choice as the rest,
and a client sending the header could pick its own `REMOTE_ADDR`.

## What it assumes

That Heroku's router is the only proxy in front of the app.
A CDN or another proxy in front of the router makes the last entry that proxy's address, not the client's,
and the app usually stays reachable on its `herokuapp.com` domain around it.
Neither is something this middleware can detect.

## Development

```bash
poetry install
poetry run pytest
```
