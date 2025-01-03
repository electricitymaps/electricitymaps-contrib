from parsers.lib import web


def test_get_response():
    assert web.get_response("ES", "https://www.google.es")


def test_get_response_text():
    assert web.get_response_text("ES", "https://www.google.es")


def test_get_response_soup():
    assert web.get_response_soup("ES", "https://www.google.es")
