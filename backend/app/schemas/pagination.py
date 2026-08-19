from typing import Generic, List, TypeVar

from pydantic import BaseModel, computed_field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic paginated list envelope. Reused by any GET-list endpoint
    (campaigns, companies, and later contacts/accounts) so the shape of
    'page N of results' stays consistent across the API."""

    items: List[T]
    total: int
    page: int
    page_size: int

    @computed_field  # included in the serialized response, not just a Python-side helper
    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
