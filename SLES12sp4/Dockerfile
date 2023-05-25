FROM jacobcallahan/sles:12sp4
MAINTAINER https://github.com/JacobCallahan

ENV HOME /root
WORKDIR /root

RUN echo "{\"virt.host_type\": \"Not Applicable\", \"virt.is_guest\": \"False\"}" > /etc/rhsm/facts/custom.facts
ADD startup.sh /tmp/
ADD install-tools.sh /tmp/
RUN chmod +x /tmp/startup.sh

EXPOSE 22

CMD /tmp/startup.sh
