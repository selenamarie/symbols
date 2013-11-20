from distutils.core import setup

setup(
    name='SymbolsDB',
    version='0.1.0',
    author='Selena Deckelmann',
    author_email='selenamarie@gmail.com',
    packages=['symbolsdb','symbols.tests'],
    scripts=['bin/count.py'],
    url='http://pypi.python.org/pypi/symbols-db/',
    license='LICENSE.txt',
    description='Database for Breakpad symbols',
    long_description=open('README.txt').read(),
    install_requires=[
        "SQLAlchemy >= 0.9.0",
        "argparse == 1.2.1",
        "psycopg2 == 2.4.6",
        "wsgiref == 0.1.2",
        "hurry.filesize == 0.9",
    ],
)
