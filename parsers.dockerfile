# Container image that executes the parser tests
# Build with "$ docker build -f parsers.dockerfile -t parsers . "
# Run with  "$ docker run parsers US-CAL-CISO production"
# If needed, pass any token env var using "docker run -e TOKEN=<token>"

FROM astral/uv:python3.10-bookworm-slim
WORKDIR /workspace
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng
COPY . .
RUN uv sync --frozen --group dev --extra parsers --compile-bytecode
ENTRYPOINT ["uv", "run", "test_parser"]
