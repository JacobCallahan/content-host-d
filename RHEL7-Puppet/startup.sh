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
    echo "Activation key $AK provided. Registering..."
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

# Install puppet 
subscription-manager attach --auto
yum clean all && yum repolist enabled
yum -y install puppet
systemctl enable puppet
sed -i "2i\    server = $SATHOST" /etc/puppet/puppet.conf
echo "    ca_server = $SATHOST" >> /etc/puppet/puppet.conf
echo "    server = $SATHOST" >> /etc/puppet/puppet.conf
echo "    environment = production" >> /etc/puppet/puppet.conf
echo "    pluginsync = true" >> /etc/puppet/puppet.conf
echo "    report = true" >> /etc/puppet/puppet.conf
echo "    ignoreschedules = true" >> /etc/puppet/puppet.conf
echo "    daemon = false" >> /etc/puppet/puppet.conf

echo "10.19.34.24 yttrium.idmqe.lab.eng.bos.redhat.com yttrium" >> /etc/hosts

echo "Initial puppet registration"
puppet agent -t --server $SATHOST
echo "sleeping for 1 minute. make sure $(hostname) has a valid certificate"
sleep 60
echo "Second puppet registration"
puppet agent -t --server $SATHOST

# if the KILL arg was not passed, then keep the container running
if [ -z "$KILL" ]; then
    echo "Starting fact flood."
    while true
    do
        echo "Updating facts..."
        puppet facts upload
        echo "sleeping"
        sleep 1
    done
fi

