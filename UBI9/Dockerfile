FROM registry.access.redhat.com/ubi9/ubi
MAINTAINER https://github.com/JacobCallahan
LABEL broker_compatible="True"

ENV HOME /root
ENV SMDEV_CONTAINER_OFF True
WORKDIR /root

RUN echo "{\"virt.host_type\": \"Not Applicable\", \"virt.is_guest\": \"False\"}" > /etc/rhsm/facts/custom.facts
ADD startup.sh /tmp/
RUN chmod +x /tmp/startup.sh
ADD hostname-3.23-6.el9.x86_64.rpm /tmp/
RUN yum -y localinstall /tmp/hostname-3.23-6.el9.x86_64.rpm

EXPOSE 22

CMD /tmp/startup.sh
