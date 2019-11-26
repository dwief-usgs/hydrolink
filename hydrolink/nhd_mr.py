#Import packages
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import difflib
from shapely.geometry import Point, LineString
import csv
import re
import os.path

############################################################################################
############################################################################################
'''
Author
---------
Daniel Wieferich: dwieferich@usgs.gov

Description
---------
Module that allows for hydrolinking of data to the National Hydrography Dataset Medium Resolution V.2.1.
Classes and methods are designed to handle one feature at a time.
'''
class MedResPoint:
    def __init__(self, feature_id, init_lat, init_lon, init_crs=4269, stream_name=None, buffer_m=1000):
        '''
        Description
        ------------
        Initiates attributes for linking a point to the NHD High Resolution
        
        Parameters
        ------------
        feature_id: str, user supplied identifier
        init_lat: float, latitude of the point to be hydrolinked
        init_lon: float, longitude of the point to be hydrolinked
        init_crs: int, coordinate reference system, default is 4269 which is NAD83
        stream_name: user supplied name of the stream a point is intended to be linked, optional
        buffer_m: distance in meters to search around a point, for identifying reaches of interest, max is 2000

        Notes
        ------------
        x,y coordinate in NAD83 (CRS 4269) or WGS84 (CRS 4326) are recommended
        stream_name works best without abbreviations
        larger buffers will take much longer to run, recommended to use the smallest buffer possible 
        '''
        if buffer_m > 2000:
            print ('Maximum buffer is 2000 meters. To run efficiently it is recommended to use the smallest buffer possible.')
            self.message('Buffer is to large, reduce buffer to less than 2000 meters.')
            self.status = 0
        else:
            self.id = str(feature_id)
            self.init_lat = float(init_lat)
            self.init_lon = float(init_lon)
            self.init_crs = int(init_crs)
            self.stream_name = str(stream_name)
            self.buffer_m = int(buffer_m)
            self.status = 1  # where 0 is failed, 1 is worked
            self.message = ''
            self.reach_query = None
            self.reach_df = None
            self.best_reach = {
                'init_id':feature_id, 
                'init_stream':stream_name,
                'stream_clean_ref': stream_name.lower()
                }
            self.no_data = {
                'GNIS_NAME': None,
                'LENGTHKM': None,
                'PERMANENT_IDENTIFIER': None,
                'REACHCODE': None,
                'geometry': None,
                'snap_meas': None,
                'snap_xy': None,
                'hl_snap_meters': None,
                'to_node_meters': None,
                'closest': None,
                'name_check': None,
                'mult_reach_ct': None,
                'name_check_txt': None,
                'meas': None
                }
        
    def crs_to_4269(self):
        '''
        Description
        ------------
        Converts coordinate reference system to NAD83 aka crs 4269, and verifies coordinates are within United States.
        Simple way of handling multiple crs, and providing user feedback before running service calls.
        '''
        if self.init_crs == 4269:
            pass
        else:
            try:
                #build shapely point from coordinates
                init_point = Point(self.init_lon, self.init_lat)
                #create geoseries of shapely point  
                pt_gdf = gpd.GeoSeries(init_point)
                #set crs of geoseries, using user provided crs
                epsg = f'epsg:{str(self.init_crs)}'
                crs={'init':epsg}
                pt_gdf.crs = crs
                #reporject point
                pt_gdf.to_crs({'init':'epsg:4269'})
                #overwrite initial point data with crs 4269 representation
                self.init_lon = pt_gdf[0].x
                self.init_lat = pt_gdf[0].y
                self.init_crs = 4269

                #Test to make sure coordinates are within U.S. including Puerto Rico and Virgian Islands.  
                #This is based on a general bounding box and intended to pick up common issues like missing values, 0 values and positive lon values
                if self.init_lat and (float(self.init_lat) > 17.5 and float(self.init_lat) < 71.5) and self.init_lon and (float(self.init_lon) < -64.0 and float(self.init_lon)> -178.5):
                    self.message = f'Coordinates for id: {self.id} are outside of the bounding box of the United States.'
                    self.error_handling()
                
            except:
                self.message = f'Issues handling provided coordinate system for {self.id}. Consider using a common crs like 4269 (NAD83) or 4326 (WGS84).'
                self.error_handling()
        
    def build_reach_query(self, service='network_flow'):
        '''
        Description
        ------------
        Builds query needed to return reaches of interest based on coordinates and buffer supplied by user.
        
        Parameters
        ------------
        service = define web service to use for query, options "network_flow" or "nonnetwork_flow"
        '''
        q = f"geometryType=esriGeometryPoint&inSR={self.init_crs}&geometry={self.init_lon},{self.init_lat}&distance={self.buffer_m}&units=esriSRUnit_Meter&outSR=4269&f=JSON&outFields=GNIS_NAME,LENGTHKM,COMID,REACHCODE,PERMANENT_IDENTIFIER&returnM=True"
        if service == 'network_flow':
            base_url = 'https://inlandwaters.geoplatform.gov/arcgis/rest/services/NHDPlus/NHDPlus/MapServer/2/query?'
            self.reach_query = f"{base_url}{q}"
        elif service == 'nonnetwork_flow':
            base_url = 'https://inlandwaters.geoplatform.gov/arcgis/rest/services/NHDPlus/NHDPlus/MapServer/3/query?'
            self.reach_query = f"{base_url}{q}"        

            
    def find_closest_reaches(self, n=6):
        '''
        Description
        ------------
        Retrieve reaches within buffer distance, buffer_m attribute, of point. Orders results closest to furthest.
        
        Parameters
        ------------
        n = int, number of reaches to return via self.reach_df   
        '''
        if self.status==1:
            try:
                self.reach_json = requests.get(self.reach_query).json() #bringing data directly into geopandas losses measures... need to look into avoiding this
                
                #Use JSON to return geodataframe
                reaches = []
                for feature in self.reach_json['features']:
                    attributes = feature['attributes']
                    line_geo = LineString([Point(float(x[0]),float(x[1])) for x in feature['geometry']['paths'][0]])
                    attributes.update({'geometry':line_geo})
                    reaches.append(attributes)

                gdf = gpd.GeoDataFrame(reaches)

                #  test if any data was returned
                if len(gdf.index)>0:
                    init_point = Point(self.init_lon, self.init_lat)    
                    gdf['snap_meas']=gdf.geometry.project(init_point) #for df calculate measure down reach where init point would snap to that reach
                    id_list = list(set(gdf['PERMANENT_IDENTIFIER'].tolist())) #create list of identifiers
                    reach_data = []

                    #Wanted to run interpolate on entire gdf but geopandas is looking for a value and wont run on df               
                    for pid in id_list:
                        reach_gdf = gdf.loc[gdf['PERMANENT_IDENTIFIER']==pid]
                        reach_gdf['snap_xy']=reach_gdf.geometry.interpolate(reach_gdf.iloc[0]['snap_meas']) #for reach find x,y on line closest to input x,y
                        snap_xy = reach_gdf.iloc[0]['snap_xy']

                        # build line representing snap path and measure it
                        snap_point = Point(snap_xy.x, snap_xy.y)
                        hl_snap_meters = build_meas_line(snap_point, init_point, crs={'init':'epsg:4269'})

                        # build lines to terminal nodes of reach and measure them
                        for line in self.reach_json['features']:
                            if line['attributes']['PERMANENT_IDENTIFIER']==pid:
                                m_range = [x[2] for x in line['geometry']['paths'][0]]
                                for node in line['geometry']['paths'][0]:
                                    max_m = max(m_range)
                                    min_m = min(m_range)
                                    if node[2]==max_m:
                                        max_coord = Point(node[0], node[1])
                                        to_max_coord_meters = build_meas_line(max_coord, init_point, crs={'init':'epsg:4269'})
                                    elif node[2]==min_m:
                                        min_coord = Point(node[0], node[1]) 
                                        to_min_coord_meters = build_meas_line(min_coord, init_point, crs={'init':'epsg:4269'})
                                to_node_meters = min(to_min_coord_meters, to_max_coord_meters)

                        #build dictionary of results
                        d = reach_gdf.iloc[0].to_dict()
                        d.update({"hl_snap_meters":hl_snap_meters,"to_node_meters":to_node_meters})
                        reach_data.append(d)

                    #keep n number of closest reaches, order them ascendingly and number closest=1 to furthest=n 
                    df = (pd.DataFrame(reach_data)).nsmallest(n,'hl_snap_meters',keep='all')
                    df = df.sort_values(by=['hl_snap_meters'])
                    df = df.reset_index(drop=True)
                    df['closest'] = df.index +1

                    self.reach_df = df
                else:
                    self.message = f'no reaches retrieved for id: {self.id}'
                    self.error_handling()
            except:
                self.message = f'find best reach failed for id: {self.id}. possibly service call issue'
                self.error_handling()
    
    def stream_match(self):
        '''
        Description: determine if user supplied stream name matches gnis stream name in nhd
        Note: It would be ideal to use np.where or alike to assign name_check values to all of the rows 
        at one time but the fuzzy match was not working so current work around using itertuples.  Also
        should be able to delete name_check_text.
        '''
        if self.status==1:
            if self.reach_df is not None and hasattr(self, 'reach_df') and hasattr(self, 'stream_name'):
                df = self.reach_df
                if 'GNIS_NAME' in df and self.stream_name is not None:
                    #If GNIS is not null and names match assign a 1
                    df['name_check'] = np.where((df.GNIS_NAME.notnull()) & (df.GNIS_NAME.str.lower()==self.stream_name.lower()), 1.0, 0)
                    for row in df.itertuples():
                        #pid = (row.PERMANENT_IDENTIFIER)
                        if row.name_check == 1:
                            df.at[row.Index, 'name_check_txt'] = 'exact match of stream names'
                            self.best_reach.update({'stream_clean_ref':self.stream_name.lower()})

                        elif row.GNIS_NAME and self.stream_name is not None:
                            gnis= (row.GNIS_NAME).lower()
                            #stream_lc = (item.stream_name).lower()
                            stream_lc = clean_stream_name(self.stream_name)
                            self.best_reach.update({'stream_clean_ref':stream_lc})
                            if 'tributary' not in stream_lc and 'branch' not in stream_lc:
                                match_ratio = difflib.SequenceMatcher(lambda x: x == " ", gnis, stream_lc).ratio()
                                df.at[row.Index, 'name_check'] = match_ratio
                                # If match ratio is greater than 0.75, update df field 'name_check_txt'
                                if match_ratio >= 0.75:
                                    df.at[row.Index, 'name_check_txt'] = 'most likely match of stream names based on fuzzy match'
                                # If match ratio is greater than 0.6 and less than 0.6, update df field 'name_check_txt'
                                elif 0.75 > match_ratio >= 0.6:
                                    df.at[row.Index, 'name_check_txt'] = 'likely match of stream names based on fuzzy match'                
                            else:
                                df.at[row.Index, 'name_check_txt'] = 'no stream matching occured due to name containing reference to tributary' 
                        else:
                            df.at[row.Index, 'name_check_txt'] = 'stream names are unlikely match'
                else:
                    df['name_check_txt'] = 'missing one or both stream names'
                    df['name_check'] = 0
        
    def select_best_reach(self):
        '''
        Description
        ------------
        Of returned reaches finds most likely reach based on available information
        -First checks to see if any reaches have an exact match of names
            -If number of reaches with exact name match equals 1 that is the reach to recommend
            -If number of reaches with exact name match > 1 take the one that is closest to the point
                -If more than one reach has exact name match and are equally close to the point grab the first but note that multiple reaches so that we can recommend taking a closer look
        -If no reaches with exact name match then check for fuzzy matches over 0.75 cutoff
        -If number of reaches with fuzzy name match equals 1 that is the reach to recommend
        -If number of reaches with fuzzy name match > 1 take the one that is closest to the point
            -If more than one reach has fuzzy name match and are equally close to the point grab the first one but note that multiple reaches so that we can recommend taking a closer look
        -If fuzzy match < 0.75 just take closest reach.
        '''
        if self.status==1:
            if self.reach_df is not None:
                df = self.reach_df
                name_check_1 = df.loc[df['name_check']==1]

                if len(name_check_1.index)==1:
                    vals = name_check_1.iloc[0].to_dict()
                    vals.update({'mult_reach_ct': len(name_check_1)})
                    self.best_reach.update(vals)
                elif len(name_check_1.index)>1:
                    closest = name_check_1.nsmallest(1,'hl_snap_meters', keep='all')
                    #take first indexed reach in list of closest reaches
                    #if multiple reaches have same hl_snap_meters and matching stream names the count will be recorded in "mult_reach_ct" field
                    vals = closest.iloc[0].to_dict()
                    vals.update({'mult_reach_ct':len(closest)})
                    self.best_reach.update(vals)
                elif len(name_check_1.index)==0:
                    name_check_lt1 = df.loc[df['name_check']>=0.75]
                    if len(name_check_lt1.index) == 1:
                        vals = name_check_lt1.iloc[0].to_dict()
                        vals.update({'mult_reach_ct':len(name_check_lt1)})
                        self.best_reach.update(vals)
                    elif len(name_check_lt1.index)>1:
                        closest = name_check_lt1.nsmallest(1,'hl_snap_meters', keep='all')
                        vals = closest.iloc[0].to_dict()
                        vals.update({'mult_reach_ct':len(closest)})
                        self.best_reach.update(vals)
                    elif len(name_check_lt1.index)==0:
                        closest = df.nsmallest(1,'hl_snap_meters', keep='all')
                        vals = closest.iloc[0].to_dict()
                        vals.update({'mult_reach_ct':len(closest)})
                        self.best_reach.update(vals)
                else:
                    self.message = f'unable to select best reach for id: {self.id}.'
                    self.error_handling()
            else:
                self.message = f'no dataframe for: {self.id}. make sure functions are called in correct sequence'
                self.error_handling()
