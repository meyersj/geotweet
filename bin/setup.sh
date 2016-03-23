#!/bin/bash
set -e


function dependencies {
    apt-get update
    apt-get install -y \
        python-pip python-dev \
        libssl-dev \
        libxml2-dev libxslt1-dev \
        libffi-dev \
        default-jre
}

function python_env {
    pip install -r /vagrant/requirements.txt    
}

function osmosis {
    cd /opt
    mkdir -p /opt/osmosis
    cd /opt/osmosis
    wget http://bretth.dev.openstreetmap.org/osmosis-build/osmosis-latest.tgz
    tar xvfz osmosis-latest.tgz
    rm osmosis-latest.tgz
    chmod a+x bin/osmosis
    ln -s ${PWD}/bin/osmosis /usr/bin/osmosis
    cd -
}

function mongo {
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
    deb="deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse"
    echo "${deb}" | tee /etc/apt/sources.list.d/mongodb-org-3.0.list
    apt-get update
    apt-get install -y mongodb-org
    # listen on all interfaces
    sed -i 's/127\.0\.0\.1/0\.0\.0\.0/g' /etc/mongod.conf 
    service mongod restart
}

dependencies
python_env
osmosis
mongo
