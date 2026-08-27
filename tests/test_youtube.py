"""YouTube search helper. No live network."""

from lucy.engines.youtube import is_results_url


def test_results_url() -> None:
    assert is_results_url("https://www.youtube.com/results?search_query=lofi+hip+hop+radio")
    assert is_results_url("https://m.youtube.com/results?search_query=soup")
    assert not is_results_url("https://www.youtube.com/watch?v=jfKfPfyJRdk")
    assert not is_results_url("https://en.wikipedia.org/wiki/Special:Random")
