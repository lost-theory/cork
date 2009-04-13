from distutils.core import setup

setup(name='Cork', version='0.1',
    description='YAML-based, WSGI-aware information repository',
    author='Alex Morega',
    author_email='cork@grep.ro',
    url='http://github.com/alex-morega/cork',
    license='MIT',
    packages=['cork'],
    install_requires=['pyyaml', 'WebOb'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    keywords='yaml wsgi web repository',
)
