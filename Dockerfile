# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.11-alpine AS builder

RUN apk add git

WORKDIR /app

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app
CMD ["waitress-serve", "--threads=6", "--port=8000", "--call", "app:create_app"]

FROM builder as dev-envs

RUN <<EOF
apk update
apk add git
EOF

RUN <<EOF
addgroup -S docker
adduser -S --shell /bin/bash --ingroup docker vscode
EOF
# install Docker tools (cli, buildx, compose)
COPY --from=gloursdocker/docker / /
