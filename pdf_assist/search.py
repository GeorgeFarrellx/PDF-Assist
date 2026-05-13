from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    page_index: int
    rect: tuple[float, float, float, float]
    text: str | None = None


@dataclass
class SearchState:
    query: str = ""
    results: list[SearchResult] = field(default_factory=list)
    current_index: int = -1

    def clear(self) -> None:
        self.query = ""
        self.results = []
        self.current_index = -1

    @property
    def has_results(self) -> bool:
        return bool(self.results)

    @property
    def current_result(self) -> SearchResult | None:
        if not self.has_results or self.current_index < 0:
            return None
        return self.results[self.current_index]

    def results_for_page(self, page_index: int) -> list[tuple[int, SearchResult]]:
        return [(i, result) for i, result in enumerate(self.results) if result.page_index == page_index]

    def next(self) -> SearchResult | None:
        if not self.has_results:
            return None
        self.current_index = (self.current_index + 1) % len(self.results)
        return self.current_result

    def previous(self) -> SearchResult | None:
        if not self.has_results:
            return None
        self.current_index = (self.current_index - 1) % len(self.results)
        return self.current_result
