# package name

#import pkg_resources  # part of setuptools


# Import 
from . import nhd_hr
from . import nhd_mr


# provide version, PEP - three components ("major.minor.micro")
#__version__ = pkg_resources.require("package_nm")[0].version


# metadata retrieval
#def get_package_metadata():
#    d = pkg_resources.get_distribution('package_nm')
#    for i in d._get_metadata(d.PKG_INFO):
#        print(i)
