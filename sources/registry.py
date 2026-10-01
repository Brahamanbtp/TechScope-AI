from sources.base import SourceAdapter


_ADAPTERS: dict[str, SourceAdapter] = {}


def register_adapter(adapter: SourceAdapter) -> None:
    _ADAPTERS[adapter.name] = adapter


def get_adapter(name: str) -> SourceAdapter | None:
    return _ADAPTERS.get(name)


def list_adapters() -> list[str]:
    return sorted(_ADAPTERS)
