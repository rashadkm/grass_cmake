"""!@package grass.temporal

@brief GRASS Python scripting module (temporal GIS functions)

Temporal GIS export functions to be used in temporal modules

Usage:

@code
import grass.temporal as tgis

input="/tmp/temp_1950_2012.tar.gz"
output="temp_1950_2012"
extrdir="/tmp"
title="My new dataset"
descr="May new shiny dataset"
location=None
link=True
exp=True
overr=False
create=False
tgis.import_stds(input, output, extrdir, title, descr, location,
                link, exp, overr, create, "strds")
...
@endcode

(C) 2012-2013 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

import os
import os.path
import tarfile

from space_time_datasets import *
from register import *
import factory
from factory import *

proj_file_name = "proj.txt"
init_file_name = "init.txt"
list_file_name = "list.txt"

# This global variable is for unique vector map export,
# since single vector maps may have several layer
# and therefore several attribute tables
imported_maps = {}

############################################################################


def _import_raster_maps_from_gdal(maplist, overr, exp, location, link, format_):
    impflags = ""
    if overr:
        impflags += "o"
    if exp or location:
        impflags += "e"
    for row in maplist:
        name = row["name"]
        if format_ == "GTiff":
            filename = row["filename"] + ".tif"
        elif format_=="AAIGrid":
            filename = row["filename"] + ".asc"
            if not overr:
                impflags += "o"

        if link:
            ret = core.run_command("r.external", input=filename,
                                   output=name,
                                   flags=impflags,
                                   overwrite=core.overwrite())
        else:
            ret = core.run_command("r.in.gdal", input=filename,
                                   output=name,
                                   flags=impflags,
                                   overwrite=core.overwrite())

        if ret != 0:
            core.fatal(_("Unable to import/link raster map <%s> from file %s.") %(name, 
                                                                     filename))

        # Set the color rules if present
        filename = row["filename"] + ".color"
        if os.path.isfile(filename):
            ret = core.run_command("r.colors", map=name,
                                   rules=filename,
                                   overwrite=core.overwrite())
            if ret != 0:
                core.fatal(_("Unable to set the color rules for "
                             "raster map <%s>.") % name)

############################################################################


def _import_raster_maps(maplist):
    # We need to disable the projection check because of its
    # simple implementation
    impflags = "o"
    for row in maplist:
        name = row["name"]
        filename = row["filename"] + ".pack"
        ret = core.run_command("r.unpack", input=filename,
                               output=name,
                               flags=impflags,
                               overwrite=core.overwrite(),
                               verbose=True)

        if ret != 0:
            core.fatal(_("Unable to unpack raster map <%s> from file %s.") % (name, 
                                                                              filename))

############################################################################


def _import_vector_maps_from_gml(maplist, overr, exp, location, link):
    impflags = "o"
    if exp or location:
        impflags += "e"
    for row in maplist:
        name = row["name"]
        filename = row["filename"] + ".xml"

        ret = core.run_command("v.in.ogr", dsn=filename,
                               output=name,
                               flags=impflags,
                               overwrite=core.overwrite())

        if ret != 0:
            core.fatal(_("Unable to import vector map <%s> from file %s.") % (name,
                                                                              filename))

############################################################################


def _import_vector_maps(maplist):
    # We need to disable the projection check because of its
    # simple implementation
    impflags = "o"
    for row in maplist:
        # Separate the name from the layer
        name = row["name"].split(":")[0]
        # Import only unique maps
        if name in imported_maps:
            continue
        filename = row["filename"] + ".pack"
        ret = core.run_command("v.unpack", input=filename,
                               output=name,
                               flags=impflags,
                               overwrite=core.overwrite(),
                               verbose=True)

        if ret != 0:
            core.fatal(_("Unable to unpack vector map <%s> from file %s.") % (name, 
                                                                              filename))

        imported_maps[name] = name
############################################################################


def import_stds(input, output, extrdir, title=None, descr=None, location=None,
        link=False, exp=False, overr=False, create=False, stds_type="strds", base=None):
    """!Import space time datasets of type raster and vector

        @param input Name of the input archive file
        @param output The name of the output space time dataset
        @param extrdir The extraction directory
        @param title The title of the new created space time dataset
        @param descr The description of the new created
                     space time dataset
        @param location The name of the location that should be created,
                        maps are imported into this location
        @param link Switch to link raster maps instead importing them
        @param exp Extend location extents based on new dataset
        @param overr Override projection (use location's projection)
        @param create Create the location specified by the "location"
                      parameter and exit.
                      Do not import the space time datasets.
        @param stds_type The type of the space time dataset that
                         should be imported
        @param base The base name of the new imported maps, it will be extended
                    using a numerical index.
    """

    global raise_on_error
    old_state = core.raise_on_error
    core.set_raise_on_error(True)

    # Check if input file and extraction directory exits
    if not os.path.exists(input):
        core.fatal(_("Space time raster dataset archive <%s> not found")
                   % input)
    if not create and not os.path.exists(extrdir):
        core.fatal(_("Extraction directory <%s> not found") % extrdir)

    tar = tarfile.open(name=input, mode='r')

    # Check for important files
    members = tar.getnames()

    if init_file_name not in members:
        core.fatal(_("Unable to find init file <%s>") % init_file_name)
    if list_file_name not in members:
        core.fatal(_("Unable to find list file <%s>") % list_file_name)
    if proj_file_name not in members:
        core.fatal(_("Unable to find projection file <%s>") % proj_file_name)

    tar.extractall(path=extrdir)
    tar.close()

    # We use a new list file name for map registration
    new_list_file_name = list_file_name + "_new"
    # Save current working directory path
    old_cwd = os.getcwd()

    # Switch into the data directory
    os.chdir(extrdir)

    # Check projection information
    if not location:
        temp_name = core.tempfile()
        temp_file = open(temp_name, "w")
        proj_name = os.path.abspath(proj_file_name)

        p = core.start_command("g.proj", flags="j", stdout=temp_file)
        p.communicate()
        temp_file.close()

        if not core.compare_key_value_text_files(temp_name, proj_name, sep="="):
            if overr:
                core.warning(_("Projection information does not match. "
                               "Proceeding..."))
            else:
                diff = ''.join(core.diff_files(temp_name, proj_name))
                core.warning(_("Difference between PROJ_INFO file of imported map "
                               "and of current location:\n{diff}").format(diff=diff))
                core.fatal(_("Projection information does not match. Aborting."))

    # Create a new location based on the projection information and switch
    # into it
    old_env = core.gisenv()
    if location:
        try:
            proj4_string = open(proj_file_name, 'r').read()
            core.create_location(dbase=old_env["GISDBASE"],
                                 location=location,
                                 proj4=proj4_string)
            # Just create a new location and return
            if create:
                os.chdir(old_cwd)
                return
        except Exception as e:
            core.fatal(_("Unable to create location %(l)s. Reason: %(e)s")
                         % {'l': location, 'e': str(e)})
        # Switch to the new created location
        ret = core.run_command("g.mapset", mapset="PERMANENT",
                               location=location,
                               gisdbase=old_env["GISDBASE"])
        if ret != 0:
            core.fatal(_("Unable to switch to location %s") % location)
        # create default database connection
        ret = core.run_command("t.connect", flags="d")
        if ret != 0:
            core.fatal(_("Unable to create default temporal database "
                         "in new location %s") % location)

    try:
        # Make sure the temporal database exists
        factory.init()

        fs = "|"
        maplist = []
        mapset = get_current_mapset()
        list_file = open(list_file_name, "r")
        new_list_file = open(new_list_file_name, "w")

        # Read the map list from file
        line_count = 0
        while True:
            line = list_file.readline()
            if not line:
                break

            line_list = line.split(fs)

            # The filename is actually the base name of the map
            # that must be extended by the file suffix
            filename = line_list[0].strip().split(":")[0]
            if base:
                mapname = "%s_%i"%(base, line_count)
                mapid= "%s@%s"%(mapname, mapset)
            else:
                mapname = filename
                mapid = mapname + "@" + mapset

            row = {}
            row["filename"] = filename
            row["name"] = mapname
            row["id"] = mapid
            row["start"] = line_list[1].strip()
            row["end"] = line_list[2].strip()
            
            new_list_file.write("%s%s%s%s%s\n"%(mapname,fs, row["start"], 
                                              fs, row["end"]))

            maplist.append(row)
            line_count += 1

        list_file.close()
        new_list_file.close()
        
        # Read the init file
        fs = "="
        init = {}
        init_file = open(init_file_name, "r")
        while True:
            line = init_file.readline()
            if not line:
                break

            kv = line.split(fs)
            init[kv[0]] = kv[1].strip()

        init_file.close()

        if "temporal_type" not in init or \
           "semantic_type" not in init or \
           "number_of_maps" not in init:
            core.fatal(_("Key words %(t)s, %(s)s or %(n)s not found in init"
                         " file.") % {'t': "temporal_type",
                                      's': "semantic_type",
                                      'n': "number_of_maps"})

        if line_count != int(init["number_of_maps"]):
            core.fatal(_("Number of maps mismatch in init and list file."))

        format_ = "GTiff"
        type_ = "strds"

        if "stds_type" in init:
            type_ = init["stds_type"]
        if "format" in init:
            format_ = init["format"]

        if stds_type != type_:
            core.fatal(_("The archive file is of wrong space time dataset type"))

        # Check the existence of the files
        if format_ == "GTiff":
            for row in maplist:
                filename = row["filename"] + ".tif"
                if not os.path.exists(filename):
                    core.fatal(_("Unable to find geotiff raster file "
                                 "<%s> in archive.") % filename)
        elif format_ == "AAIGrid":
            for row in maplist:
                filename = row["filename"] + ".asc"
                if not os.path.exists(filename):
                    core.fatal(_("Unable to find AAIGrid raster file "
                                 "<%s> in archive.") % filename)
        elif format_ == "GML":
            for row in maplist:
                filename = row["filename"] + ".xml"
                if not os.path.exists(filename):
                    core.fatal(_("Unable to find GML vector file "
                                 "<%s> in archive.") % filename)
        elif format_ == "pack":
            for row in maplist:
                if type_ == "stvds":
                    filename = str(row["filename"].split(":")[0]) + ".pack"
                else:
                    filename = row["filename"] + ".pack"
                if not os.path.exists(filename):
                    core.fatal(_("Unable to find GRASS package file "
                                 "<%s> in archive.") % filename)
        else:
            core.fatal(_("Unsupported input format"))

        # Check the space time dataset
        id = output + "@" + mapset
        sp = dataset_factory(type_, id)
        if sp.is_in_db() and core.overwrite() == False:
            core.fatal(_("Space time %(t)s dataset <%(sp)s> is already in the "
                         "database. Use the overwrite flag.") % {'t': type_,
                                                                 'sp': sp.get_id()})

        # Import the maps
        if type_ == "strds":
            if format_ == "GTiff" or format_ == "AAIGrid":
                _import_raster_maps_from_gdal(
                    maplist, overr, exp, location, link, format_)
            if format_ == "pack":
                _import_raster_maps(maplist)
        elif type_ == "stvds":
            if format_ == "GML":
                _import_vector_maps_from_gml(
                    maplist, overr, exp, location, link)
            if format_ == "pack":
                _import_vector_maps(maplist)

        # Create the space time dataset
        if sp.is_in_db() and core.overwrite() == True:
            core.info(_("Overwrite space time %(sp)s dataset "
                        "<%(id)s> and unregister all maps.") % {
                        'sp': sp.get_new_map_instance(None).get_type(),
                        'id': sp.get_id()})
            sp.delete()
            sp = sp.get_new_instance(id)

        temporal_type = init["temporal_type"]
        semantic_type = init["semantic_type"]
        relative_time_unit = None
        if temporal_type == "relative":
            if "relative_time_unit" not in init:
                core.fatal(_("Key word %s not found in init file.") % ("relative_time_unit"))
            relative_time_unit = init["relative_time_unit"]
            sp.set_relative_time_unit(relative_time_unit)

        core.verbose(_("Create space time %s dataset.") %
                     sp.get_new_map_instance(None).get_type())

        sp.set_initial_values(temporal_type=temporal_type,
                              semantic_type=semantic_type, title=title,
                              description=descr)
        sp.insert()

        # register the maps
        fs = "|"
        register_maps_in_space_time_dataset(
            type=sp.get_new_map_instance(None).get_type(),
            name=output, file=new_list_file_name, start="file",
            end="file", unit=relative_time_unit, dbif=None, fs=fs)

        os.chdir(old_cwd)
    except:
        raise

    # Make sure the location is switched back correctly
    finally:
        if location:
            # Switch to the old location
            ret = core.run_command("g.mapset", mapset=old_env["MAPSET"],
                                   location=old_env["LOCATION_NAME"],
                                   gisdbase=old_env["GISDBASE"])

        core.set_raise_on_error(old_state)
