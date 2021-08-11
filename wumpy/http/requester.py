import asyncio
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Union
from urllib.parse import quote as urlquote

import aiohttp

from ..errors import (
    Forbidden, HTTPException, NotFound, RequestException, ServerException
)
from .locks import Lock
from .ratelimiter import DictRateLimiter, RateLimiter, Route

try:
    import orjson

    def orjson_dump(obj: Any) -> str:
        # orjson returns bytes but aiohttp expects a string
        return orjson.dumps(obj).decode('utf-8')

    dump = orjson_dump
except ImportError:
    import json

    dump = json.dumps

__all__ = ('build_user_agent', 'Requester')


def build_user_agent() -> str:
    """Build a User-Agent to use in making requests."""
    from wumpy import __version__  # Avoid circular imports

    agent = f'DiscordBot (https://github.com/Bluenix2/wumpy, version: {__version__})'
    agent += f' Python/{sys.version_info[0]}.{sys.version_info[1]}'

    return agent


class Requester:
    """A class to make requests against Discord's API, respecting ratelimits.

    This class itself does not actually contain any routes, that way it can be
    re-used and subclassed for several purposes.
    """

    headers: Dict[str, str]

    ratelimiter: RateLimiter

    __session: aiohttp.ClientSession

    __slots__ = ('headers', 'ratelimiter', '__session')

    def __init__(self, ratelimiter=DictRateLimiter, *, headers: Dict[str, str] = {}) -> None:
        # Headers global to the requester
        self.headers: Dict[str, str] = {
            'User-Agent': build_user_agent(),
            'X-RateLimit-Precision': 'millisecond',
            **headers,
        }

        self.ratelimiter = ratelimiter()
        self.__session = aiohttp.ClientSession(headers=self.headers, json_serialize=dump)

    async def _handle_ratelimit(self, data: Dict[str, Any]) -> None:
        """Handle an unexpected 429 response."""
        retry_after: float = data['retry_after']

        is_global: bool = data.get('global', False)
        if is_global:
            self.ratelimiter.lock()  # Globally lock all requests

        await asyncio.sleep(retry_after)

        if is_global:
            self.ratelimiter.unlock()  # Release now that the global ratelimit has passed

    async def _request(
        self,
        route: Route,
        headers: Dict[str, str],
        ratelimit: Lock,
        attempt: int,
        **params: Any
    ) -> Union[str, Dict[str, Any], None]:
        """Attempt to actually make the request.

        None is returned if the request got a bad response which was handled
        and the function should be called again to retry.
        """
        async with self.__session.request(route.method, route.url, headers=headers, **params) as res:
            text = await res.text(encoding='utf-8')
            if res.headers.get('Content-Type') == 'application/json':
                # Parse the response
                data = json.loads(text)
            else:
                data = text

            # Update rate limit information if we have received it
            self.ratelimiter.update(route, res.headers.get('X-RateLimit-Bucket'))

            if res.headers.get('X-RateLimit-Remaining') == '0':
                ratelimit.defer()

                reset = datetime.fromtimestamp(float(res.headers['X-Ratelimit-Reset']), timezone.utc)
                # Release later when the ratelimit reset
                asyncio.get_running_loop().call_later(
                    (reset - datetime.now(timezone.utc)).total_seconds(),
                    ratelimit.release
                )

            # Successful request
            if 300 > res.status >= 200:
                return data

            # In all of these error cases the response will be a dict
            assert isinstance(data, dict)  # For the static type checking

            # We're being ratelimited by Discord
            if res.status == 429:
                # Returning None will cause the function to try again
                return await self._handle_ratelimit(data)

            elif res.status in {500, 502, 504}:
                # Unconditionally sleep and retry
                await asyncio.sleep(1 + attempt * 2)
                return None

            elif res.status == 403:
                raise Forbidden(res, data)
            elif res.status == 404:
                raise NotFound(res, data)
            elif res.status == 503:
                raise ServerException(res, data)
            else:
                raise RequestException(res, data)

    async def request(self, route: Route, **kwargs) -> Union[str, Dict[str, Any]]:
        """Make a request to the Discord API, respecting rate limits."""

        # Create the headers for the request
        headers: dict[str, str] = {}

        if 'reason' in kwargs:
            headers['X-Audit-Log-Reason'] = urlquote(kwargs.pop('reason'), safe='/ ')

        for attempt in range(5):
            async with self.ratelimiter.get(route) as rl:
                try:
                    res = await self._request(route, headers, rl, attempt, **kwargs)
                except OSError as error:
                    # Connection reset by peer
                    if attempt < 4 and error.errno in (54, 10054):
                        # Exponentially backoff and try again
                        await asyncio.sleep(1 + attempt * 2)
                        continue

                    # The last attempt or some other error
                    raise error

                if res is None:
                    continue  # Something went wrong, let's retry

                return res

        raise HTTPException(f'All attempts at {route} failed')