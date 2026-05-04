from importlib import resources
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from electricitymap.contrib.parsers.JP_KN import (
    extract_capacity,
    extract_operation_percentage,
    get_image_text,
)

_FIXTURES = resources.files("electricitymap.contrib.parsers.tests.mocks.JP-KN")

_OP_IMAGES = [
    "unten2.gif",
    "unten5.gif",
    "unten6.gif",
    "unten7.gif",
    "unten8.gif",
    "unten9.gif",
    "unten10.gif",
]


def _image_bytes(name: str) -> bytes:
    return _FIXTURES.joinpath(name).read_bytes()


def _urlopen_side_effect(request):
    """Route urlopen calls to local fixture bytes by matching the filename."""
    url = request.full_url if hasattr(request, "full_url") else request
    for name in (*_OP_IMAGES, "t_unten.gif"):
        if name in url:
            m = MagicMock()
            m.read.return_value = _image_bytes(name)
            return m
    raise AssertionError(f"Unexpected URL in test: {url}")


@patch("electricitymap.contrib.parsers.JP_KN.urlopen")
def test_snapshot_get_image_text_on_real_kepco_gifs(mock_urlopen, snapshot):
    """End-to-end snapshot over the Pillow + tesseract pipeline for each real
    kepco operation image: urlopen -> Image.open(BytesIO) -> size -> crop ->
    image_to_string. Lang is 'eng' so this only needs the default tessdata.
    """
    mock_urlopen.side_effect = _urlopen_side_effect

    ocr_by_image = {
        name: get_image_text(
            f"https://www.kepco.co.jp/interchange/nuclear_power/monitor/live_images/{name}",
            lang="eng",
            width=65,
        )
        for name in _OP_IMAGES
    }

    assert snapshot == ocr_by_image


@patch("electricitymap.contrib.parsers.JP_KN.urlopen")
def test_snapshot_reactor_rows_capacity_and_operation_percentage(
    mock_urlopen, snapshot
):
    """Walk every reactor row in the real live_unten HTML and snapshot the
    derived (capacity_kw, operation_percentage) pair. This exercises bs4 row
    traversal + real OCR for each row that has a .gif operation image.
    """
    mock_urlopen.side_effect = _urlopen_side_effect

    html = _FIXTURES.joinpath("live_unten.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    for tr in soup.findAll("tr"):
        capacity = extract_capacity(tr)
        if capacity is None:
            continue
        rows.append(
            {
                "capacity_kw": capacity,
                "operation_percentage": extract_operation_percentage(tr),
            }
        )

    assert snapshot == rows
