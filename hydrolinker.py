from hydrolink import nhd_hr
import geopandas as gpd
import pandas as pd 
import warnings; warnings.simplefilter('ignore')
import click


@click.command()
@click.option('--input_file', required=True, show_default=True,  default='test-data/test.csv', help='Enter file name, including extension (only accepts .csv and .shp)')
@click.option('--latitude_field', required=True, show_default=True, default='y', help='Enter field name for latitude, note this is case sensitive')
@click.option('--longitude_field', required=True, show_default=True, default='x', help='Enter field name for longitude, note this is case sensitive')
@click.option('--stream_name_field', required=True, show_default=True, default='stream', help='Enter field name for stream name, if none type None, note this is case sensitive')
@click.option('--identifier_field', required=True, show_default=True, default='id', help='Enter field name for identifier, note this is case sensitive')
@click.option('--crs', required=True, show_default=True, default=4269, help='Enter crs number, recommended to use NAD83 represented by 4269')
def handle_data(input_file, latitude_field, longitude_field, stream_name_field, identifier_field, crs):
    """
    description
    ----------
    a program to hydrolink point data to the nhd high resolution. 
    
    examples
    ----------
    
    python hydrolinker.py -> runs with defaults

    python hydrolinker.py --input_file=file_name.csv  -> runs with specified file name and default other values

    output
    ---------- 
    writes hydrolinked (hydro addressed information to csv file)
    """

    click.echo('Thank you, processing now...')

    in_data = {"file":input_file,"lat":latitude_field,"lon":longitude_field,"stream_name":stream_name_field,"id":identifier_field}

    if in_data['file'].endswith('.csv'):
        click.echo('reading csv file')
        try:
            df = pd.read_csv(in_data['file'],encoding='iso-8859-1')
        except KeyError:
            click.echo('csv file did not properly import, verify file name and rerun')

    #If input file is not a CSV check to see if it is a shapefile
    elif in_data['file'].endswith('.shp'):
        click.echo('reading shapefile')
        try:
            df = gpd.GeoDataFrame.from_file(in_data['file'])
        except KeyError:
            click.echo('shapefile did not properly import, verify file name and rerun')

    #If input file is not a CSV or shapefile tell the user that the file type is not excepted
    else:
       click.echo('File type not currently accepted. Please try .csv or .shp')


    if in_data['lat'] in df and in_data['lon'] in df and in_data['id'] in df and in_data['stream_name'] in df:
        df = df.rename(columns={in_data['id']: 'id', in_data['lat']: 'lat', in_data['lon']: 'lon', in_data['stream_name']: 'stream' })
        df['crs'] = int(crs)

    # if in_data['lat'] in df and in_data['lon'] in df and in_data['id'] in df:
    #     if in_data['stream_name'] is not None and in_data['stream_name'] in df:
    #         df = df[[in_data['id'], in_data['lat'], in_data['lon'], in_data['stream_name']]].copy()
    #         df = df.rename(columns={in_data['id']: 'id', in_data['lat']: 'lat', in_data['lon']: 'lon', in_data['stream_name']: 'stream' })
    #         df['crs'] = int(crs)

    #     else:
    #         df = df[[in_data['id'], in_data['lat'], in_data['lon']]].copy()
    #         df = df.rename(columns={in_data['id']: 'id', in_data['lat']: 'lat', in_data['lon']: 'lon'})
    #         df['stream'] = None
            

    else: 
        click.echo('verify field names and rerun')


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
        in_file = in_data['file'][:-4]  #remove .csv or .shp
        output_file = f'{in_file}_output.csv'
        hydrolink.write_best(outfile_name= output_file)
    
    click.echo('Output exported to %s' % output_file)


if __name__ == '__main__':
    handle_data()