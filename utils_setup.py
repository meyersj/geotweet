try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='geotweet-utils',
    version='0.1',
    description='Utils to process tweets from Streaming API',
    author='Jeffrey Alan Meyers',
    author_email='jeffrey.alan.meyers@gmail.com',
    url='https://github.com/meyersj/geotweet',
    packages=['geotweet_utils'],
    install_requires=[
        'Shapely',
        'Rtree',
        'Geohash',
        'pymongo'
    ]
)
