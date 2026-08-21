VERSION 0.8
FROM astral/uv:python3.10-bookworm-slim
WORKDIR /contrib

linting-files:
  COPY .prettierignore .
  SAVE ARTIFACT .

parser-files:
  COPY electricitymap/contrib/parsers ./parsers
  COPY electricitymap/contrib/capacity_parsers ./capacity_parsers
  SAVE ARTIFACT *

src-files:
  COPY electricitymap/contrib/config ./electricitymap/contrib/config
  COPY electricitymap/contrib/lib ./electricitymap/contrib/lib
  COPY electricitymap/contrib/py.typed ./electricitymap/contrib/py.typed
  COPY libs/types ./libs/types
  COPY ./config+src-files/* ./config
  COPY scripts ./scripts
  COPY __init__.py ./__init__.py
  COPY pyproject.toml .
  SAVE ARTIFACT .

src-files-with-parsers:
  COPY +src-files/* .
  COPY +parser-files/parsers ./electricitymap/contrib/parsers
  COPY +parser-files/capacity_parsers ./electricitymap/contrib/capacity_parsers
  SAVE ARTIFACT .

api-files:
  COPY geo/world.geojson ./geo/world.geojson
  COPY config/zone_names.json ./config/zone_names.json
  SAVE ARTIFACT .

uv-lock:
  COPY uv.lock .
  SAVE ARTIFACT .

prepare:
  FROM +src-files-with-parsers
  RUN apt-get update && apt-get install -y python3-opencv tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng libgl1
  COPY uv.lock .
  RUN uv sync --frozen --group dev --extra parsers --compile-bytecode

build:
  FROM +prepare

test:
  FROM +build
  COPY tests ./tests
  COPY geo/world.geojson ./geo/world.geojson
  RUN uv run check

# includes both test target and build target here to make sure both can work
# we can split into two later if required
test-all:
  BUILD +build
  BUILD +test
  BUILD ./config+test
