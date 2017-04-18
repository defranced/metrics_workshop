'''
make_big_anomaly
'''

import glob
import iris
import numpy as np
from iris.experimental.equalise_cubes import equalise_attributes

def main(bigcube,file_searcher,sc):
    
    filehistorical = file_searcher.replace(str(sc),'historical')
    file_historical = glob.glob(filehistorical+'*_all_models.nc')
    cubelist = iris.cube.CubeList([])
    cubehist = iris.load_cube(file_historical)
    yearslicehist = iris.Constraint(year = lambda cell: 1950 <= cell <= 1999)
    yearslicefuture = iris.Constraint(year = lambda cell: 2050 <= cell <= 2099)
    cubehist = cubehist.extract(yearslicehist)
    cubefuture = bigcube.extract(yearslicefuture)
    cubehist = cubehist.collapsed('year', iris.analysis.MEDIAN)
    cubefuture = cubefuture.collapsed('year',iris.analysis.MEDIAN)
    anom = cubefuture.copy()
    mdls = anom.coord('model_name').points
    mdls = np.ndarray.tolist(mdls)
    for mdl in mdls:
	fi = mdls.index(mdl)
        mdlextract = iris.Constraint(model_name = lambda cell: cell == mdl)
	smllcubefuture = cubefuture.extract(mdlextract)
	smllcubepast = cubehist.extract(mdlextract)
    	differences = smllcubefuture - smllcubepast
        cubelist.append(differences)
#        anom[fi,:,:].data = differences[:,:].data
#	print np.percentile(anom[fi,:,:].data,50)

    anom = cubelist.merge_cube()
    print np.percentile(anom[fi,:,:].data,50)
    	
    iris.save(anom, file_searcher+'_anomalies.nc') 
    return (anom)
    
if __name__ == "__main__":
    outpath = '/nfs/a266/earv061'
    main(file_searcher)    
