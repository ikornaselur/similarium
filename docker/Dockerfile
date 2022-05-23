# Builder image
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements.txt

RUN pip install poetry==1.1.13

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
COPY src .

RUN poetry config virtualenvs.in-project true \
  && poetry install --no-dev -E sqlite -E postgres

# Runner image
FROM python:3.10-slim AS runner

COPY --from=builder /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
 
WORKDIR /app

COPY docker/run.sh run.sh
COPY alembic.ini .
COPY alembic ./alembic
COPY src .

RUN useradd -u 1001 -r similarium

RUN chown -R similarium /app
USER similarium

CMD ["/app/run.sh"]
