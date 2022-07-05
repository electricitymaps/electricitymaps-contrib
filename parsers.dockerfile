# Container image that executes the parser tests 
# Build with "$ docker build -f parsers.dockerfile -t parsers . "
# Run with  "$ docker run parsers US-CAL-CISO production"
# If needed, pass any token env var using "docker run -e TOKEN=<token>"

FROM python:3.10

WORKDIR /workspace

RUN apt-get update && apt-get install -y python3-opencv

RUN pip install poetry

COPY . .

RUN poetry install -E parsers

ENTRYPOINT ["poetry",  "run", "test_parser"]
