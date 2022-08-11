FROM alpine:latest
WORKDIR /databases
COPY . .
WORKDIR /databases
RUN apk --update-cache add sqlite \
    && rm -rf /var/cache/apk/* \
    && touch ./data/migrations-docker.sqlite \
    && chmod a+rw ./data/migrations-docker.sqlite \
    && chmod a+x ./create_database.sh \
    && ./create_database.sh \
