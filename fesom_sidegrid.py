from numpy import *
from netCDF4 import Dataset
from triangle_area_latdepth import *

# Classes and routines to extract a zonal slice (depth vs latitude) of the
# FESOM grid


# SideNode object containing longitude, latitude, depth, value of variable
# (chosen earlier by the user), and the node directly below it (if there is one)
# These SideNodes are interpolated between the original grid Nodes and represent
# the intersections of the original grid Elements with the specified longitude.
class SideNode:

    # Initialise with location and variable data
    def __init__ (self, lon, lat, depth, var):

        self.lon = lon
        self.lat = lat
        self.depth = depth
        self.var = var
        self.below = None

    # Save the node directly below the current node
    def set_below (self, snode_below):

        self.below = snode_below


# SideNodePair object containing two SideNodes which will later be used for
# the boundaries of SideElements.
class SideNodePair:

    # Initialise with two SideNodes
    def __init__ (self, snode1, snode2):

        # Figure out which is further south
        if snode1.lat < snode2.lat:
            self.south = snode1
            self.north = snode2
        else:
            self.south = snode2
            self.north = snode1


# SideElement object containing the four SideNodes making up the quadrilateral
# element (intersection of an original grid Element, and its 3D extension down
# through the water column, with the user-defined zonal slice).
class SideElement:

    # Initialise with four nodes (assumed to trace continuously around the
    # border of the SideElement, i.e. not jump between diagonal corners)
    def __init__ (self, snode1, snode2, snode3, snode4):

        self.snodes = array([snode1, snode2, snode3, snode4])
        lat = array([snode1.lat, snode2.lat, snode3.lat, snode4.lat])
        depth = array([snode1.depth, snode2.depth, snode3.depth, snode4.depth])
        self.y = lat
        # Make depth negative
        self.z = -depth
        # Set the value of the user-defined variable to be the mean of the
        # values at each corner (not quite mathematically correct but this
        # is just a visualisation, and much easier than integrating around a
        # quadrilateral!!)
        self.var = (snode1.var + snode2.var + snode3.var + snode4.var)/4.0

    # Return the area of the quadrilateral making up this Element
    def area (self):

        # Divide into two triangles and add the areas
        lat1 = array([self.y[0], self.y[1], self.y[2]])
        depth1 = array([self.z[0], self.z[1], self.z[2]])
        area1 = triangle_area_latdepth(lat1, depth1)
        
        lat2 = array([self.y[0], self.y[2], self.y[3]])
        depth2 = array([self.z[0], self.z[2], self.z[3]])
        area2 = triangle_area_latdepth(lat2, depth2)

        return area1 + area2        


