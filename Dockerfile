# Smoke-test image: installs codeatlas and runs it on the bundled sample.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .

COPY sample/ sample/

CMD ["codeatlas", "scan", "sample"]
