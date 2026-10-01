from typing import Protocol


class SourceAdapter(Protocol):
    name: str

    def get_article_links(self) -> list[str]:
        ...

    def parse_article(self, url: str) -> dict | None:
        ...
