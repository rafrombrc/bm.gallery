from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='bm.gallery',
      version=version,
      description="Burning Man media galleries",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='burning man media gallery',
      author='Rob Miller',
      author_email='rob@kalistra.com',
      url='http://www.burningman.com/',
      license='',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['bm'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'psycopg2',
          'python-ldap',
          'django-auth-ldap',
          'django-tagging',
          'django-imagekit',
          'django-notify',
          'hachoir-metadata',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
