Introduction
============

This is bm.gallery, a media gallery application intended for use on
the burningman.com website.  It is built on top of Django, a web
application framework, using the Python programming language.
Installation is handled via zc.buildout.


Getting Started
===============

To get started w/ a development instance of the bm.gallery project on
a POSIX-like system (i.e. anything except Windows) you should perform
the following steps:

 - Copy the src/bm.gallery/bm/gallery/local_settings.py.example file
   to src/bm.gallery/bm/gallery/local_settings.py, then edit this file
   to specify site-specific settings.  The example lists the required
   settings.

 - run 'python2.5 bootstrap.py -v1.4.3' (python2.6 mostly works, but
   some changes in the imaging library can sometimes cause problems
   when images are being scaled)

 - run './bin/buildout'

This will launch the build process, which will take a short while,
probably at least a few minutes.  Hopefully this will go smoothly, but
you may see errors here related to missing dependency libraries on
your system.  If this is the case, please contact the developer for
support resolving these issues.

Before you can use this software you must set up a PostGreSQL
database, using the name, owner, and password specified in the
local_settings.py file.  Also, the PL/Python language must be
installed.  Assuming PostGreSQL is installed on your host, this can
usually be achieved with the following commands, run as the "postgres"
user:

 $ createuser <DATABASE_USER>
 $ psql
 postgres=# \password <DATABASE_USER>
 <enter password as prompted>
 postgres=# \q
 $ createdb -O <DATABASE_USER> <DATABASE_NAME>
 $ createlang plpgsql <DATABASE_NAME>

...where "$" is the shell prompt and "postgres=#" is the psql client
prompt.

Once the software has been successfully built and the database has
been set up, you will run the following commands:

 - './bin/django syncdb': This initializes the database with the
   required tables and initial data.  The first time you try this you
   will be prompted to enter a superuser username and password.  Also,
   first time you run this you will see a big warning message about
   LDAP groups not being initialized.  Follow the instructions of
   that message and again run:

 - './bin/django syncdb': The second run of this command finishes the
   initialization.

 - './bin/django runserver': To start the development server.

At this point you should have a fully functional gallery application
running in development mode on http://localhost:8000/.

Congratulations!
