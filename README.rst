=========
HydroLink
=========


.. image:: https://img.shields.io/pypi/v/hydrolink.svg
        :target: https://pypi.python.org/pypi/hydrolink

.. image:: https://img.shields.io/travis/dwief-usgs/hydrolink.svg
        :target: https://travis-ci.com/dwief-usgs/hydrolink

.. image:: https://readthedocs.org/projects/hydrolink/badge/?version=latest
        :target: https://hydrolink.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Python package with methods to hydrolink (address) information to National Hydrography Datasets using web services.

* Free software: CC0 1.0
* Documentation: https://hydrolink.readthedocs.io.


Contact
--------
Daniel Wieferich (dwieferich@usgs.gov)


Purpose
--------
Hydrolinking refers to the linkage of spatial data to a stream network.  This is similar to the analogy of addresses in a road network.  This package is specific to versions of the National Hydrography Dataset that have mapservices (currently the NHDPlusV2.1 Medium Resolution, NHD High Resolution, and NHD High Resolution Plus are supported). Hydrolinking data to the NHD provides context to the hydrographic network and allows for integration of information in a common spatial framework/context.


Copyright and License
--------
This USGS product is considered to be in the U.S. public domain, and is licensed under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

Although this software program has been used by the U.S. Geological Survey (USGS), no warranty, expressed or implied,
is made by the USGS or the U.S. Government as to the accuracy and functioning of the program and related program
material nor shall the fact of distribution constitute any such warranty, and no responsibility is assumed by the
USGS in connection therewith.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
