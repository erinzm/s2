FROM python:3.7-alpine
ADD . /src
WORKDIR /src

RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    apk --no-cache --update-cache add gcc gfortran python python-dev py-pip build-base \
        wget freetype-dev libjpeg-turbo-dev libpng-dev openblas-dev postgresql-dev && \
    pip install pipenv gunicorn && \
    pipenv install --deploy --system

CMD ["scripts/wait-for", "postgres:5432", "--", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app.wsgi:app"]