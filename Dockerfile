FROM python:3.10-slim

WORKDIR /app

EXPOSE 8080

COPY requirements.txt requirements.txt
RUN pip install --no-deps --no-cache -r requirements.txt

COPY src .

RUN useradd -u 1001 -r similarium

RUN chown -R similarium /app
USER similarium

CMD ["python", "-m", "similarium.app"]
