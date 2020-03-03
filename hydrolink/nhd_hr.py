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
from hydrolink import utils
############################################################################################
############################################################################################
'''
Author
------------
Daniel Wieferich: dwieferich@usgs.gov

Description
------------
Module that allows for hydrolinking of data to the High Resolution National Hydrography Dataset.
Classes and methods are designed to handle one feature at a time.
'''
class HighResPoint:
    def __init__(self, input_identifier, input_lat, input_lon, input_crs=4269, waterbody_type='unknown', water_name=None, buffer_m=1000):
        '''
        Description
        ------------
        Initiates attributes for linking a point to the NHD High Resolution.  First ensure that the buffer
        is less than 2000 meters.  If it is then try converting crs to NAD83.  Then make sure point is within
        United States bounding box.  If any of these fail, create error message and do not run hydrolink.
        
        Parameters
        ------------
        input_identifier: str, user supplied identifier
        input_lat: float, latitude of the point to be hydrolinked
        input_lon: float, longitude of the point to be hydrolinked
        input_crs: int, coordinate reference system, default is 4269 which is NAD83
        waterbody_type: str, choices include 'stream' aka flowlines, 'waterbody' aka polygons, 'unknown' 
        water_name: str, user supplied name of the waterbody a point is intended to be linked, optional
        buffer_m: distance in meters to search around a point, for identifying reaches of interest, max is 2000

        Notes
        ------------
        x,y coordinate in NAD83 (CRS 4269), WGS84 (CRS 4326), (CRS 5070) are tested and recommended
        water_name works best without abbreviations
        larger buffers will take much longer to run, recommended to use the smallest buffer possible 
        '''
        
        self.id = str(input_identifier)
        self.water_name = str(water_name)
        self.buffer_m = int(buffer_m)
        self.status = 1  # where 0 is failed, 1 is worked properly
        self.wb= False   # is point assoicated with waterbody
        self.message = ''
        self.reach_query = None
        self.reach_df = None
        self.best_reach = {
            'input_id': input_identifier, 
            'input_water':str(water_name),
            'water_name_ref': str(water_name).lower(),
            'GNIS_NAME': None,
            'LENGTHKM': None,
            'PERMANENT_IDENTIFIER': None,
            'wb_id': None,
            'wb_gnis_name': None,
            'REACHCODE': None,
            'snap_xy': None,
            'snap_m': None,
            'closest_node_m': None,
            'closest': None,
            'name_check': None,
            'mult_reach_ct': None,
            'name_check_txt': None,
            'hr_meas': None,
            'message': ''
            }
        
        #If buffer is greater than 2000 do not run and set error message
        if buffer_m > 2000:
            self.message = ('Maximum buffer is 2000 meters, reduce buffer to less than 2000 meters.')
            self.error_handling()
            
        #If buffer is less than or equal to 2000 then run 
        else:
            #Try converting to NAD83 (crs==4269) coordinate system if different coordinate system provided
            #If fails do not run and set error message
            try:
                if int(input_crs) == 4269:
                    self.init_lon = float(input_lon)
                    self.init_lat = float(input_lat)
                else:
                    self.init_lon, self.init_lat = utils.crs_to_nad83(float(input_lon), float(input_lat), input_crs)
                
                
                #Test to make sure coordinates are within U.S. including Puerto Rico and Virgian Islands.  
                #This is based on a general bounding box and intended to pick up common issues like missing values, 0 values and positive lon values
                if (float(self.init_lat) > 17.5 and float(self.init_lat) < 71.5) and (float(self.init_lon) < -64.0 and float(self.init_lon)> -178.5):
                    pass
                else:
                    self.message = f'Coordinates for id: {self.id} are outside of the bounding box of the United States.'
                    self.error_handling()
            
            except:
                self.message = f'Issues handling provided coordinate system or coordinates for {self.id}. Consider using a common crs like 4269 (NAD83) or 4326 (WGS84).'
                self.error_handling()
        
    def build_nhd_query(self, service=['hem_flow','hem_waterbody']):
        '''
        Description
        ------------
        Builds query needed to return reaches of interest based on coordinates and buffer supplied by user.
        Currently only HEM service option is supported.
        TNM stands for The National Map
        HEM stands for Hydro Event Managmeent, see documentation https://edits.nationalmap.gov/hem-soe-docs/
        NHD stands for National Hydrography Dataset https://www.usgs.gov/core-science-systems/ngp/national-hydrography
        HRPlus stands for National Hydrography Dataset Plus https://www.usgs.gov/core-science-systems/ngp/national-hydrography/nhdplus-high-resolution
        
        Parameters
        ------------
        service = list of web service queries to build.  current options 'hem_flow','hem_waterbody or both
                  
        Note(s)
        ------------
        HEM: recommended for high resolution. all flowlines are in one mapservice layer.  Provides a recent version of NHD.
        TNM_HR service splits flowlines into in-network and non-network and thus may require multiple service calls
        TNM_HRPlus service uses a snap-shot of NHD. This service also splits flowlines into in-network and non-network and thus may require multiple service calls
        '''
        
        if 'hem_flow' in service:
            q = f"geometryType=esriGeometryPoint&inSR=4269&geometry={self.init_lon},{self.init_lat}&distance={self.buffer_m}&units=esriSRUnit_Meter&outSR=4269&f=JSON&outFields=GNIS_NAME,LENGTHKM,PERMANENT_IDENTIFIER,REACHCODE&returnM=True"
            base_url = 'https://edits.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/1/query?'
            self.reach_query = f"{base_url}{q}"
        
        #hem waterbody returns information about hem waterbodies that the point is within
        if 'hem_waterbody' in service:
            q = f"geometryType=esriGeometryPoint&spatialRel=esriSpatialRelWithin&inSR=4269&geometry={self.init_lon},{self.init_lat}&f=JSON&outFields=PERMANENT_IDENTIFIER,GNIS_NAME,FTYPE&returnGeometry=False"
            base_url = 'https://edits.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/2/query?'
            self.waterbody_query = f"{base_url}{q}"

        #returns reaches associated with a waterbody (e.g. reservoir, lake...)
        if 'hem_waterbody_flow' in service:
            q = f"where=WBAREA_PERMANENT_IDENTIFIER IN (%27{self.best_reach['wb_id']}%27)&outSR=4269&f=JSON&outFields=GNIS_NAME,LENGTHKM,PERMANENT_IDENTIFIER,REACHCODE&returnM=True"
            base_url = 'https://edits.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/1/query?'
            self.reach_query = f"{base_url}{q}"

        #TNM_HR and TNM_HRPlus were included for testing purposes and for potential future efforts
        #if service == 'TNM_HR':
        #    print ('currently these methods are not tuned for the TNM_HR service, it is recommended to use HEM')
        #    base_url = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/5/query?'
        #    self.reach_query = f"{base_url}{q}"
        #    base_url_off_network = 'https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/5/query?'
        #if service == 'TNM_HRPlus':
        #    print ('currently these methods are not tuned for the TNM_HR service, it is recommended to use HEM')
        #    base_url = 'https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/2/query?'
        #    self.reach_query = f"{base_url}{q}"

    def is_in_waterbody(self):
        '''
        Description
        ------------
        Checks to see if point is in a NHD waterbody.  If yes, sets waterbody attribute to permanent identifier value
        
        Parameters
        ------------
        self.waterbody_query is required, see build_reach_query
        '''
        if self.status==1 and self.waterbody_query is not None:  #if status = 0 or if we do not have waterbody query set then skip to avoid wasted processing time
            try:
                results = requests.get(self.waterbody_query).json()
                if len(results['features'])>0:
                    self.wb = True
                    self.best_reach.update({'wb_id':results['features'][0]['attributes']['PERMANENT_IDENTIFIER'],'wb_name': results['features'][0]['attributes']["GNIS_NAME"]})
                    # else:
                    #     self.best_reach.update({'wb_id':-999})
            except:
               self.message = f'is_in_waterbody failed for: {self.id}. possibly service call issue'
               self.error_handling()
        
    def info_on_closest_reaches(self, n=6):
        '''
        Description
        ------------
        Retrieve reaches within buffer distance, buffer_m attribute, of point. Orders results closest to furthest.
        
        Parameters
        ------------
        n = int, number of reaches to return via self.reach_df
        wb = boolean, True queries waterbody specific reaches, False queries based on a buffer   
        '''
        if self.status==1:  #if status = 0 we don't want to waste time processing
            try:
                if self.wb:
                    self.build_nhd_query(service=['hem_waterbody_flow'])
                self.reach_json = requests.get(self.reach_query).json()
                
                if 'features' in self.reach_json.keys() and len(self.reach_json['features'])>0:

                    init_point = Point(self.init_lon, self.init_lat)  

                    reach_data = []
                    for line in self.reach_json['features']:
                        attributes = line['attributes']
                        line_geo = LineString([Point(float(x[0]),float(x[1])) for x in line['geometry']['paths'][0]]) #assumes not multi line

                        #shortest distance from initial coordinates to the line
                        snap_meas = line_geo.project(init_point)
                        snap_xy = line_geo.interpolate(snap_meas) #for reach find x,y on line closest to input x,y
                        snap_point = Point(snap_xy.x, snap_xy.y)
                        snap_m = utils.build_meas_line(snap_point, init_point, crs={'init':'epsg:4269'})
                        
                        # build lines to terminal nodes of reach and measure them
                        meters_to_up_node = None
                        meters_to_dwn_node = None
                        closest_node_m = None
                        for node in line['geometry']['paths'][0]:
                            if node[2]==100:    #upstream confluence or upstream most point on network     
                                max_coord = Point(node[0], node[1])
                                meters_to_up_node = utils.build_meas_line(max_coord, init_point, crs={'init':'epsg:4269'}) #max measure is node at upstream end
                            elif node[2]==0:
                                min_coord = Point(node[0], node[1])
                                meters_to_dwn_node = utils.build_meas_line(min_coord, init_point, crs={'init':'epsg:4269'}) #min measure is node at downstream end
                        if meters_to_dwn_node or meters_to_up_node:   #if one is not none
                            closest_node_m = min(list(filter(None, [meters_to_dwn_node, meters_to_up_node])))

                        #old code looking at range, confluence should (I think always be 0 or 100 measure nodes)
                        # meas_range = [x[2] for x in line['geometry']['paths'][0]]
                        # for node in line['geometry']['paths'][0]:
                        #     max_meas = max(meas_range)
                        #     min_meas = min(meas_range)
                        #     if node[2]==max_meas:
                        #         max_coord = Point(node[0], node[1])
                        #         meters_to_up_node = utils.build_meas_line(max_coord, init_point, crs={'init':'epsg:4269'}) #max measure is node at upstream end
                        #     elif node[2]==min_meas:
                        #         min_coord = Point(node[0], node[1])
                        #         meters_to_dwn_node = utils.build_meas_line(min_coord, init_point, crs={'init':'epsg:4269'}) #min measure is node at downstreaem end
                        
                        #closest_node_m = min(meters_to_dwn_node, meters_to_up_node)  #meters to closest node/confluence of the reach (upstream or downstream)
                        
                        attributes.update({'closest_node_m':closest_node_m, 'snap_m':snap_m, 'snap_xy':snap_xy})
                        reach_data.append(attributes)

                        #keep n number of closest reaches, order them ascendingly and number closest=1 to furthest=n 
                        df = (pd.DataFrame(reach_data)).nsmallest(n,'snap_m',keep='all')
                        df = df.sort_values(by=['snap_m'])
                        df = df.reset_index(drop=True)
                        df['closest'] = df.index +1

                        #df.drop(['geometry','snap_meas'],axis=1)
                        self.reach_df = df
                else:
                    self.message = f'no reaches retrieved for id: {self.id}'
                    self.error_handling()
            except:
                self.message = f'find best reach failed for id: {self.id}. possibly service call issue'
                self.error_handling()
    
    def water_name_match(self):
        '''
        Description: determine if user supplied water name matches nhd supplied gnis name
        Note: It would be ideal to use np.where or alike to assign name_check values to all of the rows 
        at one time but the fuzzy match was not working so current work around using itertuples.  Also
        should be able to delete name_check_text but some users may find this helpful?
        '''
        if self.status==1:  #if status = 0 we don't want to waste time processing
            if self.reach_df is not None and self.water_name is not None:
                df = self.reach_df
                #If GNIS is not null and names match assign a 1
                df['name_check'] = np.where((df.GNIS_NAME.notnull()) & (df.GNIS_NAME.str.lower()==self.water_name.lower()), 1.0, 0)
                for row in df.itertuples():
                    #pid = (row.PERMANENT_IDENTIFIER)
                    if row.name_check == 1:
                        df.at[row.Index, 'name_check_txt'] = 'exact name match'
                        self.best_reach.update({'water_name_ref':self.water_name.lower()})

                    elif row.GNIS_NAME and self.water_name is not None:
                        gnis= (row.GNIS_NAME).lower()
                        #cleaned_water_name = (item.water_name).lower()
                        cleaned_water_name = utils.clean_water_name(self.water_name)
                        self.best_reach.update({'water_name_ref':cleaned_water_name})
                        if 'tributary' not in cleaned_water_name and 'branch' not in cleaned_water_name:
                            match_ratio = difflib.SequenceMatcher(lambda x: x == " ", gnis, cleaned_water_name).ratio()
                            df.at[row.Index, 'name_check'] = match_ratio
                            # If match ratio is greater than 0.75, update df field 'name_check_txt'
                            if match_ratio >= 0.75:
                                df.at[row.Index, 'name_check_txt'] = 'most likely name match based on fuzzy match'
                            # If match ratio is greater than 0.6 and less than 0.6, update df field 'name_check_txt'
                            elif 0.75 > match_ratio >= 0.6:
                                df.at[row.Index, 'name_check_txt'] = 'likely name match based on fuzzy match'               
                        else:
                            df.at[row.Index, 'name_check_txt'] = 'no name match, water name containing reference to tributary'
                            df.at[row.Index, 'name_check'] = 0 
                    else:
                        df.at[row.Index, 'name_check_txt'] = 'no name match, water name and or gnis name not provided'
                        df.at[row.Index, 'name_check'] = 0
            else:
                df['name_check_txt'] = 'no name match, water name not provided'
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
                if 'name_check' in df:
                    name_check_1 = df.loc[df['name_check']==1]

                    if len(name_check_1.index)==1:
                        vals = name_check_1.iloc[0].to_dict()
                        vals.update({'mult_reach_ct': len(name_check_1)})
                        self.best_reach.update(vals)
                    elif len(name_check_1.index)>1:
                        closest = name_check_1.nsmallest(1,'snap_m', keep='all')  #take first indexed reach in list of closest reaches
                        #if multiple reaches have same hl_snap_meters and matching names the count will be recorded in "mult_reach_ct" field
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
                            closest = name_check_lt1.nsmallest(1,'snap_m', keep='all')
                            vals = closest.iloc[0].to_dict()
                            vals.update({'mult_reach_ct':len(closest)})
                            self.best_reach.update(vals)
                        elif len(name_check_lt1.index)==0:
                            closest = df.nsmallest(1,'snap_m', keep='all')
                            vals = closest.iloc[0].to_dict()
                            vals.update({'mult_reach_ct':len(closest)})
                            self.best_reach.update(vals)
                    else:
                        self.message = f'unable to select best reach for id: {self.id}.'
                        self.error_handling()
                else:
                    self.message = f'water match function was not used for {self.id}, using this function will lower the probability of finding best reach match'
                    print (self.message)
                    closest = df.nsmallest(1,'snap_m', keep='all')
                    vals = closest.iloc[0].to_dict()
                    vals.update({'mult_reach_ct':len(closest), 'message':self.message})
                    self.best_reach.update(vals)
                        
            else:
                self.message = f'no dataframe for: {self.id}. make sure functions are called in correct sequence'
                self.error_handling()
        
    def get_hl_measure(self):
        '''
        Description
        ------------
        Use HEM SOE extension HEMPointEvents to pass the snap location on best reach to return reach measure.
        Documentation of HEMPointEvents is found https://edits.nationalmap.gov/hem-soe-docs/soe-reference/hem-point-events.html
        '''
        if self.status == 1:
            if 'REACHCODE' in self.best_reach.keys():
                hem_get_hr_xy = 'https://edits.nationalmap.gov/arcgis/rest/services/HEM/NHDHigh/MapServer/exts/Vwe_HEM_Soe/HEMPointEvents'
                reach = self.best_reach['REACHCODE']
                x = self.best_reach['snap_xy'].x
                y = self.best_reach['snap_xy'].y
                xy = '{"x":' + str(self.init_lon) + ',"y":' + str(self.init_lat) + ', "spatialReference": {"wkid":4269}}'

                payload = {
                        "point": xy ,
                        "reachcode": reach,
                        "searchToleranceMeters": 15,
                        "outWKID": 4269,
                        "f": "json"
                        }

                hr_xy = requests.post(hem_get_hr_xy,params=payload,verify=False).json()
                
                if hr_xy['resultStatus'] == 'success' and hr_xy['features']:
                    self.hl_reach_meas = hr_xy['features'][0]['attributes']
                    meas = hr_xy['features'][0]['attributes']['MEASURE']
                    self.best_reach.update({"hr_meas": meas})
                else:
                    self.message='get_hem_measure failed'
                    self.best_reach.update({"hr_meas": None, 'message': self.message})
            else:
                self.message = f'no reachcode for running measure on id: {self.id}'
                self.best_reach.update(self.no_data)
                message = {'message': self.message}
                self.best_reach.update(message)
        
    
    def error_handling(self):
        '''
        Description
        ------------
        when error is captured, document and send message to user
        '''
        self.status = 0
        #self.best_reach.update(self.no_data)
        message = {'message': self.message}
        self.best_reach.update(message)  
        print (self.message)

    def write_best(self, outfile_name='hr_hydrolink_output.csv'):
        file_exists = os.path.isfile(outfile_name)
        with open(outfile_name, 'a', newline='') as csv_file:
            field_names = self.best_reach.keys()
            writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter=',')
            if not file_exists:
                writer.writeheader()
            writer.writerow(self.best_reach)

    def write_reach_options(self, outfile_name='hr_hydrolink_reach_output.csv'):
        if self.status ==1:
            file_exists = os.path.isfile(outfile_name)
            with open(outfile_name, 'a', newline='') as csv_file:
                for r in self.reach_df.to_dict(orient='records'):
                    r.update({'input_id':self.id})
                    writer = csv.DictWriter(csv_file, r.keys(), delimiter=',')
                    if not file_exists:
                        writer.writeheader()
                        file_exists=True
                    writer.writerow(r) 

def get_ftype(fcode):
    '''
    Description:  Lookup NHD feature type based on fcode
    '''

    #create dictionary with fcode:ftype pairs
    ftypes = {
        '436': 'Reservoir',
        '390': 'LakePond',
        '493': 'Estuary',
        '466': 'SwampMarsh',
        '361': 'Playa',
        '378': 'Ice Mass',
        '566': 'Coastline',
        '334': 'Connector',
        '336': 'CanalDitch',
        '558': 'ArtificialPath',
        '428': 'Pipeline',
        '460': 'StreamRiver',
        '420': 'Underground Conduit'
        }
    ftype = ftypes[str(fcode)]
    return ftype

############################################################################################
############################################################################################