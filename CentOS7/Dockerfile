FROM centos:7
LABEL org.opencontainers.image.authors="https://github.com/JacobCallahan"

RUN yum install -y subscription-manager

ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh

EXPOSE 22

CMD /tmp/startup.sh
