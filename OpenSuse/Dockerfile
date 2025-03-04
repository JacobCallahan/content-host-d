FROM jacobcallahan/opensuse-host
LABEL org.opencontainers.image.authors="https://github.com/JacobCallahan"

ADD startup.sh /tmp/
ADD install-tools.sh /tmp/
RUN chmod +x /tmp/startup.sh

EXPOSE 22

CMD /tmp/startup.sh
