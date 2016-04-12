#!/bin/bash

SCRIPTDIR=`dirname $(readlink -f $0)`
JOBDIR=`readlink -f ${SCRIPTDIR}/../geotweet/mapreduce`
DATADIR=`readlink -f ${SCRIPTDIR}/../geotweet/data/mapreduce`



# === MR Job Parameters ===

interpreter=../env/bin/python
conf="--conf-path ~/scratch/mrjob.conf"
#script="${JOBDIR}/state_county_wordcount.py"
#script="${JOBDIR}/metro_mongo_wordcount.py"
script="${JOBDIR}/metro_nearby_osm_tag_count.py"
# ==========================


# === Persistant Cluster ===
# ../env/bin/mrjob create-cluster ${conf} --max-hours-idle 1
# ==========================


# Local Job
logfile1="twitter-stream.log.2016-03-26_13-13"
logfile2="/home/data/twitter-stream.log.2016-03-29_12-36"
logfile3="twitter-stream.log.2016-03-27_01-53"
src="${DATADIR}/${logfile1} ${logfile2}"
osmfiles="${DATADIR}/oregon-latest.poi ${DATADIR}/colorado-latest.poi"

# for state_county and metro_mongo
#LOCAL_JOB_CMD="${interpreter} ${script} ${src}"

# for metro_nearby_osm
data="/home/jeff/data/geotweet-test/*"
LOCAL_JOB_CMD="${interpreter} ${script} --strict-protocols ${data}"
#LOCAL_JOB_CMD="${interpreter} ${script} --strict-protocols ${src} ${osmfiles}"


# EMR Job
now=`date +"%Y%m%d%H%M"`
src="s3://jeffrey.alan.meyers.geotweet-test/"
dst="--output-dir s3://jeffrey.alan.meyers.bucket/geotweet/output/metro-osm-${now}"
#EMR_JOB_CMD="${interpreter} ${script} -r emr ${src} ${dst} --no-output"
EMR_JOB_CMD="${interpreter} ${script} ${conf} -r emr ${src} ${dst} --no-output"

# Run
#${LOCAL_JOB_CMD}
${EMR_JOB_CMD}
