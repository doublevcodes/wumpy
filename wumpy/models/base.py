"""
MIT License

Copyright (c) 2021 Bluenix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from datetime import datetime, timezone
from typing import Any, Type, TypeVar

__all__ = ('Object', 'Snowflake')


DISCORD_EPOCH = 1420070400000


class Object:
    """The root for all Wumpy objects, a Discord object with an ID.

    A Wumpy object is a simple wrapper over an integer, the Discord snowflake
    which is guaranteed by Discord to be unique. It tries to support as many
    operations as possible.
    """

    id: int

    __slots__ = ('id',)

    def __init__(self, id: int) -> None:
        self.id = id

    def __repr__(self) -> str:
        # To be clear that it isn't a normal object
        return f'<wumpy.Object id={self.id}>'

    def __str__(self) -> str:
        return str(self.id)

    def __bytes__(self) -> bytes:
        return bytes(self.id)

    def __hash__(self) -> int:
        return self.id >> 22

    def __int__(self) -> int:
        # Even though __index__ covers __int__, we need to define
        # it so that we successfully implement SupportsInt
        return self.id

    def __index__(self) -> int:
        # __index__ convers __complex__, __int__ and __float__
        # by defining this one we don't need to define the rest
        return self.id

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, int):
            value = other
        elif isinstance(other, self.__class__):
            value = other.id
        else:
            return NotImplemented

        return self.id == value

    def __ne__(self, other: Any) -> bool:
        # There's a performance hit to not defining __ne__, even though
        # Python will automatically call __eq__ and invert it

        if isinstance(other, int):
            value = other
        elif isinstance(other, self.__class__):
            value = other.id
        else:
            return NotImplemented

        return self.id != value

    @property
    def created_at(self) -> datetime:
        timestamp = (self.id >> 22) + DISCORD_EPOCH
        return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


# We need to type the return type of the from_datetime() classmethod
SELF = TypeVar('SELF', bound='Snowflake')


class Snowflake(Object):
    """Standalone Discord snowflake.

    This is seperate from Object as not all methods on this class should be
    inherited to subclasses, such as the `from_datetime()` classmethod. Any
    standalone ID field will be an instance of this class.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f'<Snowflake id={self.id}>'

    @property
    def worker_id(self) -> int:
        """Return the ID of the worker that created the snowflake."""
        return (self.id & 0x3E0000) >> 17

    @property
    def process_id(self) -> int:
        """Return the ID of the process that created the snowflake."""
        return (self.id & 0x1F000) >> 12

    @property
    def process_increment(self) -> int:
        """Return the increment of the process that created the snowflake."""
        return self.id & 0xFFF

    @classmethod
    def from_datetime(cls: Type[SELF], dt: datetime) -> SELF:
        """Craft a snowflake created at the specified time."""
        return cls(int(dt.timestamp() * 1000 - DISCORD_EPOCH) << 22)
