"""
Package to create all Netcdf files necessary for metric atlas plotting. Reads CMIP5 original data and writes
metric files for single models (*_single_model.nc) and the big model cube (*_all_models.nc).

* NetCDF files of single model / multi-model cubes are saved as 2D cubes (lat,lon) and time series (1D)  cubes



Input: strings defining the input netcdf files
Output: netcdf files for single models, big model cube and anomalies 
"""

import utils
import iris
import itertools
import os
import glob
import numpy as np
import calc
import constants as cnst
import sys
from iris.experimental.equalise_cubes import equalise_attributes
#import pdb


def load_file_names(inpath, variable, scenario, bc_and_resolution):
    """
    Returns the path to CMIP5 files and model names
    """

    filepath = inpath + '/' + str(bc_and_resolution) + '/*/' + str(scenario) + '/' + str(variable) + '*.nc'
#    print filepath
    files_good = glob.glob(filepath)

    modelID = [f.split(os.sep)[-3] for f in files_good]

    return (files_good, modelID)



def model_files(variable, scenario, bc_and_resolution, inpath, outpath, season, metric, region, overwrite):
    """
    Computes respective metric and returns single model files and multi-model cube at different aggregations
    """

    for sc, bc, seas, var, reg in itertools.product(scenario, bc_and_resolution, season, variable, region):

        box = reg[2]
        xmin = box[0]
        xmax = box[1]
        ymin = box[2]
        ymax = box[3]

        files_good, modelID = load_file_names(inpath, var, sc, bc)

        if files_good == []:
            print inpath, sc, bc, seas, var
            sys.exit('No files found. Check your input directory!!!')

        out = outpath + os.sep + bc

        calc_to_call = getattr(calc, metric) # calls the metric calc function from calc.py
        file_searcher = out + os.sep + str(metric) + '_' +str(var) + '_' + str(bc) + \
                        '_' + str(sc) + '_' + str(seas) +'_' + str(reg[0])
        
        for file, nme in zip(files_good, modelID):
            
            # Check if we have any missing files for all aggregation types, if so, run the metric calculation again
            # Note: the calc functions run for 2 or 3 aggregation methods
            for agg in cnst.METRIC_AGGS[metric]:
                print agg
                
                nc_file = file_searcher + '_' + str(nme) + '_singleModel_'+agg+'.nc'
                print 'nc_file: ' + nc_file
                
                if not os.path.isfile(nc_file) or (overwrite == 'Yes'):
                    cubeout = utils.load_data(file, xmin, xmax, ymin, ymax)
                    calc_to_call(cubeout, seas, nc_file)  # saves single model netcdf
                
                big_cube(file_searcher, agg)
                
            


def big_cube(file_searcher, aggregation):
    """
    Reads single model files and creates multi model cubes for time series and 2d cubes
    """
    print file_searcher, aggregation
    
    if aggregation not in cnst.AGGREGATION:
        sys.exit('Data aggregation does not exist, choose either trend, tseries or 2d')
        
    list_of_files = glob.glob(file_searcher + '*_singleModel_' + aggregation + '.nc')

    model_names = [f.split('/')[-1].split('_')[-3].split('.')[0] for f in list_of_files]
    cubelist = iris.cube.CubeList([])

    for file in list_of_files:
#        print file
        fi = list_of_files.index(file)
        mod_coord = iris.coords.AuxCoord([model_names[fi]], long_name='model_name', var_name='model_name', units='1')

        cube = iris.load_cube(file)
        cube.data = np.ma.masked_invalid(cube.data)

        if fi == 0:
            template = cube.copy()
            cube.add_aux_coord(mod_coord, data_dims=None)
            cubelist.append(cube)
        else:
            newcube = template.copy()
            newcube.add_aux_coord(mod_coord, data_dims=None)
            newcube.data = cube.data
            cubelist.append(newcube)

#    print cubelist
#    pdb.set_trace()
    if not cubelist:
        print "No cubes found"
    else:
        equalise_attributes(cubelist)
        bigcube = cubelist.merge_cube()
        iris.save(bigcube, str(file_searcher) + '_allModels_' + aggregation + '.nc')


def run(variable, bc_and_resolution, inpath, outpath, season, metric, region, overwrite,):

    """
    Calls the functions to write single model, multi-model and anomaly NetCDF files.
    Just a shortcut for calling them seperately.

    :param variable: string list of chosen variables: e.g. ['pr', 'tasmax']
    :param bc_and_resolution: string list of chosen correction option: e.g. ['BC_0.5x0.5' , '0.5x0.5']
    :param inpath: path to CMIP5 Africa directory: '/my/path/CMIP5_Africa'
    :param outpath: path where intermediate NetCDF files should be saved (single / multi-model / anomalies)
    :param season: string list months for which the metric is to be computed: ['jas', 'ann']
    :param metric: STRING identifing a metric (the calculation file), no list: 'annualMax'
    :param overwrite: whether or not existing NetCDF files should be overwritten
    :return: NetCDF files
    """

    # write all single model and big_cube files - make sure all scenarios are written to calculate anomalies!
    model_files(variable, cnst.SCENARIO, bc_and_resolution, inpath, outpath, season, metric, region, overwrite)
