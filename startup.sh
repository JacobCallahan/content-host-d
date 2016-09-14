#!/bin/sh

# Add the Satellite's cert
if [ -n "$SATHOST" ]; then
    echo "Adding satellite certificate http://$SATHOST/pub/katello-ca-consumer-latest.noarch.rpm"
    rpm -Uvh http://$SATHOST/pub/katello-ca-consumer-latest.noarch.rpm
fi

# Configure our registration auth, if provided
if [ -n "$AUTH" ]; then
    IFS="/" read -r UNAME PWORD <<< "$AUTH"
    AUTH='--username="$UNAME" --password="$PWORD"'
else
    AUTH="--username="admin" --password="changeme""
fi

# Set the organization to default, if not provided
if [ -z "$ORG" ]; then
    ORG="Default_Organization"
fi

# Register to the sat if an activation key specified
if [ -n "$AK" ]; then
    echo "Activation key $AK found. Registering..."
    subscription-manager register --org="$ORG" --activationkey="$AK"
# If an environment is otherwise specified, use it
elif [ -n "$ENV" ]; then
    echo "Environment $ENV found. Registering..."
    subscription-manager register --org="$ORG" --environment="$ENV" $AUTH
# If no specifics are provided, register to the library
else
    echo "No registration details specified. Registering to $ORG and Library..."
    subscription-manager register --org="$ORG" --environment="Library" $AUTH
fi

# Install katello agent
subscription-manager refresh
yum -y install katello-agent openssh-server openssh-clients passwd

# Then prepare this host for remote execution
echo "Preparing host for remote execution"
mkdir ~/.ssh
touch ~/.ssh/authorized_keys
chmod -R 777 ~/.ssh
curl https://$SATHOST:9090/ssh/pubkey >> ~/.ssh/authorized_keys

# if the KILL arg was not passed, then keep the container running
if [ -z "$KILL" ]; then
    echo "Starting goferd in foreground."
    goferd -f
fi