#        self.best_reach.update(self.message)
        
    def get_hem_measure(self):
        '''
        Description
        ------------
        Use HEM SOE extension HEMPointEvents to pass the snap location on best reach to return reach measure.
        Documentation of HEMPointEvents is found https://edits.nationalmap.gov/hem-soe-docs/soe-reference/hem-point-events.html
        '''
        if self.status == 1:
            if 'REACHCODE' in self.best_reach.keys():
                hem_get_mr_hl = 'https://ofmpub.epa.gov/waters10/PointIndexing.Service'
                x = self.best_reach['snap_xy'].x
                y = self.best_reach['snap_xy'].y
                xy_mr2 = f"POINT({x} {y})"

                payload_mr2 = {
                    'optNHDPlusDataset': '2.1',
                    'pGeometry': xy_mr2,
                    'pGeometryMod': 'SRID=4269',
                    'pOutputPathFlag': 'TRUE',
                    'pPointIndexingMaxDist': '0.1', #Kilometers
                    'pPointIndexingMethod':'DISTANCE',
                    'pResolution': '3',
                    'pPointIndexingFcodeDeny' : [56600],
                    'pReturnFlowlineGeomFlag':'FALSE',
                    'f':'json'}

                self.mr_hl = requests.post(hem_get_mr_hl,params=payload_mr2,verify=False).json()
                
            #    print(mr_hl)
            #     if hr_xy['resultStatus'] == 'success' and hr_xy['features']:
            #         self.hl_reach_meas = hr_xy['features'][0]['attributes']
            #         meas = hr_xy['features'][0]['attributes']['MEASURE']
            #         self.best_reach.update({"meas": meas})
            #     else:
            #         self.message='get_hem_measure failed'
            #         self.best_reach.update({"meas": None, 'message': self.message})
            # else:
            #     self.message = f'no reachcode for running measure on id: {self.id}'
            #     self.best_reach.update(self.no_data)
            #     message = {'message': self.message}
            #     self.best_reach.update(message)
        
    
    def error_handling(self):
        '''
        Description
        ------------
        when error is captured, document and send message to user
        '''
        self.status = 0
        self.best_reach.update(self.no_data)
        message = {'message': self.message}
        self.best_reach.update(message)  
        print (self.message)

    def write_best(self, outfile_name='hydrolink_mr_output.csv'):
        file_exists = os.path.isfile(outfile_name)
        with open(outfile_name, 'a', newline='') as csv_file:
            field_names = self.best_reach.keys()
            writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter=',')
            if not file_exists:
                writer.writeheader()
            writer.writerow(self.best_reach)

    def write_reach_options(self, outfile_name='hydrolink_mr_reach_output.csv'):
        if self.status ==1:
            file_exists = os.path.isfile(outfile_name)
            with open(outfile_name, 'a', newline='') as csv_file:
                for r in self.reach_df.to_dict(orient='records'):
                    r.update({'init_id':self.id})
                    writer = csv.DictWriter(csv_file, r.keys(), delimiter=',')
                    if not file_exists:
                        writer.writeheader()
                        file_exists=True
                    writer.writerow(r)

