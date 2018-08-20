FROM python:3.6-alpine
MAINTAINER Denys Chekirda aka Rocklviv

ARG VERSION

ENV VERSION ${VERSION}
ENV USER aws_prices
ENV WORKSPACE /opt/${USER}

RUN mkdir -p ${WORKSPACE} &&\
    addgroup -g 1001 ${USER} &&\
    adduser -D -u 1001 -G ${USER} ${USER}

COPY ./ ${WORKSPACE}

WORKDIR ${WORKSPACE}
RUN pip install -U -r requirements.txt

USER ${USER}
VOLUME ${WORKSPACE}
EXPOSE 8080

CMD ["python", "main.py"]