# Function to build SideElement mesh
# Input:
# elm2D = elements from regular FESOM grid
# data = FESOM output at each node; can be a single time index or a timeseries
# lon0 = longitude to use for zonal slice
# lat_max = northernmost latitude to plot (generally -50, depends on your
#           definition of the Southern Ocean)
# lat_min = optional southernmost latitude to plot
# Output:
# selements = array of SideElements making up the zonal slice
def fesom_sidegrid (elm2D, data, lon0, lat_max, lat_min=-90):

    snode_pairs = []
    for elm in elm2D:
        # Don't consider elements outside the given latitude bounds
        if any(elm.lat >= lat_min) and any(elm.lat <= lat_max):
            # Select elements which intersect lon0
            if any(elm.lon <= lon0) and any(elm.lon >= lon0):
                # Special cases where nodes (corners) of the element are exactly
                # at longitude lon0
                if count_nonzero(elm.lon == lon0) == 1:
                    # If exactly one of the corners is at lon0, check if the opposite side of
                    # the triangle intersects lon0
                    if elm.lon[0] == lon0 and any(array([elm.lon[1], elm.lon[2]]) < lon0) and any(array([elm.lon[1], elm.lon[2]]) > lon0):                        
                        # Get one SideNode directly from the node at lon0, and interpolate
                        # another SideNode on the line between the other 2 nodes
                        snode_pairs.append(SideNodePair(single_coincide_snode(elm.nodes[0], data), interp_snode(elm.nodes[1], elm.nodes[2], lon0, data)))
                    elif elm.lon[1] == lon0 and any(array([elm.lon[0], elm.lon[2]]) < lon0) and any(array([elm.lon[0], elm.lon[2]]) > lon0):
                        snode_pairs.append(SideNodePair(single_coincide_snode(elm.nodes[1], data), interp_snode(elm.nodes[0], elm.nodes[2], lon0, data)))
                    elif elm.lon[2] == lon0 and any(array([elm.lon[0], elm.lon[1]]) < lon0) and any(array([elm.lon[0], elm.lon[1]]) > lon0):
                        snode_pairs.append(SideNodePair(single_coincide_snode(elm.nodes[2], data), interp_snode(elm.nodes[0], elm.nodes[1], lon0, data)))
                    else:
                        # The element skims across lon0 at exactly one point. Ignore it, because
                        # that point will be dealt within inside another element.
                        pass
                if count_nonzero(elm.lon == lon0) == 2:
                    # If two of the corners are at lon0, an entire side of the
                    # element lies along the line lon0
                    # Select these two Nodes
                    index = nonzero(elm.lon == lon0)
                    nodes = elm.nodes[index]
                    node1 = nodes[0]
                    node2 = nodes[1]
                    # Convert to SideNodes and add them to snode_pairs
                    double_coincide_snode(node1, node2, data, snode_pairs)
                # Impossible for all three corners to be at lon0
                else:
                    # Regular case
                    snodes_curr = []
                    # Find the two sides of the triangular element which
                    # intersect longitude lon0
                    # For each such side, interpolate a SideNode between the
                    # two endpoint Nodes.
                    if any(array([elm.lon[0], elm.lon[1]]) < lon0) and any(array([elm.lon[0], elm.lon[1]]) > lon0):
                        snodes_curr.append(interp_snode(elm.nodes[0], elm.nodes[1], lon0, data))
                    if any(array([elm.lon[1], elm.lon[2]]) < lon0) and any(array([elm.lon[1], elm.lon[2]]) > lon0):
                        snodes_curr.append(interp_snode(elm.nodes[1], elm.nodes[2], lon0, data))
                    if any(array([elm.lon[0], elm.lon[2]]) < lon0) and any(array([elm.lon[0], elm.lon[2]]) > lon0):
                        snodes_curr.append(interp_snode(elm.nodes[0], elm.nodes[2], lon0, data))
                    # Add the two resulting SideNodes to snode_pairs
                    snode_pairs.append(SideNodePair(snodes_curr[0], snodes_curr[1]))

    selements = []
    # Build the quadrilateral SideElements
    for pair in snode_pairs:
        # Start at the surface
        snode1_top = pair.south
        snode2_top = pair.north
        while True:
            # Select the SideNodes directly below
            snode1_bottom = snode1_top.below
            snode2_bottom = snode2_top.below
            if snode1_bottom is None or snode2_bottom is None:
                # Reached the bottom, so stop
                break
            # Make a SideElement from these four SideNodes
            # The order they are passed to the SideElement initialisation
            # function is important: must trace continuously around the
            # border of the SideElement, i.e. not jump between diagonal corners
            selements.append(SideElement(snode1_top, snode2_top, snode2_bottom, snode1_bottom))
            # Get ready for the next SideElement below
            snode1_top = snode1_bottom
            snode2_top = snode2_bottom

    return selements


# Process the special case where a single node lies on the line longitude=lon0 (and the opposite
# edge of the triangle intersects lon0, so we care). Convert this node to a SideNode.
# Input:
# node = Node at lon0
# data = FESOM output at each node; can be a single time index or a timeseries
# Output:
# snode_sfc = SideNode object for the intersection at the surface, with all
#             SideNodes beneath it also interpolated and linked in
def single_coincide_snode(node, data):

    if len(data.shape) == 2:
        # Timeseries
        snode_sfc = SideNode(node.lon, node.lat, node.depth, data[:,node.id])
    else:
        # Single time index
        snode_sfc = SideNode(node.lon, node.lat, node.depth, data[node.id])
    # Travel down the water column to similarly process the node at each depth level
    snode = snode_sfc
    while True:
        # Find the node directly below
        node = node.below
        if node is None:
            # We've reached the bottom; stop
            break
        # Convert to SideNode
        if len(data.shape) == 2:
            # Timeseries
            snode_below = SideNode(node.lon, node.lat, node.depth, data[:,node.id])
        else:
            # Single time index
            snode_below = SideNode(node.lon, node.lat, node.depth, data[node.id])
        # Save to linked list
        snode.set_below(snode_below)
        # Get ready for next iteration
        snode = snode_below


