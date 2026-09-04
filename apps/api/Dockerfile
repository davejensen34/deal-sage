FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
# The providers remain runtime-disabled without keys, but the local image includes
# their SDKs so selecting a configured provider does not require rebuilding by hand.
RUN pip install --no-cache-dir ".[ai]"
COPY app app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
