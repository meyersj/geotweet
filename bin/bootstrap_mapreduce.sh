#!/bin/bash


# extra commands required when starting from fresh Centos Box
# When running on EMR these commands are not required
# -------------------------------------------------------------
#yum install -y epel-release
#curl "https://bootstrap.pypa.io/get-pip.py" -o "/tmp/get-pip.py"
#python /tmp/get-pip.py
# -------------------------------------------------------------

# system packages
yum update -y
yum install -y gcc-c++ geos geos-devel python-devel

# install libspatialindex for Rtree
cd /opt
wget http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.gz
tar xzvf spatialindex-src-1.8.5.tar.gz
cd spatialindex-src-1.8.5
./configure && make && make install
echo /usr/local/lib >> /etc/ld.so.conf
ldconfig

# install protobuf
cd /opt
wget http://cbs.centos.org/kojifiles/packages/protobuf/2.5.0/10.el7.centos/x86_64/protobuf-2.5.0-10.el7.centos.x86_64.rpm
wget http://cbs.centos.org/kojifiles/packages/protobuf/2.5.0/10.el7.centos/x86_64/protobuf-devel-2.5.0-10.el7.centos.x86_64.rpm
wget http://cbs.centos.org/kojifiles/packages/protobuf/2.5.0/10.el7.centos/x86_64/protobuf-compiler-2.5.0-10.el7.centos.x86_64.rpm
yum -y install protobuf-2.5.0-10.el7.centos.x86_64.rpm \
    protobuf-compiler-2.5.0-10.el7.centos.x86_64.rpm \
    protobuf-devel-2.5.0-10.el7.centos.x86_64.rpm 
