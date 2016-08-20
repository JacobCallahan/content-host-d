FROM centos
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh

# runtime
EXPOSE 22

CMD /tmp/startup.sh