def build_meas_line(point1, point2, crs={'init':'epsg:4269'}):
    '''
    Description: where point1 and 2 are shapely points
    '''
    line_geom = LineString([point1, point2]) 
    line_geoseries = gpd.GeoSeries(line_geom)           
    line_geoseries.crs = crs
    line_geoseries=line_geoseries.to_crs({'init':'epsg:5070'})
    line_length_meters = line_geoseries.length[0]
    return line_length_meters

def clean_stream_name(name):
    '''
    Description: replace common abbreviations, this needs improvement but be careful not to replace 
    strings we dont want to this code currently assumes GNIS_NAME never contains abbreviations... 
    something to verify. If you have a better way to do this let me know!!!!
    '''
    stream = name
    stream_lower = f'{stream.lower()} '
    stream_lower = re.sub("[\(\[].*?[\)\]]", "", stream_lower)
    stream_lower = stream_lower.replace(' st. ', ' stream')
    stream_lower = stream_lower.replace(' st ', ' stream')
    stream_lower = stream_lower.replace(' rv. ', ' river')
    stream_lower = stream_lower.replace(' rv ', ' river')
    stream_lower = stream_lower.replace('unt ', 'unnamed tributary ')
    stream_lower = stream_lower.replace(' trib. ', ' tributary')
    stream_lower = stream_lower.replace(' trib) ', ' tributary')
    stream_lower = stream_lower.replace(' trib ', ' tributary')
    stream_lower = stream_lower.replace(' ck ', ' creek')
    stream_lower = stream_lower.replace(' ck. ', ' creek')
    stream_lower = stream_lower.replace(' br ', ' branch')
    stream_lower = stream_lower.replace(' br. ', ' branch')
    stream_name = stream_lower.strip()
    return stream_name  

############################################################################################
############################################################################################