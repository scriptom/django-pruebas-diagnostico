import os
from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-pruebas-diagnostico',
    version='1.2.1',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',  # example license
    description='Aplicación sencilla de Django que brinda soporte para pruebas Diagnóstico sencillas.',
    author='Tomás El Fakih',
    author_email='tomaselfakih@gmail.com',
    download_url='https://github.com/scriptom/django-pruebas-diagnostico/archive/1.2.1.tar.gz',
    install_requires=[
        'django_nested_admin'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.1 ',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
