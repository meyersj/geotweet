#!/bin/bash
set -e


function dependencies {
    apt-get update
    apt-get install -y python-dev libgeos-dev libspatialindex-dev \
            build-essential protobuf-compiler libprotobuf-dev
    curl https://bootstrap.pypa.io/get-pip.py | python
    pip install virtualenv
}


function python_env {
    cd /vagrant
    virtualenv env
    ./env/bin/pip install -r /vagrant/requirements.txt
}


function mongo {
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
    deb="deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse"
    echo "${deb}" | tee /etc/apt/sources.list.d/mongodb-org-3.2.list
    apt-get update
    apt-get install -y mongodb-org
    # listen on all interfaces
    sed -i 's/127\.0\.0\.1/0\.0\.0\.0/g' /etc/mongod.conf 
    service mongod restart
}


dependencies
python_env
mongo
