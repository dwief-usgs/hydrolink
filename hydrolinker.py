from hydrolink import nhd_hr
import geopandas as gpd
import pandas as pd 
import warnings; warnings.simplefilter('ignore')
import click


@click.command()
@click.option('--input_file', default='test-data/test.csv', help='Enter file name, including extension (only accepts .csv and .shp)')
@click.option('--latitude_field', default='y', help='Enter field name for latitude, note this is case sensitive')
@click.option('--longitude_field', default='x', help='Enter field name for longitude, note this is case sensitive')
@click.option('--stream_name_field', default='stream', help='Enter field name for stream name, if none type None, note this is case sensitive')
@click.option('--identifier_field', default='id', help='Enter field name for identifier, note this is case sensitive')
@click.option('--crs', default=4269, help='Enter crs number, recommended to use NAD83 represented by 4269')
def get_input( input_file, latitude_field, longitude_field, stream_name_field, identifier_field, crs):
    """
    A program that helps you do things. 
    """
    click.echo('Thank you, processing now...')
    in_data = {"file":input_file,"lat":latitude_field,"lon":longitude_field,"stream_name":stream_name_field,"id":identifier_field}
    return in_data, crs


def import_file(in_data, crs):
    '''
    Description: Imports CSV or SHP files into a Pandas dataframe. Makes sure that all fields 
    are in the file and converts the file into a dataframe with a standard set of field names.
    
    Input
    ------------
    in_data: dictionary with values for file, lat, lon, stream_name, id
    
    Output
    ------------
    Pandas Dataframe
    '''
    #Check to see if the file is a CSV file
    if in_data['file'].endswith('.csv'):
        print ('reading csv file' +'\n')
        try:
            df = pd.read_csv(in_data['file'],encoding='iso-8859-1')
        except KeyError:
            print ('file did not properly import, verify file name and rerun')
            #It would be nice here to reask for inputFileName and then restart at try statement
    
    #If input file is not a CSV check to see if it is a shapefile
    elif in_data['file'].endswith('.shp'):
        print('\n' + 'reading shapefile' + '\n')
        try:
            df = gpd.GeoDataFrame.from_file(in_data['file'])
        except KeyError:
            print ('file did not properly import, verify file name and rerun')
            #It would be nice here to reask for inputFileName and then restart at try statement
    
    #If input file is not a CSV or shapefile tell the user that the file type is not excepted
    else:
        print('File type not currently accepted. Please try .csv or .shp')
    
    

    if in_data['lat'] in df and in_data['lon'] in df and in_data['id'] in df:
        if in_data['stream_name'] is not None and in_data['stream_name'] in df:
            df = df[[in_data['id'], in_data['lat'], in_data['lon'], in_data['stream_name']]].copy()
            df = df.rename(columns={in_data['id']: 'id', in_data['lat']: 'lat', in_data['lon']: 'lon', in_data['stream_name']: 'stream' })
            df['crs'] = int(crs)
            return df
        else:
            df = df[[in_data['id'], in_data['lat'], in_data['lon']]].copy()
            df = df.rename(columns={in_data['id']: 'id', in_data['lat']: 'lat', in_data['lon']: 'lon'})
            df['stream'] = None
            df['crs'] = int(crs)
            return df
    else: 
        print ('verify field names and rerun')


if __name__ == '__main__':

    #input_data, crs = get_user_input()
    input_data, crs = get_input()

    df = import_file(input_data, crs)

    for row in df.itertuples():
        
        #initiate a Python object
        hydrolink = nhd_hr.HighResPoint(row.id, float(row.lat), float(row.lon), water_name=str(row.stream), input_crs=int(row.crs))

        #builds query against USGS hem web services
        hydrolink.build_nhd_query(service='hem_flow')

        #executes query and measures distances from point to each line and their nodes
        hydrolink.get_closest_reaches(n=3)

        #stream name match for each of the reaches
        hydrolink.water_name_match()
    
        #Return reach most likely associated with point
        hydrolink.select_best_reach()

        #get address of hydrolinked point
        hydrolink.get_hl_measure()

        #Creates a CSV file of all reach options.  This can be used for QAQC procedures.
        #hydrolink.write_reach_options(outfile_name='test-data/test_hr_hydrolink_reach_output.csv')

        #Creates a CSV file with one reach per point.
        in_file = input_data['file']  
        output_file = f'{in_file}_output.csv'
        hydrolink.write_best(outfile_name= output_file)
