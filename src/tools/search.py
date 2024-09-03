import logging
import time
from ddgs import DDGS
from config import MAX_SEARCH_RESULTS

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 2.0
_QUERY_DELAY = 1.0


def search(queries: list[str]) -> tuple[str, list[str]]:
    all_results: list[str] = []
    all_sources: list[str] = []
    errors: list[str] = []

    with DDGS() as ddgs:
        for i, query in enumerate(queries):
            if i > 0:
                time.sleep(_QUERY_DELAY)

            hits = _search_with_retry(ddgs, query, errors)

            for hit in hits:
                title = hit.get("title", "Untitled")
                url = hit.get("href", "")
                snippet = hit.get("body", "").strip()

                if snippet:
                    all_results.append(f"[{title}]\n{snippet}")

                if url and url not in all_sources:
                    all_sources.append(url)

    if not all_results:
        raise RuntimeError(
            "All search queries failed for this section.\nErrors:\n" +
            "\n".join(errors)
        )

    if errors:
        logger.warning("Some queries failed (partial results returned): %s", errors)

    return "\n\n---\n\n".join(all_results), all_sources


def _search_with_retry(ddgs: DDGS, query: str, errors: list[str]) -> list[dict]:
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            hits = list(ddgs.text(query, max_results=MAX_SEARCH_RESULTS))
            if hits:
                return hits

            if attempt < _RETRY_ATTEMPTS:
                logger.warning("Empty results for '%s' (attempt %d), retrying...", query, attempt)
                time.sleep(_RETRY_DELAY)
        except Exception as e:
            if attempt < _RETRY_ATTEMPTS:
                logger.warning("Error on '%s' (attempt %d): %s, retrying...", query, attempt, e)
                time.sleep(_RETRY_DELAY)
            else:
                errors.append(f"Query '{query}' failed after {_RETRY_ATTEMPTS} attempts: {e}")

    errors.append(f"Query '{query}' returned 0 results after {_RETRY_ATTEMPTS} attempts")
    return []
