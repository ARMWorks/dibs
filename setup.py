from setuptools import setup

setup(
    name='dibs',
    version='0.0.1',
    description='Debian Image Build System',
    author='Jeff Kent',
    author_email='jeff@jkent.net',
    url='https://github.com/ARMWorks/dibs',
    packages=['dibs'],
    license='MPLv2',
    include_data_files=True,
    install_requires=[
        'pyyaml',
    ]
)
