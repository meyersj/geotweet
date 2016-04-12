from setuptools import setup


setup(
    name='geotweet',
    version='0.2.5',
    description='Fetch geographic tweets from Twitter Streaming API',
    author='Jeffrey Alan Meyers',
    author_email='jeffrey.alan.meyers@gmail.com',
    url='https://github.com/meyersj/geotweet',
    packages=[
        'geotweet',
        'geotweet.twitter',
        'geotweet.geomongo',
        'geotweet.mapreduce',
        'geotweet.mapreduce.utils'
    ],
    scripts=['bin/geotweet'],
    include_package_data=True,
    install_requires=[
        'setuptools>=7.0',
        'argparse',
        'boto3',
        'mrjob>=0.5.0',
        'requests>=2.0',
        'python-twitter',
        'pymongo',
        'Geohash',
        'Shapely',
        'Rtree',
        'pyproj',
        'imposm.parser',
        'ujson'
    ]
)
