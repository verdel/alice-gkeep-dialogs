FROM verdel/centos-base:latest
LABEL maintainer="Vadim Aleksandrov <valeksandrov@me.com>"

COPY docker/rootfs /

RUN pip3 install git+http://github.com/verdel/alice-gkeep-dialogs \
    # Clean up
    && dnf clean all \
    && rm -rf \
    /usr/share/man \
    /tmp/* \
    /var/cache/dnf