# Process the special case where an entire side of a triangular Element lies
# on the line longitude=lon0. Convert the endpoint Nodes to SideNodes, and add
# to the snode_pairs list.
# Input:
# node1, node2 = endpoint Nodes from this Element
# data = FESOM output at each node; can be a single time index or a timeseries
# snode_pairs = list of SideNodePair objects to add to
def double_coincide_snode (node1, node2, data, snode_pairs):

    # Convert the Nodes into SideNodes
    if len(data.shape) == 2:
        # Timeseries
        snode1 = SideNode(node1.lon, node1.lat, node1.depth, data[:,node1.id])
        snode2 = SideNode(node2.lon, node2.lat, node2.depth, data[:,node2.id])
    else:
        # Single time index
        snode1 = SideNode(node1.lon, node1.lat, node1.depth, data[node1.id])
        snode2 = SideNode(node2.lon, node2.lat, node2.depth, data[node2.id])
    # Save to SideNodePair list
    snode_pairs.append(SideNodePair(snode1, snode2))

    # Travel down the water column to similarly process the Nodes at each
    # depth level
    while True:
        # Find the Nodes directly below
        node1 = node1.below
        node2 = node2.below
        if node1 is None or node2 is None:
            # We've reached the bottom; stop
            break
        # Convert these to SideNodes
        if len(data.shape) == 2:
            # Timeseries
            snode1_below = SideNode(node1.lon, node1.lat, node1.depth, data[:,node1.id])
            snode2_below = SideNode(node2.lon, node2.lat, node2.depth, data[:,node2.id])
        else:
            # Single time index
            snode1_below = SideNode(node1.lon, node1.lat, node1.depth, data[node1.id])
            snode2_below = SideNode(node2.lon, node2.lat, node2.depth, data[node2.id])
        # Save to linked list
        snode1.set_below(snode1_below)
        snode2.set_below(snode2_below)
        # Get ready for next iteration
        snode1 = snode1_below
        snode2 = snode2_below


# Given two Nodes where the straight line (in lon-lat space) between them
# intersects the line longitude=lon0, calculate the latitude of this
# intersection and linearly interpolate the model output at this intersection.
# Input:
# node1, node2 = Nodes at the endpoints of this line
# lon0 = longitude to interpolate to
# data = FESOM output on regular grid; can be a single time index or a 
#        timeseries
# Output:
# snode_sfc = SideNode object for the intersection at the surface, with all
#             SideNodes beneath it also interpolated and linked in
def interp_snode (node1, node2, lon0, data):

    # Calculate latitude at the intersection using basic equation of a line
    lat0 = node1.lat + (node2.lat - node1.lat)/(node2.lon - node1.lon)*(lon0 - node1.lon)
    # Calculate distances from intersection to node1 (d1) and to node2 (d2)
    d1 = sqrt((lon0 - node1.lon)**2 + (lat0 - node1.lat)**2)
    d2 = sqrt((lon0 - node2.lon)**2 + (lat0 - node2.lat)**2)
    # Save the values of the given variable at each Node
    if len(data.shape) == 2:
        # Timeseries
        var1 = data[:,node1.id]
        var2 = data[:,node2.id]
    else:
        # Single time index
        var1 = data[node1.id]
        var2 = data[node2.id]
    # Linearly interpolate the variable at the intersection
    var0 = var1 + (var2 - var1)/(d2 + d1)*d1
    # Also interpolate depth
    depth = node1.depth + (node2.depth - node1.depth)/(d2 + d1)*d1
    # Create a surface SideNode at this intersection
    snode_sfc = SideNode(lon0, lat0, depth, var0)

    # Now travel down the water column to interpolate the intersection at
    # each depth level
    snode = snode_sfc
    while True:
        # Find the Nodes directly below
        node1 = node1.below
        node2 = node2.below
        if node1 is None or node2 is None:
            # We've reached the bottom; stop
            break
        # Latitude and distances will not change; just interpolate the new var0
        if len(data.shape) == 2:
            # Timeseries
            var1 = data[:,node1.id]
            var2 = data[:,node2.id]
        else:
            # Single time index
            var1 = data[node1.id]
            var2 = data[node2.id]
        var0 = var1 + (var2 - var1)/(d2 + d1)*d1
        # Similarly interpolate depth
        depth = node1.depth + (node2.depth - node1.depth)/(d2 + d1)*d1
        # Create a SideNode at this depth
        snode_below = SideNode(lon0, lat0, depth, var0)
        # Add to the linked list
        snode.set_below(snode_below)
        # Get ready for next iteration
        snode = snode_below

    return snode_sfc

    
                

    

    
                        
                     
    
