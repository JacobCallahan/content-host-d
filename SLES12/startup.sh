#!/bin/bash

# Adding the local entry on /etc/hosts
if [ -n "$LOCAL" ]; then
    echo "Adding entry '$LOCAL $SATHOST' on /etc/hosts"
    echo "$LOCAL $SATHOST" >>/etc/hosts
fi

# Add the Satellite's cert
if [ -n "$SATHOST" ]; then
    echo "Adding satellite certificate http://$SATHOST/pub/katello-ca-consumer-latest.noarch.rpm"
    curl --insecure --output katello-ca-consumer-latest.noarch.rpm http://$SATHOST/pub/katello-ca-consumer-latest.noarch.rpm
    rpm -Uvh katello-ca-consumer-latest.noarch.rpm
fi

# Configure our registration auth, if provided
if [ -n "$AUTH" ]; then
    IFS="/" read -r UNAME PWORD <<< "$AUTH"
    AUTH="--username=$UNAME --password=$PWORD"
else
    AUTH="--username=admin --password=changeme"
fi

# Set the organization to default, if not provided
if [ -z "$ORG" ]; then
    ORG="Default_Organization"
fi

# Register to the sat if an activation key specified
if [ -n "$AK" ]; then
    echo "Activation key $AK specified. Registering..."
    subscription-manager register --org="$ORG" --activationkey="$AK"
# If an environment is otherwise specified, use it
elif [ -n "$ENV" ]; then
    echo "Environment $ENV found. Registering..."
    subscription-manager register --org="$ORG" --environment="$ENV" "$AUTH"
# If no specifics are provided, register to the library
else
    echo "No registration details specified. Registering to $ORG and Library..."
    subscription-manager register --org="$ORG" --environment="Library" "$AUTH"
fi

# Install katello agent
echo "Trying to install katello-host-tools"
zypper --no-gpg-checks --auto-agree-with-licenses in -y katello-host-tools

# if the KILL arg was not passed, then keep the container running
if [ -z "$KILL" ]; then
    echo "Starting goferd in foreground."
    goferd -f
    tail -f /var/log/rhsm/rhsm.log
fi
