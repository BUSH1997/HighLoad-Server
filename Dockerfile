FROM python:3.8

COPY . /app
COPY . /var/www

WORKDIR /app

EXPOSE 80

CMD python3 main.py