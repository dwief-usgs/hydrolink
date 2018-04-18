Batch HydroLink
===============================================================================================================

-----------
Contact:
-----------
Daniel Wieferich (dwieferich@usgs.gov)


-----------
Purpose:
-----------
Linking observation and spatial feature data to the National Hydrography Dataset (NHD) provides context to the hydrographic network and provides access to additional hydrography information within the NHD for research and analitical purposes.
This repository contains Python code that explores methods that link sampling and feature information to the NHDPlusV2 and NHDHR datasets using a batch approach and providing a level of certainty.  

  
-----------
Additional Details:
-----------
This code performs a hydrolink batch process on a text file (.csv ) or shapefile (.shp) using user defined latitude and longitude fields. 
The code returns the reachcode and measure of the closest position on the High Resolution National Hydrography Dataset and the Medium Resolution NHDPlusV2.1 using web services. 
The code also uses snap distance and stream name to help quantify a level of certainty. Levels of certainty currently exist only for the NHDPlusV2.1, due to the availability of 
needed information from current web services.  
  
To help standardize linked data processes, the code uses similar methods (based on available web services) to link information to the hydrography as the USGS HydroLink Tool ( https://maps.usgs.gov/hydrolink/ ).
  
-----------
Development Status:
-------------------
Software documented in this repository are unpublished and will often be under development.  Collaborative efforts to help improve code are encouraged.
This software is preliminary or provisional and is subject to revision. It is being provided to meet the need for timely best science. 
The software has not received final approval by the U.S. Geological Survey (USGS). No warranty, expressed or implied, is made by the USGS or the U.S. Government as to the functionality of the software and related material nor shall the fact of release constitute any such warranty. The software is provided on the condition that neither the USGS nor the U.S. Government shall be held liable for any damages resulting from the authorized or unauthorized use of the software. 



----------------------
Copyright and License:
---------------------
This USGS product is considered to be in the U.S. public domain, and is licensed under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

Although this software program has been used by the U.S. Geological Survey (USGS), no warranty, expressed or implied,
is made by the USGS or the U.S. Government as to the accuracy and functioning of the program and related program
material nor shall the fact of distribution constitute any such warranty, and no responsibility is assumed by the
USGS in connection therewith.
