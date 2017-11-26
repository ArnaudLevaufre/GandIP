from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gandip',
    version='2.0.0',

    description='Keep your gandi DNS records up to date with your current IP',
    long_description=long_description,
    url='https://github.com/ArnaudLevaufre/GandIP',
    author='Arnaud Levaufre',
    author_email='arnaud@levaufre.name',
    license='MIT',

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Internet :: Name Service (DNS)',

        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='dns gandi ip selfhosting hosting',

    py_modules=["gandip"],

    install_requires=[],


    entry_points={
        'console_scripts': [
            'gandip=gandip:main',
        ],
    },
)
