from parsers.lib.exceptions import ParserException


def test_instance():
    exception = ParserException("ESIOS", "Parser exception")
    assert isinstance(exception, ParserException)
    assert str(exception) == "ESIOS Parser: Parser exception"


def test_instance_with_zone_key():
    exception = ParserException("ESIOS", "Parser exception", "ES")
    assert isinstance(exception, ParserException)
    assert str(exception) == "ESIOS Parser (ES): Parser exception"
