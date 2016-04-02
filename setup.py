try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='geotweet',
    version='0.1.1',
    description='Fetch geographic tweets from Twitter Streaming API',
    author='Jeffrey Alan Meyers',
    author_email='jeffrey.alan.meyers@gmail.com',
    url='https://github.com/meyersj/geotweet',
    packages=['geotweet'],
    scripts=['bin/geotweet'],
    install_requires=[
        'argparse',
        'boto3',
        'python-twitter',
        'pyinotify',
    ]
)
