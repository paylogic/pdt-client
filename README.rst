pdt-client
==========

pdt-client is a client tool for `Paylogic Deployment Tool <https://github.com/paylogic/pdt>`_ web application

.. image:: http://img.shields.io/pypi/v/pdt-client.svg
   :target: https://pypi.python.org/pypi/pdt-client
.. image:: http://img.shields.io/coveralls/paylogic/pdt-client/master.svg
   :target: https://coveralls.io/r/paylogic/pdt-client
.. image:: https://travis-ci.org/paylogic/pdt-client.svg?branch=master
    :target: https://travis-ci.org/paylogic/pdt-client
.. image:: https://readthedocs.org/projects/pdt-client/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://readthedocs.org/projects/pdt-client/

.. contents::

Installation
------------

::

    pip install pdt-client

Usage
-----

Client has single entry point console script:

::

    pdt-client --help

Push migrations data
^^^^^^^^^^^^^^^^^^^^

::

    pdt-client migration-data push

Check not reviewed migrations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    pdt-client migration-data get-not-reviewed

Apply migrations
^^^^^^^^^^^^^^^^

::

    pdt-client migrate


Report deployment status
^^^^^^^^^^^^^^^^^^^^^^^^

::

    pdt-client deploy


Generate a graph of the revisions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The same as the graph command of alembic offline, but enriched with the release from the PDT.

::

    pdt-client graph


Get not deployed case data
^^^^^^^^^^^^^^^^^^^^^^^^^^

::

    pdt-client case-data get-not-deployed


Contact
-------

If you have questions, bug reports, suggestions, etc. please create an issue on
the `GitHub project page <http://github.com/paylogic/pdt-client>`_.

License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

Please refer to the `license file <https://github.com/paylogic/pdt-client/blob/master/LICENSE.txt>`_

© 2015 Anatoly Bubenkov, Paylogic International and others.
