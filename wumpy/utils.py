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

from typing import Any, BinaryIO

from typing_extensions import Final, final

__all__ = ('MISSING', 'File')


@final
class MissingType(object):
    """Representing an optional default when no value has been passed.

    This is mainly used as a sentinel value for defaults to work nicely
    with typehints, so that `Optional[X]` doesn't have to be used.
    """

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return '<MISSING>'


MISSING: Final[Any] = object()


class File:
    """Representing a file to be uploaded to Discord."""

    source: BinaryIO
    filename: str

    __slots__ = ('source', 'filename')

    def __init__(self, source: BinaryIO, filename: str, *, spoiler: bool = False) -> None:
        self.source = source

        # We use the removeprefix methods as they do nothing if the string does not
        # start with the string passed.
        if not spoiler:
            self.filename = filename.removeprefix('SPOILER_')
        else:
            # The user may have already added a SPOILER_ prefix
            self.filename = 'SPOILER_' + filename.removeprefix('SPOILER_')

    def read(self, n: int) -> bytes:
        return self.source.read(n)

    def close(self) -> None:
        return self.source.close()
