FROM registry.access.redhat.com/rhel6.8
MAINTAINER https://github.com/jyejare

ENV HOME /root
WORKDIR /root

RUN rm -f /etc/rhsm-host /etc/pki/entitlement-host

ADD startup.sh /tmp
RUN chmod +x /tmp/startup.sh

EXPOSE 22

CMD /tmp/startup.sh
