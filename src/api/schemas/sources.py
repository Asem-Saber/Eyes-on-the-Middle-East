"""Source contracts — v2's replacement for v1's `/authors`.

v1 ranked publishers from the `Publisher` field. v2's processing step drops
`Publisher`, `Topics` and `Sources` from accepted output, so there is no author
data in the warehouse. `dim_source` carries the publishing domain instead,
which is what remains attributable.
"""

from __future__ import annotations

from pydantic import BaseModel


class Source(BaseModel):
    source_key: int
    source_name: str | None = None
    domain: str | None = None
    article_count: int = 0
