FROM traefik:latest

RUN apk add --no-cache gettext


COPY ./entrypoint.sh /entrypoint.sh
COPY ./traefik.yml /traefik.yml
COPY ./dynamic /dynamic
COPY ./acme /acme
COPY ./config /config
COPY ./logs /logs

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--configFile=/traefik.yml"]