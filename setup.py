try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='geotweet',
    version='0.1.6',
    description='Fetch geographic tweets from Twitter Streaming API',
    author='Jeffrey Alan Meyers',
    author_email='jeffrey.alan.meyers@gmail.com',
    url='https://github.com/meyersj/geotweet',
    packages=['geotweet', 'geotweet.twitter', 'geotweet.mongo', 'geotweet.geo'],
    scripts=['bin/geotweet', 'bin/geoloader'],
    include_package_data=True,
    install_requires=[
        'argparse',
        'boto3',
        'python-twitter',
        'requests',
        'mrjob',
        'pymongo',
        'Geohash',
        'Shapely',
        'Rtree',
        'lxml'
    ]
)
