#!/bin/sh

# Add the Capsule LB's cert
if [ -n "$LBHOST" ]; then
    echo "Adding Capsule Load Balancer certificate http://$LBHOST/pub/katello-ca-consumer-latest.noarch.rpm"
    rpm -Uvh http://$LBHOST/pub/katello-ca-consumer-latest.noarch.rpm
fi


# Set the organization to default, if not provided
if [ -z "$ORG" ]; then
    ORG="Default_Organization"
fi

# Register to the sat using an activation key specified
if [ -n "$AK" ]; then
    echo "Activation key $AK specified. Registering..."
    subscription-manager register --org="$ORG" --activationkey="$AK" --serverurl=https://$LBHOST:8443/rhsm --baseurl=https://$LBHOST/pulp/repos
else
    echo "FAILED! No registration details specified - $AK"
fi

# Install katello agent
yum -y install katello-agent

# if the KILL arg was not passed, then keep the container running
if [ -z "$KILL" ]; then
    echo "Tailing rhsm log."
    tail -f /var/log/rhsm/rhsm.log
fi
