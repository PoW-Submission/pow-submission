FROM python:3.8.6-alpine

RUN mkdir -p /code

WORKDIR /code

EXPOSE 3000

RUN apk update && \
    apk add --no-cache \
        gcc \
        musl-dev \
        libc-dev \
        linux-headers \
        postgresql-dev \
        nodejs \
        yarn

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY prod-requirements.txt .
RUN pip install -r prod-requirements.txt

RUN pip install gunicorn

COPY pow_submission ./pow_submission

WORKDIR /code/pow_submission

RUN yarn install
RUN yarn build
RUN rm -rf node_modules
RUN apk del yarn nodejs

ARG POW_DJANGO_SECRET_KEY
ENV POW_DJANGO_SECRET_KEY=$POW_DJANGO_SECRET_KEY
ARG POW_DATABASE_USER
ENV POW_DATABASE_USER=$POW_DATABASE_USER
ARG POW_DATABASE_PASSWORD
ENV POW_DATABASE_PASSWORD=$POW_DATABASE_PASSWORD
ARG POW_DATABASE_HOST
ENV POW_DATABASE_HOST=$POW_DATABASE_HOST

ENV DJANGO_SETTINGS_MODULE=pow_submission.prod_settings
ENTRYPOINT ["gunicorn"]
CMD ["pow_submission.wsgi", "--bind=127.0.0.1:3000", "--workers=2"]
