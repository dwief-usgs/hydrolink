"""Command line tool for HydroLinking data.

Authors
----------
Name: Daniel Wieferich
Contact: dwieferich@usgs.gov

Name: Brandon Serna
Contact: bserna@usgs.gov

"""
import click
from hydrolink import nhd_hr
from hydrolink import nhd_mr
import geopandas as gpd
import pandas as pd
import warnings
warnings.simplefilter('ignore')


@click.command()
@click.option('--input_file', required=True, help='Enter file name, including extension (only accepts .csv and .shp)')
@click.option('--latitude_field', required=True, show_default=True, default='y', help='Enter field name for latitude, note this is case sensitive')
@click.option('--longitude_field', required=True, show_default=True, default='x', help='Enter field name for longitude, note this is case sensitive')
@click.option('--stream_name_field', required=True, show_default=True, default='stream', help='Enter field name for stream name, if none type None, note this is case sensitive')
@click.option('--identifier_field', required=True, show_default=True, default='id', help='Enter field name for identifier, note this is case sensitive')
@click.option('--crs', required=True, show_default=True, default=4269, help='Enter crs number, recommended to use NAD83 represented by 4269')
@click.option('--buffer', required=True, show_default=True, default=1000, help='Enter buffer distance in meters, max is 2000')
@click.option('--method', required=True, show_default=True, default='name_match', help='Enter method to use, options include name_match and closest')
@click.option('--nhd_version', required=True, show_default=True, default='nhdhr', help='Version of NHD to use, options include nhdhr and nhdplusv2')
@click.option('--hydro_type', required=True, show_default=True, default='flowline', help='Options flowline or waterbody')
def handle_data(input_file, latitude_field, longitude_field, stream_name_field, identifier_field, crs, buffer, method, nhd_version, hydro_type):
    """Hydrolink point data to the nhd high resolution.

    HydroLinker accepts a CSV file of multiple points of interest, HydroLinks each to
    the specified version of NHD and writes HydroLink data (addresses to NHD) along with
    measures of certainty to a csv file.

    """
    click.echo('Thank you, processing now...')

    in_data = {"file": input_file,
               "lat": latitude_field,
               "lon": longitude_field,
               "stream_name": stream_name_field,
               "id": identifier_field}

    if in_data['file'].endswith('.csv'):
        click.echo('reading csv file')
        try:
            df = pd.read_csv(in_data['file'], encoding='iso-8859-1')
        except KeyError:
            click.echo('csv file did not properly import, verify file name and rerun')

    # If input file is not a CSV check to see if it is a shapefile
    elif in_data['file'].endswith('.shp'):
        click.echo('reading shapefile')
        try:
            df = gpd.GeoDataFrame.from_file(in_data['file'])
        except KeyError:
            click.echo('shapefile did not properly import, verify file name and rerun')

    # If input file is not a CSV or shapefile tell the user that the file type is not excepted
    else:
        click.echo('File type not currently accepted. Please try .csv or .shp')

    if in_data['lat'] in df and in_data['lon'] in df and in_data['id'] in df and in_data['stream_name'] in df:
        df = df.rename(columns={in_data['id']: 'id',
                                in_data['lat']: 'lat',
                                in_data['lon']: 'lon',
                                in_data['stream_name']: 'stream'
                                })
        df['crs'] = int(crs)

    else:
        click.echo('Verify field names and rerun')

    for row in df.itertuples():
        if nhd_version == 'nhdhr':
            hydrolink = nhd_hr.HighResPoint(row.id, float(row.lat), float(row.lon), input_crs=int(row.crs), water_name=str(row.stream), buffer_m=buffer)
        elif nhd_version == 'nhdplusv2':
            hydrolink = nhd_mr.HighResPoint(row.id, float(row.lat), float(row.lon), input_crs=int(row.crs), water_name=str(row.stream), buffer_m=buffer)
        hydrolink.hydrolink_method(method=method, hydro_type=hydro_type)

        # in_file = in_data['file'][:-4]  #remove .csv or .shp
        # output_file = f'{in_file}_output.csv'
        # hydrolink.write_best(outfile_name= output_file)

    # click.echo('Output exported to %s' % output_file)


if __name__ == '__main__':
    handle_data()
