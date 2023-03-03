VERSION 0.7
FROM python:3.8
WORKDIR /contrib

src-files:
  COPY electricitymap ./electricitymap
  COPY parsers ./parsers
  COPY validators ./validators
  COPY ./config+src-files/* ./config
  COPY scripts ./scripts
  COPY web/public/locales/en.json ./web/public/locales/en.json
  COPY __init__.py ./__init__.py
  COPY pyproject.toml .
  SAVE ARTIFACT .

prepare:
  FROM +src-files
  RUN pip install poetry==1.1.12
  RUN apt-get update && apt-get install -y python3-opencv tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng libgl1
  RUN poetry config virtualenvs.create false
  RUN poetry install -E parsers -E validators

build:
  FROM +prepare

test:
  FROM +build
  COPY tests ./tests
  COPY web/src/utils/constants.ts ./web/src/utils/constants.ts # TODO: python tests should not depend on this js file
  COPY web/geo/world.geojson ./web/geo/world.geojson
  RUN poetry run check
