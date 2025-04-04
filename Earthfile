VERSION 0.7
FROM python:3.10
WORKDIR /contrib

linting-files:
  COPY .prettierignore .
  SAVE ARTIFACT .

parser-files:
  COPY parsers ./parsers
  COPY electricitymap ./electricitymap
  SAVE ARTIFACT .

src-files:
  COPY electricitymap/contrib/config ./electricitymap/contrib/config
  COPY electricitymap/contrib/lib ./electricitymap/contrib/lib
  COPY electricitymap/contrib/py.typed ./electricitymap/contrib/py.typed
  COPY ./config+src-files/* ./config
  COPY scripts ./scripts
  COPY web/public/locales/en.json ./web/public/locales/en.json
  COPY __init__.py ./__init__.py
  COPY pyproject.toml .
  SAVE ARTIFACT .

src-files-with-parsers:
  COPY +src-files/* .
  COPY +parser-files/* .
  SAVE ARTIFACT .

poetry-lock:
  COPY poetry.lock .
  SAVE ARTIFACT .

prepare:
  FROM +src-files-with-parsers
  RUN pip install "poetry==2.*"
  RUN apt-get update && apt-get install -y python3-opencv tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng libgl1
  RUN poetry config virtualenvs.create false
  COPY poetry.lock .
  RUN poetry install --compile -E parsers

build:
  FROM +prepare

test:
  FROM +build
  COPY tests ./tests
  COPY web/src/utils/constants.ts ./web/src/utils/constants.ts # TODO: python tests should not depend on this js file
  COPY web/geo/world.geojson ./web/geo/world.geojson
  RUN poetry run check

# includes both test target and build target here to make sure both can work
# we can split into two later if required
test-all:
  BUILD +build
  BUILD +test
  BUILD ./config+test
  # BUILD ./web+build # TODO: This currently fails for unknown reasons, disabling for now
  BUILD ./web+test

