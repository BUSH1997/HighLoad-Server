FROM python:3.8

RUN mkdir var/www
RUN mkdir var/www/html

COPY httpd.conf /etc
COPY httptest/ /var/www/html/httptest

WORKDIR /app

COPY main.py /app

EXPOSE 80

CMD python3 main.py 0.0.0.0 80