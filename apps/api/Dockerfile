FROM python:3.12-slim

# Base-image publication can lag available Debian security fixes. Apply them
# before installing the app; the container audit remains the release gate.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml .
# The providers remain runtime-disabled without keys, but the local image includes
# their SDKs so selecting a configured provider does not require rebuilding by hand.
RUN pip install --no-cache-dir ".[ai]"
COPY app app
COPY alembic alembic
COPY alembic.ini .
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
