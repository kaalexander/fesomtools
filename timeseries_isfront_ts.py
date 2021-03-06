from netCDF4 import Dataset
from numpy import *
from matplotlib.pyplot import *
from os.path import *
from fesom_grid import *

# Plot timeseries of the annually-averaged, volume-averaged temperature and
# salinity at the ice shelf front (all depths) for each major ice shelf.
# Input:
# mesh_path = path to FESOM mesh directory
# output_path = path to FESOM experiment directory containing all oce.mean.nc
#               files (one for each year)
# start_year, end_year = integers containing range of years to process
# fig_dir = path to directory to save the figures in
def timeseries_isfront_ts (mesh_path, output_path, start_year, end_year, fig_dir=''):

    # Titles and figure names for each ice shelf
    names = ['All Ice Shelf Fronts', 'Larsen D Ice Shelf Front', 'Larsen C Ice Shelf Front', 'Wilkins & George VI & Stange Ice Shelf Front', 'Ronne-Filchner Ice Shelf Front', 'Abbot Ice Shelf Front', 'Pine Island Glacier Ice Shelf Front', 'Thwaites Ice Shelf Front', 'Dotson Ice Shelf Front', 'Getz Ice Shelf Front', 'Nickerson Ice Shelf Front', 'Sulzberger Ice Shelf Front', 'Mertz Ice Shelf Front', 'Totten & Moscow University Ice Shelf Front', 'Shackleton Ice Shelf Front', 'West Ice Shelf Front', 'Amery Ice Shelf Front', 'Prince Harald Ice Shelf Front', 'Baudouin & Borchgrevink Ice Shelf Front', 'Lazarev Ice Shelf Front', 'Nivl Ice Shelf Front', 'Fimbul & Jelbart & Ekstrom Ice Shelf Front', 'Brunt & Riiser-Larsen Ice Shelf Front', 'Ross Ice Shelf Front']
    fig_names = ['front_ts.png', 'larsen_d_front_ts.png', 'larsen_c_front_ts.png', 'wilkins_georgevi_stange_front_ts.png', 'ronne_filchner_front_ts.png', 'abbot_front_ts.png', 'pig_front_ts.png', 'thwaites_front_ts.png', 'dotson_front_ts.png', 'getz_front_ts.png', 'nickerson_front_ts.png', 'sulzberger_front_ts.png', 'mertz_front_ts.png', 'totten_moscowuni_front_ts.png', 'shackleton_front_ts.png', 'west_front_ts.png', 'amery_front_ts.png', 'princeharald_front_ts.png', 'baudouin_borchgrevink_front_ts.png', 'lazarev_front_ts.png', 'nivl_front_ts.png', 'fimbul_jelbart_ekstrom_front_ts.png', 'brunt_riiserlarsen_front_ts.png', 'ross_front_ts.png']
    # Limits on longitude and latitude for each ice shelf
    # These depend on the source geometry, in this case RTopo 1.05
    # Note there is one extra index at the end of each array; this is because
    # the Ross region crosses the line 180W and therefore is split into two
    # We have -181 and 181 not -180 and 180 at this boundary so that
    # elements which cross the boundary are still counted
    lon_min = [-181, -62.67, -65.5, -79.17, -85, -104.17, -102.5, -108.33, -114.5, -135.67, -149.17, -155, 144, 115, 94.17, 80.83, 65, 33.83, 19, 12.9, 9.33, -10.05, -28.33, -181, 158.33]
    lon_max = [181, -59.33, -60, -66.67, -28.33, -88.83, -99.17, -103.33, -111.5, -114.33, -140, -145, 146.62, 123.33, 102.5, 89.17, 75, 37.67, 33.33, 16.17, 12.88, 7.6, -10.33, -146.67, 181]
    lat_min = [-90, -73.03, -69.35, -74.17, -83.5, -73.28, -75.5, -75.5, -75.33, -74.9, -76.42, -78, -67.83, -67.17, -66.67, -67.83, -73.67, -69.83, -71.67, -70.5, -70.75, -71.83, -76.33, -85, -84.5]
    lat_max = [-30, -69.37, -66.13, -69.5, -74.67, -71.67, -74.17, -74.67, -73.67, -73, -75.17, -76.41, -66.67, -66.5, -64.83, -66.17, -68.33, -68.67, -68.33, -69.33, -69.83, -69.33, -71.5, -77.77, -77]

    circumpolar = True   # Only consider elements south of 30S
    cross_180 = False    # Don't make second copies of elements that cross 180E
    # Naming conventions for FESOM output files
    file_head = output_path + 'MK44005.'
    file_tail = '.oce.mean.nc'
    num_years = end_year - start_year + 1

    print 'Building grid'
    elements = fesom_grid(mesh_path, circumpolar, cross_180)

    print 'Setting up arrays'
    # Timeseries of temperature and salinity to plot
    front_temp_ts = empty([len(names), num_years])
    front_salt_ts = empty([len(names), num_years])
    # Temporary arrays containing integrated temperature, salinity, and volume
    # for each ice shelf front. Will be overwritten every year.
    front_temp_int = empty(len(names))
    front_salt_int = empty(len(names))
    front_volume_int = empty(len(names))

    # Loop over years
    for year in range(start_year, end_year+1):
        print 'Processing year ' + str(year)
        # Initialise integrals
        front_temp_int[:] = 0.0
        front_salt_int[:] = 0.0
        front_volume_int[:] = 0.0
        # Read temperature and salinity for this year, annually average
        id = Dataset(file_head + str(year) + file_tail, 'r')
        temp = mean(id.variables['temp'][:,:], axis=0)
        salt = mean(id.variables['salt'][:,:], axis=0)
        id.close()
        # Loop over elements
        for elm in elements:
            # Select elements where some of the 3 nodes are in a cavity, some
            # aren't: this is the ice shelf front
            if count_nonzero(elm.cavity_nodes) in [1,2]:
                # Loop over ice shelves
                for index in range(len(names)):
                    keep = False
                    # Check if within lat/lon bounds for this ice shelf
                    if all(elm.lon >= lon_min[index]) and all(elm.lon <= lon_max[index]) and all(elm.lat >= lat_min[index]) and all(elm.lat <= lat_max[index]):
                        keep = True
                    # Ross region is split into 2
                    if index == len(names)-1:
                        if all(elm.lon >= lon_min[index+1]) and all(elm.lon <= lon_max[index+1]) and all(elm.lat >= lat_min[index+1]) and all(elm.lat <= lat_max[index+1]):
                            keep = True
                    if keep:
                        # Get area of 2D element
                        area = elm.area()
                        nodes = [elm.nodes[0], elm.nodes[1], elm.nodes[2]]
                        # Loop downward
                        while True:
                            if nodes[0].below is None or nodes[1].below is None or nodes[2].below is None:
                                # Reached the bottom
                                break
                            # Calculate average temperature, salinity, and
                            # layer thickness for this 3D triangular prism
                            temp_vals = []
                            salt_vals = []
                            dz_vals = []
                            for i in range(3):
                                temp_vals.append(temp[nodes[i].id])
                                salt_vals.append(salt[nodes[i].id])
                                temp_vals.append(temp[nodes[i].below.id])
                                salt_vals.append(salt[nodes[i].below.id])
                                dz_vals.append(abs(nodes[i].depth - nodes[i].below.depth))
                                # Get ready for next iteration of loop
                                nodes[i] = nodes[i].below
                            # Calculate volume
                            volume = area*mean(array(dz_vals))
                            # Integrate temperature, salinity, volume for this
                            # cavity
                            front_temp_int[index] += mean(array(temp_vals))*volume
                            front_salt_int[index] += mean(array(salt_vals))*volume
                            front_volume_int[index] += volume
        # Convert temperature and salinity from integrals to volume-averages,
        # add to timeseries
        front_temp_ts[:,year-start_year] = front_temp_int/front_volume_int
        front_salt_ts[:,year-start_year] = front_salt_int/front_volume_int

    # Make time axis
    time = range(start_year, end_year+1)

    print 'Plotting'
    # One plot for each ice shelf
    for index in range(len(names)):
        fig, ax1 = subplots()
        # Temperature
        ax1.plot(time, front_temp_ts[index,:], color='b')
        ax1.set_ylabel(r'Average temperature ($^{\circ}$C)', color='b')
        for t1 in ax1.get_yticklabels():
            t1.set_color('b')
        ax1.set_xlabel('Years')
        ax1.grid(True, axis='x')
        ax2 = ax1.twinx()
        # Salinity
        ax2.plot(time, front_salt_ts[index,:], color='r')
        ax2.set_ylabel('Average salinity (psu)', color='r')
        for t2 in ax2.get_yticklabels():
            t2.set_color('r')
        title(names[index])
        fig.savefig(fig_dir + fig_names[index])


# Command-line interface
if __name__ == "__main__":

    mesh_path = raw_input("Path to FESOM mesh directory: ")
    output_path = raw_input("Path to FESOM output directory: ")
    start_year = int(raw_input("First year to process: "))
    end_year = int(raw_input("Last year to process: "))
    timeseries_isfront_ts(mesh_path, output_path, start_year, end_year)
    
    
                    
