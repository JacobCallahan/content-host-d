FROM registry.access.redhat.com/rhel6.8
MAINTAINER https://github.com/jyejare

ENV HOME /root
WORKDIR /root

RUN sed -i -e 's/os.path.exists(HOST_CONFIG_DIR)/False/g' /usr/lib64/python2.6/site-packages/rhsm/config.py

ADD startup.sh /tmp
RUN chmod +x /tmp/startup.sh

EXPOSE 22

CMD /tmp/startup.sh
