FROM registry.access.redhat.com/rhel7.2
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

RUN rm -f /etc/rhsm-host /etc/pki/entitlement-host
ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh
ADD hostname-3.13-3.el7.x86_64.rpm /tmp/
RUN yum -y localinstall /tmp/hostname-3.13-3.el7.x86_64.rpm

EXPOSE 22

CMD /tmp/startup.sh
