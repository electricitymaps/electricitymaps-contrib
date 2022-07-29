# Container image that executes the parser tests 
# Build with "$ docker build -f parsers.dockerfile -t parsers . "
# Run with  "$ docker run parsers US-CAL-CISO production"
# If needed, pass any token env var using "docker run -e TOKEN=<token>"

FROM python:3-slim
WORKDIR /workspace
RUN apt-get update -qqy --no-install-recommends  && apt-get install -qqy --no-install-recommends python3-opencv tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng libgl1 && apt-get -qqy clean
RUN pip install poetry
COPY . .
RUN poetry install -E parsers
ENTRYPOINT ["poetry",  "run", "test_parser"]
