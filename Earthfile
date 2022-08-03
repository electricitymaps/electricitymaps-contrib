VERSION 0.6

prepare:
  FROM python:3.8
  WORKDIR /contrib
  COPY electricitymap ./electricitymap
  COPY parsers ./parsers
  COPY validators ./validators
  COPY config ./config
  COPY pyproject.toml .
  RUN pip install poetry==1.1.12
  RUN poetry config virtualenvs.create false
  RUN poetry install

test:
  FROM +prepare
  RUN poetry run check

artifact:
  FROM +prepare
  SAVE ARTIFACT .
