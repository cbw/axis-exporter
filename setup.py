import io
from setuptools import setup, find_packages

VERSION = "1.0.0"
PACKAGE_NAME = "axis-exporter"
SOURCE_DIR_NAME = "src"


def readme():
    with io.open('README.md', 'r', encoding='utf-8') as f:
        return f.read()


setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description="Prometheus exporter for Axis Communications IP camera metrics",
    author="Chris Wilson",
    author_email="chris@chrisbwilson.com",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/cbw/axis-exporter",
    package_dir={'': SOURCE_DIR_NAME},
    packages=find_packages(SOURCE_DIR_NAME, exclude=('*.tests',)),
    include_package_data=True,
    zip_safe=False,
    package_data={},
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    install_requires=[
        "prometheus-client",
        "requests",
    ],
    entry_points={
        'console_scripts': [
            'axis-exporter = axis_exporter.main:main',
        ],
    }
)
