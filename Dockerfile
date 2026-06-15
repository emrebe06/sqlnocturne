FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SQLNOCTURNE_DATABASE=sqlite:////data/app.db

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY sqlnocturne ./sqlnocturne

RUN pip install --no-cache-dir -e .

RUN mkdir -p /data
VOLUME ["/data"]

CMD ["python", "-m", "sqlnocturne.cli.main", "check"]
