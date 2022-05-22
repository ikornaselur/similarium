FROM --platform=$BUILDPLATFORM python:3.10-slim AS builder

ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential

COPY requirements.txt requirements.txt

RUN pip install \
  --user \
  --no-deps \
  --no-cache \
  -r requirements.txt

FROM python:3.10-slim AS runner

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
 
WORKDIR /app

COPY docker/run.sh /app/run.sh
COPY alembic.ini .
COPY alembic ./alembic
COPY src .

RUN useradd -u 1001 -r similarium

RUN chown -R similarium /app
USER similarium

CMD ["/app/run.sh"]
