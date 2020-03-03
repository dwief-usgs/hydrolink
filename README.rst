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

* Free software: unlicense
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
[unlicense](https://unlicense.org/).

This software is preliminary or provisional and is subject to revision. It is being provided to meet the need for timely best science. The software has not received final approval by the U.S. Geological Survey (USGS). No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. The software is provided on the condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from the authorized or unauthorized use of the software.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
