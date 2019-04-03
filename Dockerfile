FROM        python:3.7-alpine
MAINTAINER  blessmht@gmail.com

ENV         PYTHONUNBUFFERED 1

COPY        ./requirements.txt /requirements.txt
RUN         apk add --update --no-cache postgresql-client jpeg-dev
RUN         apk add --update --no-cache --virtual .tmp-build-deps \
                gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
RUN         pip install -r /requirements.txt
RUN         apk del .tmp-build-deps

RUN         mkdir /app
WORKDIR     /app
COPY        ./app /app

# -p 옵션을 사용하면 /vol/web/media 디렉토리를 한번의 커맨드로 생성 가능함
RUN         mkdir -p /vol/web/media
RUN         mkdir -p /vol/web/static
RUN         adduser -D user
RUN         chown -R user:user /vol/
RUN         chmod -R 755 /vol/web
USER        user