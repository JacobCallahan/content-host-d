FROM jacobcallahan/sles:11
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

ADD startup.sh /tmp/
ADD install-tools.sh /tmp/
RUN chmod +x /tmp/startup.sh

EXPOSE 22

CMD /tmp/startup.sh
