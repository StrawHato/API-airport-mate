FROM ubuntu:latest
LABEL authors="garganta"

ENTRYPOINT ["top", "-b"]