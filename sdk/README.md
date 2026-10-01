# TechScope Source SDK

Install locally with:

```bash
pip install -e sdk
```

Implement `techscope_sources.SourceAdapter` with `name`, `get_article_links`,
and `parse_article`. Adapters should ship fixture tests and return normalized
article dictionaries.