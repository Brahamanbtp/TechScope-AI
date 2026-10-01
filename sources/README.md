# Source Adapter SDK

Implement the `SourceAdapter` protocol from `sources/base.py`:

```python
class MyAdapter:
    name = "example"

    def get_article_links(self) -> list[str]:
        return []

    def parse_article(self, url: str) -> dict | None:
        return None
```

Register adapters with `sources.registry.register_adapter(adapter)`. Adapters
must return normalized dictionaries containing `url`, `title`, `author`,
`published`, and `content`, and should include fixture-backed parser tests.