"""Aerie object (de)serialization utilities

Postgres interval parsing modified from Django implementation:
https://github.com/django/django/blob/0dd29209091280ccf34e07c9468746c396b7778e/django/utils/dateparse.py#L52-L64

Django is licensed under the BSD 3-Clause License:
    Copyright (c) Django Software Foundation and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

        1. Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.

        2. Redistributions in binary form must reproduce the above copyright
        notice, this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.

        3. Neither the name of Django nor the names of its contributors may be used
        to endorse or promote products derived from this software without
        specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import re
from datetime import timedelta


POSTGRES_INTERVAL_RE = re.compile(
    r"^"
    r"(?:(?P<days>-?\d+) (days? ?))?"
    r"(?:(?P<sign>[-+])?"
    r"(?P<hours>\d+):"
    r"(?P<minutes>\d\d):"
    r"(?P<seconds>\d\d)"
    r"(?:\.(?P<microseconds>\d{1,6}))?"
    r")?$"
)


def postgres_interval_to_timedelta(interval: str) -> timedelta:
    """Parse a Postgres inteval to a `timedelta` object

    Modified from Django interval parsing cited above.

    Args:
        interval (str): Postgres interval string

    Raises:
        ValueError: Unable to match patterns in the interval

    Returns:
        timedelta
    """
    match = POSTGRES_INTERVAL_RE.match(interval)
    if match:
        kw = match.groupdict()
        sign = -1 if kw.pop("sign", "+") == "-" else 1
        if kw.get("microseconds"):
            kw["microseconds"] = kw["microseconds"].ljust(6, "0")
        kw = {k: float(v.replace(",", ".")) for k, v in kw.items() if v is not None}
        days = timedelta(kw.pop("days", 0.0) or 0.0)
        return days + sign * timedelta(**kw)
    else:
        raise ValueError(f"Unable to parse interval string: {interval}")


def postgres_interval_to_microseconds(interval: str) -> int:
    """Convert a postgres interval string to an integer number of microseconds

    Both `timedelta` and Postgres intervals have a precision of 1us, so this conversion shouldn't introduce any rounding errors
    """
    return int(postgres_interval_to_timedelta(interval).total_seconds() * (10**6))


def timedelta_to_postgres_interval(td: timedelta) -> str:
    """Constructs a PostgreSQL interval from a `timedelta`
    """
    seconds = td.days * 86400 + td.seconds
    microseconds = td.microseconds
    return f"{int(seconds)} seconds {int(microseconds)} microseconds"
