# before changing these variables, make sure the tag $PYTHON_VERSION-alpine$ALPINE_VERSION exists first
# list of valid tags hese: https://hub.docker.com/_/python
ARG PYTHON_VERSION=3.6
ARG ALPINE_VERSION=3.12

# stage-0: copy pyproject.toml/poetry.lock and install the production set of dependencies
FROM python:$PYTHON_VERSION-alpine$ALPINE_VERSION as stage-0
WORKDIR /usr/src/app/
RUN apk add --no-cache openssl-dev libffi-dev build-base git
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock  ./
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    PIP_DEFAULT_TIMEOUT=600
RUN apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing rocksdb-dev
RUN poetry install -n -E rocksdb --no-root --no-dev

# stage-1: install all dev dependencies and build protos, reuse .venv from stage-0
FROM python:$PYTHON_VERSION-alpine$ALPINE_VERSION as stage-1
WORKDIR /usr/src/app/
RUN apk add --no-cache openssl-dev libffi-dev build-base git
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock  ./
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    PIP_DEFAULT_TIMEOUT=600
COPY --from=stage-0 /usr/src/app/.venv /usr/src/app/.venv/
RUN poetry install -n -E rocksdb --no-root
COPY Makefile ./
COPY hathor/protos ./hathor/protos/
RUN poetry run make protos

# finally: use production .venv (from stage-0) and compiled protos (from stage-1)
# lean and mean: this image should be about ~110MB, would be about ~470MB if using the whole stage-1
FROM python:$PYTHON_VERSION-alpine$ALPINE_VERSION
WORKDIR /usr/src/app/
RUN apk add --no-cache openssl libffi libstdc++ graphviz
RUN apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing rocksdb
COPY --from=stage-0 /usr/src/app/.venv/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=stage-1 /usr/src/app/hathor/protos/*.py /usr/src/app/hathor/protos/
COPY hathor ./hathor
EXPOSE 40403 8080
ENTRYPOINT ["python", "-m", "hathor"]
