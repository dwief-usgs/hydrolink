"""Allows for HydroLinking of data to the National Hydrography Dataset High Resolution (NHDHR).

Module that HydroLinks data to the National Hydrography Dataset High Resolution (NHDHR). Classes
and methods are designed to handle one feature at a time.  This module is designed to handle errors
by returning a message to objects to help facilitate HydroLinking of multiple points in a single program.
Currently only HydroLinks point data (not lines or polygons) to flowlines or waterbodies. The terms
"HydroLinking" and "addressing" are used synonymously throughout this code and both refer to making
a relationship between a feature and a stream network, similar to addresses assigned to road networks.

Author
----------
Name: Daniel Wieferich
Contact: dwieferich@usgs.gov
"""

# Import packages
import requests
import csv
import os.path
from hydrolink import utils
from shapely.geometry import Point
############################################################################################
############################################################################################


class HighResPoint:
    """Class specific for HydroLinking point data to the NHDHR."""

    def __init__(self, source_identifier, input_lat, input_lon, input_crs=4269, water_name=None, buffer_m=1000):
        """Initiate attributes for HydroLinking point data to the NHDHR.

        During initiation of an object the buffer is verified to be less than 2000 meters.  Initiation
        also converts supplied coordinates to NAD83 (crs=4269), and validates that coordinates are within
        the bounds of the United States bounding box.  If any of these conditions caused a failed initiation
        of an object an error message is created and the HydroLinking process does not run.

        Parameters
        ----------
        source_identifier: str
            User supplied identifier
        input_lat: float
            Latitude of the point to be HydroLinked
        input_lon: float
            Longitude of the point to be HydroLinked
        input_crs: int
            Coordinate reference system, default is 4269 which is NAD83
        water_name: str
            User supplied name of the waterbody that a point occurs on. Optional
        buffer_m: int
            Distance in meters. Used as buffer to search for canidate NHD features
            for HydroLinking

        Notes
        ----------
        Coordinate system recommendations
            Tested NAD83 (CRS 4269), WGS84 (CRS 4326), Albers (CRS 5070).  These are recommended.
        Source name recommendations
            To be most effective the water_name variable should contain no abbreviations and
            only contain official names from USGS Geospatial Names Information System.
        Buffer recommendations
            Larger buffers will take much longer to run so it is to test need for large buffer
            and using the smallest buffer possible.
        Expected speed note
            A set of 10 points were hydrolinked (4/13/2020) with average speed of 1 point per 0.74 seconds. This
            includes request of data, name matching, and writing to csv.

        """
        self.source_id = str(source_identifier)
        if water_name and str(water_name) != 'nan':
            self.water_name = str(water_name)
        else:
            self.water_name = None
        self.buffer_m = int(buffer_m)
        self.status = 1  # where 0 is failed, 1 is worked properly
        self.message = ''
        self.flowline_query = None
        self.waterbody_query = None
        self.hydrolink_waterbody = None

        # If buffer is greater than 2000 do not run and set error message
        if buffer_m > 2000:
            self.message = ('Maximum buffer is 2000 meters, reduce buffer.')
            self.error_handling()

        # If buffer is less than or equal to 2000 then run
        else:
            # Try converting to NAD83 (crs==4269) coordinate system if different coordinate system provided
            # If fails do not run and set error message
            try:
                self.init_lon = float(input_lon)
                self.init_lat = float(input_lat)
                self.input_point = Point(self.init_lon, self.init_lat)

                if int(input_crs) != 4269:
                    self.init_lon, self.init_lat = utils.crs_to_nad83(self.input_point, input_crs)

                # Test to make sure coordinates are within U.S. including Puerto Rico and Virgian Islands.
                # This is based on a general bounding box and intended to pick up common issues like missing values, 0 values and positive lon values
                if (float(self.init_lat) > 17.5 and float(self.init_lat) < 71.5) and (float(self.init_lon) < -64.0 and float(self.init_lon) > -178.5):
                    pass
                else:
                    self.message = f'Coordinates for id: {self.source_id} are outside of the bounding box of the United States.'
                    self.error_handling()

            except:
                self.message = f'Issues handling provided coordinate system or coordinates for {self.source_id}. Consider using a common crs like 4269 (NAD83) or 4326 (WGS84).'
                self.error_handling()

    def hydrolink_method(self, method='name_match', hydro_type='flowline', outfile_name='nhdhr_hydrolink_output.csv', similarity_cutoff=0.6):
        """Build HydroLinking pipeline based on specified method and hydro_type.

        Builds commonly used HydroLink pipelines for users.
        These pipelines write data to the outfile specified in "outfile_name".

        Parameters
        ----------
        method: {'name_match', 'closest'}, default 'name_match'
            Method for HydroLinking data. Supported methods are

            - ``'name_match'``: This default method HydroLinks data to the closest NHD feature with a name similarity
            that meets the specified similarity_cutoff. If no flowlines meet similarity cutoff the method HydroLinks
            data to the closest NHD feature.
            - ``'closest'``: This method HydroLinks data to the closest NHD feature.

        hydro_type: {'waterbody', 'flowline'}, default 'flowline'
            Type of features to HydroLink. Feature types as defined by NHDHR.

            - ``'flowline'``: This default feature type specifies NHD feature type of flowline.
            Flowline features represent water types such as streams, rivers, canals/ditches.
            Waterbodies also have line representations as flowline type.
            - ``'waterbody'``: This feature type specifies NHD feature type of waterbody.
            Waterbody features represent water types such as lakes, ponds, estuaries, reservoirs,
            marshes, swamps.

        outfile_name: str
            Name and directory of csv output file.  default is 'nhdhr_hydrolink_output.csv'.
        similarity_cutoff: float
            Values between 0 and 1.0, range of similarity between 0 representing no match to 1.0 being perfect match.

        """
        if hydro_type in ['waterbody', 'flowline'] and method in ['name_match', 'closest'] and 0.6 <= similarity_cutoff <= 1.0:
            if self.status == 1:
                self.build_nhd_query(query=['hem_flowline', 'hem_waterbody'])
                if hydro_type == 'waterbody':
                    self.is_in_waterbody()
                self.query_flowlines()
                self.hydrolink_flowlines()
                if method == 'name_match':
                    self.select_closest_flowline_w_name_match(similarity_cutoff=similarity_cutoff)
                elif method == 'closest':
                    self.select_closest_flowline()
                self.write_hydrolink(outfile_name=outfile_name)
            else:
                self.write_hydrolink(outfile_name=outfile_name)

    def build_nhd_query(self, query=['hem_flowline', 'hem_waterbody']):
        """Build queries to return required data for HydroLink process.

        Parameters
        ----------
        query: list, default ['hem_flowline', 'hem_waterbody']
            Specifies MapServer instance to use for HydroLink. Uses user specified information from object.
            Supported queries include

            - ``'hem_flowline'``: Default query that returns data for flowline features within a buffer of
            a given location. This query uses the following Hydro Event Management (HEM) MapServer layer
            https://hydromaintenance.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/1.
            - ``'hem_waterbody'``: Query that returns data for the waterbody feature that intersects a given location.
            This query uses the following Hydro Event Management (HEM) MapServer layer
            https://hydromaintenance.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/2.
            - ``'hem_waterbody_flowline'``: Query that returns data for flowline features within a waterbody.
            This query uses the following Hydro Event Management (HEM) MapServer layer
            https://hydromaintenance.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/1.

        Note(s)
        ----------
        Recommended queries for NHDHR are currently those supported by Hydro Event Management (HEM). In this MapServer
        all flowlines are in one layer and this layer provides a recent version of NHDHR data.

        The National Map Mapservers (including HighResPlus) can also be used but these services split flowlines
        into in-network and non-network and will require multiple service calls (not handled in current code).

        """
        # hem flowlines within a buffer of coordinates
        if 'hem_flowline' in query:
            q = f"where=ftype%20NOT%20IN%20(420,428,566)&geometryType=esriGeometryPoint&inSR=4269&geometry={self.init_lon},{self.init_lat}&distance={self.buffer_m}&units=esriSRUnit_Meter&outSR=4269&f=JSON&outFields=gnis_name,lengthkm,permanent_identifier,reachcode&returnM=True"
            base_url = 'https://hydromaintenance.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/1/query?'
            self.flowline_query = f"{base_url}{q}"

        # hem waterbody returns information about hem waterbodies that the point is within
        if 'hem_waterbody' in query:
            q = f"geometryType=esriGeometryPoint&spatialRel=esriSpatialRelWithin&inSR=4269&geometry={self.init_lon},{self.init_lat}&f=JSON&outFields=permanent_identifier,gnis_name,ftype,reachcode&returnGeometry=False"
            base_url = 'https://hydromaintenance.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/2/query?'
            self.waterbody_query = f"{base_url}{q}"

        # returns flowlines associated with a waterbody (e.g. reservoir, lake...)
        if 'hem_waterbody_flowline' in query:
            q = f"where=WBAREA_PERMANENT_IDENTIFIER%20IN%20(%27{self.hydrolink_waterbody['nhdhr waterbody permanent identifier']}%27)&outSR=4269&f=JSON&outFields=gnis_name,lengthkm,permanent_identifier,reachcode&returnM=True"
            base_url = 'https://hydromaintenance.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/1/query?'
            self.flowline_query = f"{base_url}{q}"

        # The National Map (including HighResPlus) are included for future reference, not currenlty supported
        # if service == 'TNM_HR':
        #    base_url = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/5/query?'
        #    base_url_off_network = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/5/query?'
        # if service == 'TNM_HRPlus':
        #    base_url = 'https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/2/query?'

    def is_in_waterbody(self):
        """Check to see if point location falls within waterbody feature.

        Check to see if point location falls within waterbody feature.  If it does it collects HydroLink
        data for the waterbody and also resets query of flowlines (self.flowline_query) to only return
        flowlines that intersect with the waterbody.

        Parameters
        ----------
        self.waterbody_query: str
            Query built in build_nhd_query

        Returns
        ----------
        self.hydrolink_waterbody: dictionary
            Attributes of HydroLink (address) to waterbody
        self.build_nhd_query: list
            Reset self.build_nhd_query to query only flowlines within waterbody

        """
        # if status == 0 or if we do not have waterbody query set then skip to avoid wasted processing time
        if self.status == 1 and self.waterbody_query is not None:
            try:
                results = requests.get(self.waterbody_query).json()
                self.waterbody_json = results
                if len(results['features']) > 0:
                    self.hydrolink_waterbody = {'nhdhr waterbody permanent identifier': results['features'][0]['attributes']['permanent_identifier'],
                                                'nhdhr waterbody gnis name': results['features'][0]['attributes']["gnis_name"],
                                                'nhdhr waterbody reachcode': results['features'][0]['attributes']['reachcode']
                                                }
                    self.build_nhd_query(query=['hem_waterbody_flowline'])
                    # add name match here?
            except:
                self.message = f'is_in_waterbody failed for: {self.source_id}. possibly service call issue'
                self.error_handling()

    def query_flowlines(self):
        """Query flowlines using query built in build_nhd_query.

        Query flowlines using query built in build_nhd_query.  Handles failed requests and
        instances where no flowlines are returned.

        Parameters
        ----------
        self.flowline_query: str
            Query built in build_nhd_query

        Returns
        ----------
        self.flowlines_json: dictionary
            JSON returned from request of flowline_query.  JSON contains data about flowlines.

        """
        if self.status == 1:  # if status == 0 we don't want to waste time processing
            try:
                self.flowlines_json = requests.get(self.flowline_query).json()
                if 'features' in self.flowlines_json.keys() and len(self.flowlines_json['features']) == 0:
                    self.message = f'No flowlines selected in query_flowlines for id: {self.source_id}. Try increasing buffer.'
                    self.error_handling()

            except:
                self.message = f'query_flowlines failed for id: {self.source_id}. Request failed.'
                self.error_handling()

    def hydrolink_flowlines(self):
        """Evaluate flowlines in self.flowlines_json to understand certainty for HydroLink selection.

        Evaluate flowlines in self.flowlines_json to understand certainty for HydroLink selection.
        Evaluations include calculating distance to each flowline, calculating distance to closest
        confluence, calculate name similarity for water names. Handles instances where no flowlines
        are available and failed evaluations.

        Parameters
        ----------
        self.flowlines_json: dictionary
            JSON returned from request of flowline_query.  JSON contains data about flowlines.
        self.water_name: str
            User supplied name of the waterbody that a point occurs on. Optional
        self.input_point: shapely point
            Input location for hydrolinking. For formatting see shapely.geometry Point method

        Returns
        ----------
        self.closest_confluence_meters: float
            Distance from input point to closest confluence in meters, see utils.closest_confluence
        self.flowline_data: dictionary
            Contains information about a flowline

        """
        # if status == 0 we don't want to waste time processing
        if self.status == 1:
            if 'features' in self.flowlines_json.keys() and len(self.flowlines_json['features']) > 0:
                try:
                    flowlines_data = []
                    all_flowline_terminal_node_points = []
                    for flowline_data in self.flowlines_json['features']:
                        flowline_attributes, terminal_node_points, flowline_geo = utils.build_flowline_details(flowline_data, self.input_point, 'nhdhr', self.water_name)
                        flowlines_data.append(flowline_attributes)
                        all_flowline_terminal_node_points = all_flowline_terminal_node_points + terminal_node_points

                    self.closest_confluence_meters = utils.closest_confluence(all_flowline_terminal_node_points, self.input_point, flowline_geo)
                    self.flowlines_data = flowlines_data

                except:
                    self.message = f'hydrolink_flowlines failed for id: {self.source_id}.'
                    self.error_handling()
            else:
                self.message = f'no flowlines retrieved for id: {self.source_id}'
                self.error_handling()

    def select_closest_flowline(self, similarity_cutoff=0.6):
        """Select closest flowline.

        Selects closest flowline from flowlines_data, including all evaluation information
        for the flowline. Although name similarity is not considered for selection it is used
        to document if a name matched flowline is available. Requires output from hydrolink_flowlines.

        """
        if self.status == 1:
            df = utils.df_for_selection(self.flowlines_data)
            df = df.rename(columns={"lengthkm": "nhdhr flowline length km",
                                    "reachcode": "nhdhr flowline reachcode",
                                    "gnis_name": "nhdhr flowline gnis name",
                                    "permanent_identifier": "nhdhr flowline permanent identifier"
                                    })
            self.total_count_flowlines = df.shape[0]
            self.name_match_in_buffer = df.loc[df['flowline name similarity'] >= similarity_cutoff].shape[0]

            df = df.nsmallest(1, 'meters from flowline', keep='all')
            if df.shape[0] > 1:
                self.message = f'multiple flowlines with same snap distance for id: {self.source_id}. Use name_match method.'
                self.error_handling()

            else:
                self.hydrolink_flowline = ((df.to_dict('records'))[0])

    def select_closest_flowline_w_name_match(self, similarity_cutoff=0.6):
        """Select closest flowline with matching water name.

        HydroLink data to the closest NHD feature with a name similarity that meets the specified
        similarity_cutoff. If no flowlines meet similarity cutoff the method HydroLinks data to the
        closest NHD feature. Requires output from hydrolink_flowlines.
        """
        if self.status == 1:
            df = utils.df_for_selection(self.flowlines_data)
            df = df.rename(columns={"lengthkm": "nhdhr flowline length km",
                                    "reachcode": "nhdhr flowline reachcode",
                                    "gnis_name": "nhdhr flowline gnis name",
                                    "permanent_identifier": "nhdhr flowline permanent identifier"
                                    })
            self.total_count_flowlines = df.shape[0]
            df_1 = df.loc[df['flowline name similarity'] == 1.0]
            df_similarity = df.loc[df['flowline name similarity'] >= similarity_cutoff]
            # only 1 flowline has extact matching name
            if df_1.shape[0] == 1:
                self.hydrolink_flowline = ((df.to_dict('records'))[0])
            # more than 1 flowline has exact matching name, grab closest of matching name flowlines
            elif df_1.shape[0] > 1:
                df_1 = df_1.nsmallest(1, 'meters from flowline', keep='all')
                if df_1.shape[0] > 1:
                    self.message = f'multiple flowlines with same snap distance for id: {self.source_id}.'
                    self.error_handling()
                else:
                    self.hydrolink_flowline = ((df_1.to_dict('records'))[0])
            # only one flowline has matching name meeting similarity cutoff
            elif df_1.shape[0] == 0 and df_similarity.shape[0] == 1:
                self.hydrolink_flowline = ((df_similarity.to_dict('records'))[0])
            # select closest flowline meeting name match similarity cutoff
            elif df_1.shape[0] == 0 and df_similarity.shape[0] > 1:
                df_similarity = df_similarity.nsmallest(1, 'meters from flowline', keep='all')
                if df_similarity.shape[0] > 1:
                    self.message = f'multiple flowlines with same snap distance for id: {self.source_id}.'
                    self.error_handling()
                else:
                    self.hydrolink_flowline = ((df_similarity.to_dict('records'))[0])
            # no flowlines with name match, select closest
            else:
                df = df.nsmallest(1, 'meters from flowline', keep='all')
                if df.shape[0] > 1:
                    self.message = f'multiple flowlines with same snap distance for id: {self.source_id}.'
                    self.error_handling()
                else:
                    self.hydrolink_flowline = ((df.to_dict('records'))[0])

    def error_handling(self):
        """Handle errors throughout HydroLink."""
        self.status = 0
        print(self.message)

    def write_hydrolink(self, outfile_name='nhdhr_hydrolink_output.csv'):
        """Write HydroLink data output to CSV."""
        file_exists = os.path.isfile(outfile_name)
        if self.status == 1:
            source_data = {'source id': self.source_id,
                           'source water name': self.water_name,
                           'source lat nad83': self.init_lat,
                           'source lon nad83': self.init_lon,
                           'closest conluence meters': self.closest_confluence_meters,
                           'source buffer meters': self.buffer_m,
                           'total count flowlines in buffer': self.total_count_flowlines,
                           'hydrolink message': self.message}
            source_data.update(self.hydrolink_flowline)
            if self.hydrolink_waterbody is not None:
                source_data.update(self.hydrolink_waterbody)
        elif self.status == 0:
            source_data = {'source id': self.source_id,
                           'source water name': self.water_name,
                           'source lat nad83': self.init_lat,
                           'source lon nad83': self.init_lon,
                           'source buffer meters': self.buffer_m,
                           'hydrolink message': self.message}
        field_names = ['source id', 'source lat nad83', 'source lon nad83', 'source buffer meters',
                       'closest conluence meters', 'closest flowline order', 'total count flowlines in buffer',
                       'source water name', 'cleaned source water name', 'flowline name similarity',
                       'flowline name similarity message', 'nhdhr flowline gnis name',
                       'nhdhr flowline length km', 'nhdhr flowline permanent identifier',
                       'nhdhr flowline reachcode', 'meters from flowline', 'nhdhr flowline measure',
                       'nhdhr waterbody permanent identifier', 'nhdhr waterbody gnis name',
                       'nhdhr waterbody reachcode', 'hydrolink message'
                       ]
        with open(outfile_name, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter=',')
            if not file_exists:
                writer.writeheader()
            writer.writerow(source_data)

    # def write_flowline_options(self, outfile_name='hr_hydrolink_reach_output.csv'):
    #     """Write HydroLink data output to CSV."""
    #     if self.status ==1:
    #         file_exists = os.path.isfile(outfile_name)
    #         with open(outfile_name, 'a', newline='') as csv_file:
    #             for r in self.reach_df.to_dict(orient='records'):
    #                 r.update({'source identifier': self.source_id})
    #                 writer = csv.DictWriter(csv_file, r.keys(), delimiter=',')
    #                 if not file_exists:
    #                     writer.writeheader()
    #                     file_exists = True
    #                 writer.writerow(r)


# def get_ftype(fcode):
#     """Lookup NHD feature type based on fcode."""
#     # create dictionary with fcode:ftype pairs
#     ftypes = {
#         '436': 'Reservoir',
#         '390': 'LakePond',
#         '493': 'Estuary',
#         '466': 'SwampMarsh',
#         '361': 'Playa',
#         '378': 'Ice Mass',
#         '566': 'Coastline',
#         '334': 'Connector',
#         '336': 'CanalDitch',
#         '558': 'ArtificialPath',
#         '428': 'Pipeline',
#         '460': 'StreamRiver',
#         '420': 'Underground Conduit'
#     }
#     ftype = ftypes[str(fcode)]
#     return ftype

############################################################################################
############################################################################################
