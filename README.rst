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




Python package with methods to hydrolink (address) point information to National Hydrography Datasets using web services. Docs and tests are in progress.

* Free software: unlicense
* Documentation: https://hydrolink.readthedocs.io.
* Related HydroLink Efforts: https://doi.org/10.5066/P9KRWCFL


Contact
-------
Daniel Wieferich (dwieferich@usgs.gov)


Purpose
-------
Hydrolink refers to the linkage of spatial data to a stream network.  This is similar to the analogy of providing an addresses on a road network and provides context to the hydrographic network allowing for integration of information into a common spatial framework/context.  This package accepts point data and HydroLinks to versions of the National Hydrography Dataset (NHD) using MapServices. Two versions of the NHD are currently support including the NHDPlusV2.1 Medium Resolution and the NHD High Resolution. 

Requirements
------------
Currently working to get startup and requirements in a more usable state. In meantime requirements.txt shows condensed version of packages, while requirements_dev shows a full list of packages used in development.

Getting Started
---------------
Install the package
* pip install git+https://github.com/dwief-usgs/hydrolink.git

Using the hydrolinker command line tool you can HydroLink all points in a CSV file.  

* Access help menu -> python -m hydrolink.hydrolinker --help
* Example running with default options ->  python -m hydrolink.hydrolinker --input_file=file_name.csv

Two Jupyter Notebooks are included to show a few basic capabilities for both NHD versions.

* example-using-single-point-nhd-high-resolution.ipynb -> Jupyter notebook with descriptions on how to run hydrolink methods on NHD High Resolution for a single point location.
* example-using-single-point-nhd-medium-resolution.ipynb -> Jupyter notebook with descriptions on how to run hydrolink methods on NHDPlusV2.1 for a single point location.

Documentation
-------------
Documentation can be found at this link ()

Documentation HTML can be generated using this command from the docs folder. 

``
make html
``

Copyright and License
---------------------
This USGS product is considered to be in the U.S. public domain, and is licensed under
[unlicense](https://unlicense.org/).

This software is preliminary or provisional and is subject to revision. It is being provided to meet the need for timely best science. The software has not received final approval by the U.S. Geological Survey (USGS). No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. The software is provided on the condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from the authorized or unauthorized use of the software.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
