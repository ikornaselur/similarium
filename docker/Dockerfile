# Builder image
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements.txt

RUN pip install \
  --no-deps \
  --no-cache \
  -r requirements.txt

# Runner image
FROM python:3.10-slim AS runner

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
 
WORKDIR /app

COPY docker/run.sh run.sh
COPY alembic.ini .
COPY alembic ./alembic
COPY src .

RUN useradd -u 1001 -r similarium

RUN chown -R similarium /app
USER similarium

CMD ["/app/run.sh"]
