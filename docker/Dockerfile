FROM python:3.10-slim

WORKDIR /app

COPY docker/run.sh /app/run.sh

# Used to apply migrations on startup
COPY alembic.ini .
COPY alembic ./alembic
RUN pip install alembic==1.7.7

COPY requirements.txt requirements.txt
RUN pip install --no-deps --no-cache -r requirements.txt

COPY src .

RUN useradd -u 1001 -r similarium

RUN chown -R similarium /app
USER similarium

CMD ["/app/run.sh"]
