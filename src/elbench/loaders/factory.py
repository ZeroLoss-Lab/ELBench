from __future__ import annotations

from elbench.loaders.base import BaseLoader
from elbench.loaders.jsonl_loader import JsonlLoader
from elbench.loaders.xlsx_loader import XlsxLoader


class LoaderFactory:
    _LOADERS: dict[str, type[BaseLoader]] = {
        "jsonl": JsonlLoader,
        "xlsx": XlsxLoader,
    }

    @classmethod
    def create(cls, loader_name: str) -> BaseLoader:
        if loader_name not in cls._LOADERS:
            raise ValueError(f"Unsupported loader: {loader_name}")
        return cls._LOADERS[loader_name]()

