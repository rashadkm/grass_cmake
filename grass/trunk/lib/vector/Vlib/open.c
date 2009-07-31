/*!
 * \file vector/Vlib/open.c
 *
 * \brief Vector library - Open vector map
 *
 * Higher level functions for reading/writing/manipulating vectors.
 *
 * (C) 2001-2009 by the GRASS Development Team
 *
 * This program is free software under the GNU General Public License
 * (>=v2).  Read the file COPYING that comes with GRASS for details.
 *
 * \author Original author CERL, probably Dave Gerdes or Mike
 * Higgins.
 * \author Update to GRASS 5.7 Radim Blazek and David D. Gray.
 */
#include <grass/config.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <grass/glocale.h>
#include <grass/gis.h>
#include <grass/vector.h>

#define MAX_OPEN_LEVEL 2

static int open_old_dummy()
{
    return 0;
}

#ifndef HAVE_OGR
static int format()
{
    G_fatal_error(_("Requested format is not compiled in this version"));
    return 0;
}
#endif

static int Open_level = 0;

static int (*Open_old_array[][2]) () = {
    {
    open_old_dummy, V1_open_old_nat}
#ifdef HAVE_OGR
    , {
    open_old_dummy, V1_open_old_ogr}
#else
    , {
    open_old_dummy, format}
#endif
};

static void fatal_error(int ferror, char *errmsg)
{
    switch (ferror) {
    case GV_FATAL_EXIT:
	G_fatal_error(errmsg);
	break;
    case GV_FATAL_PRINT:
	G_warning(errmsg);
	break;
    case GV_FATAL_RETURN:
	break;
    }
}


/*!
 * \brief Predetermine level at which a vector map will be opened for
 * reading.
 *
 * If it can't open that level, the open will fail. The specified
 * level must be set before any call to open. The default is to try to
 * open the highest level possible, and keep stepping down until
 * success.
 *
 * NOTE: This should only be used to set when you wish to force a
 * lower level open. If you require a higher level, then just check
 * the return to verify the level instead of forcing it.  This is
 * because future releases will have higher levels which will be
 * downward compatible and which your programs should support by
 * default.
 *
 * \param level vector (topo) level
 *
 * \return 0 on success
 * \return 1 on error
 */

int Vect_set_open_level(int level)
{
    Open_level = level;
    if (Open_level < 1 || Open_level > MAX_OPEN_LEVEL) {
	G_warning(_("Programmer requested unknown open level %d"),
		  Open_level);
	Open_level = 0;
	return 1;
    }

    return 0;
}

/*! 
 * \brief Open old vector for reading.
 *
 * In case of error, the functions respect fatal error settings.
 *
 * \param[out] Map vector map
 * \param name name of vector map to open
 * \param mapset mapset name
 * \param update open for update
 * \param head_only read only header info from 'head', 'dbln', 'topo', 'cidx' is not opened. The header may be opened on level 2 only. 
 *
 * \return level of openness (1, 2)
 * \return -1 in error
 */
int
Vect__open_old(struct Map_info *Map, const char *name, const char *mapset,
	       int update, int head_only)
{
    char buf[GNAME_MAX + 10], buf2[GMAPSET_MAX + 10], xname[GNAME_MAX],
	xmapset[GMAPSET_MAX], errmsg[2000];
    FILE *fp;
    int level, level_request, ferror;
    int format, ret;
    int ogr_mapset;
    const char *fmapset;

    G_debug(1, "Vect__open_old(): name = %s mapset= %s update = %d", name,
	    mapset, update);

    /* zero Map_info structure */
    G_zero(Map, sizeof(struct Map_info));

    /* TODO: Open header for update ('dbln') */

    ferror = Vect_get_fatal_error();
    Vect_set_fatal_error(GV_FATAL_EXIT);

    level_request = Open_level;
    Open_level = 0;

    /* initialize Map->head */
    Vect__init_head(Map);
    /* initialize Map->plus */
    dig_init_plus(&(Map->plus));

    ogr_mapset = 0;
    if (G__name_is_fully_qualified(name, xname, xmapset)) {
	if (strcmp(xmapset, "OGR") == 0) {
	    /* unique OGR mapset detected */
	    G_debug(1, "OGR mapset detected");
	    ogr_mapset = 1;
	    Map->fInfo.ogr.dsn = xname;
	    Map->fInfo.ogr.layer_name = NULL; /* no layer to be open */
	}
	else {
	    sprintf(buf, "%s/%s", GV_DIRECTORY, xname);
	    sprintf(buf2, "%s@%s", GV_COOR_ELEMENT, xmapset);
	}
	Map->name = G_store(xname);
	Map->mapset = G_store(xmapset);
    }
    else {
	sprintf(buf, "%s/%s", GV_DIRECTORY, name);
	sprintf(buf2, "%s", GV_COOR_ELEMENT);
	Map->name = G_store(name);

	if (mapset)
	    Map->mapset = G_store(mapset);
	else
	    Map->mapset = G_store("");
    }

    fmapset = G_find_vector2(Map->name, Map->mapset);
    if (fmapset == NULL) {
	sprintf(errmsg, _("Vector map <%s> not found"),
		Vect_get_full_name(Map));
	fatal_error(ferror, errmsg);
	return -1;
    }
    Map->mapset = G_store(fmapset);

    Map->location = G_store(G_location());
    Map->gisdbase = G_store(G_gisdbase());
    
    if (update && (0 != strcmp(Map->mapset, G_mapset()))) {
	G_warning(_("Vector map which is not in the current mapset cannot be opened for update"));
	return -1;
    }

    G_debug(1, "Map name: %s", Map->name);
    G_debug(1, "Map mapset: %s", Map->mapset);

    /* Read vector format information */
    if (ogr_mapset) {
	format = GV_FORMAT_OGR;
    }
    else {
	format = 0;
	sprintf(buf, "%s/%s", GV_DIRECTORY, Map->name);
	G_debug(1, "open format file: '%s/%s/%s'", Map->mapset, buf,
		GV_FRMT_ELEMENT);
	fp = G_fopen_old(buf, GV_FRMT_ELEMENT, Map->mapset);
	if (fp == NULL) {
	    G_debug(1, "Vector format: %d (native)", format);
	    format = GV_FORMAT_NATIVE;
	}
	else {
	    format = dig_read_frmt_ascii(fp, &(Map->fInfo));
	    fclose(fp);
	    
	    G_debug(1, "Vector format: %d (non-native)", format);
	    if (format < 0) {
		sprintf(errmsg, _("Unable to open vector map <%s>"),
			Vect_get_full_name(Map));
		fatal_error(ferror, errmsg);
		return -1;
	    }
	}
    }
    Map->format = format;
    
    /* Read vector head */
    if (!ogr_mapset && Vect__read_head(Map) != 0) {
	sprintf(errmsg,
		_("Unable to open vector map <%s> on level %d. "
		  "Try to rebuild vector topology by v.build."),
		Vect_get_full_name(Map), level_request);
	G_warning(_("Unable to read head file of vector <%s>"),
		  Vect_get_full_name(Map));
    }
    
    G_debug(1, "Level request = %d", level_request);

    /* There are only 2 possible open levels, 1 and 2. Try first to open 'support' files
     * (topo,sidx,cidx), these files are the same for all formats.
     * If it is not possible and requested level is 2, return error,
     * otherwise call Open_old_array[format][1], to open remaining files/sources (level 1)
     */

    /* Try to open support files if level was not requested or requested level is 2 (format independent) */
    if (level_request == 0 || level_request == 2) {
	level = 2;		/* We expect success */
	/* open topo */
	ret = Vect_open_topo(Map, head_only);
	if (ret == 1) {		/* topo file is not available */
	    G_debug(1, "topo file for vector '%s' not available.",
		    Vect_get_full_name(Map));
	    level = 1;
	}
	else if (ret == -1) {
	    G_fatal_error(_("Unable to open topology file for vector map <%s>"),
			  Vect_get_full_name(Map));
	}
	/* open spatial index */
	if (level == 2) {
	    ret = Vect_open_sidx(Map, (update != 0));
	    if (ret == 1) {	/* sidx file is not available */
		G_debug(1, "sidx file for vector '%s' not available.",
			Vect_get_full_name(Map));
		level = 1;
	    }
	    else if (ret == -1) {
		G_fatal_error(_("Unable to open spatial index file for vector map <%s>"),
			      Vect_get_full_name(Map));
	    }
	}
	/* open category index */
	if (level == 2) {
	    ret = Vect_cidx_open(Map, head_only);
	    if (ret == 1) {	/* category index is not available */
		G_debug(1,
			"cidx file for vector '%s' not available.",
			Vect_get_full_name(Map));
		dig_free_plus(&(Map->plus));	/* free topology */
		dig_spidx_free(&(Map->plus));	/* free spatial index */
		level = 1;
	    }
	    else if (ret == -1) {	/* file exists, but cannot be opened */
		G_fatal_error(_("Unable to open category index file for vector map <%s>"),
			      Vect_get_full_name(Map));
	    }
	}
#ifdef HAVE_OGR
	/* Open OGR specific support files */
	if (level == 2 && Map->format == GV_FORMAT_OGR) {
	    if (V2_open_old_ogr(Map) < 0) {
		dig_free_plus(&(Map->plus));
		dig_spidx_free(&(Map->plus));
		dig_cidx_free(&(Map->plus));
		level = 1;
	    }
	}
#endif
	if (level_request == 2 && level < 2) {
	    if (ogr_mapset) {
		G_warning(_("Topology level (2) is not supported when reading "
			    "OGR layers directly. For topology level "
			    "is required link to OGR layer via v.external command."));
	    }
	    else {
		sprintf(errmsg,
			_("Unable to open vector map <%s> on level %d. "
			  "Try to rebuild vector topology by v.build."),
			Vect_get_full_name(Map), level_request);
		fatal_error(ferror, errmsg);
		return -1;
	    }
	}
    }
    else {
	level = 1;		/* I.e. requested level is 1 */
    }

    /* Open level 1 files / sources (format specific) */
    if (!head_only) {		/* No need to open coordinates */
	if (0 != (*Open_old_array[format][1]) (Map, update)) {	/* Cannot open */
	    if (level == 2) {	/* support files opened */
		dig_free_plus(&(Map->plus));
		dig_spidx_free(&(Map->plus));
		dig_cidx_free(&(Map->plus));
	    }
	    sprintf(errmsg,
		    _("Unable to open vector map <%s> on level %d. "
		      "Try to rebuild vector topology by v.build."),
		    Vect_get_full_name(Map), level_request);
	    fatal_error(ferror, errmsg);
	    return -1;
	}
    }
    else {
	Map->head.with_z = Map->plus.with_z;	/* take dimension from topo */
    }

    /* Set status */
    Map->open = VECT_OPEN_CODE;
    Map->level = level;
    Map->head_only = head_only;
    Map->support_updated = 0;
    if (update) {
	Map->mode = GV_MODE_RW;
	Map->plus.mode = GV_MODE_RW;
    }
    else {
	Map->mode = GV_MODE_READ;
	Map->plus.mode = GV_MODE_READ;
    }
    if (head_only) {
	Map->head_only = 1;
    }
    else {
	Map->head_only = 0;
    }

    Map->Constraint_region_flag = 0;
    Map->Constraint_type_flag = 0;
    G_debug(1, "Vect_open_old(): vector opened on level %d", level);

    if (level == 1) {		/* without topology */
	Map->plus.built = GV_BUILD_NONE;
    }
    else {			/* level 2, with topology */
	Map->plus.built = GV_BUILD_ALL;	/* Highest level of topology for level 2 */
    }

    Map->plus.do_uplist = 0;

    Map->dblnk = Vect_new_dblinks_struct();
    Vect_read_dblinks(Map);

    /* Open history file */
    sprintf(buf, "%s/%s", GV_DIRECTORY, Map->name);

    if (update) {		/* native only */
	Map->hist_fp = G_fopen_modify(buf, GV_HIST_ELEMENT);
	if (Map->hist_fp == NULL) {
	    sprintf(errmsg,
		    _("Unable to open history file for vector map <%s>"),
		    Vect_get_full_name(Map));
	    fatal_error(ferror, errmsg);
	    return (-1);
	}
	fseek(Map->hist_fp, (off_t) 0, SEEK_END);
	Vect_hist_write(Map,
			"---------------------------------------------------------------------------------\n");

    }
    else {
	if (Map->format == GV_FORMAT_NATIVE || Map->format == GV_FORMAT_OGR) {
	    Map->hist_fp =
		G_fopen_old(buf, GV_HIST_ELEMENT, Map->mapset);
	    /* If NULL (does not exist) then Vect_hist_read() handle that */
	}
	else {
	    Map->hist_fp = NULL;
	}
    }

    if (!head_only) {		/* Cannot rewind if not fully opened */
	Vect_rewind(Map);
    }

    /* Delete support files if native format was opened for update (not head_only) */
    if (update && !head_only) {
	char file_path[2000];
	struct stat info;

	sprintf(buf, "%s/%s", GV_DIRECTORY, name);

	G__file_name(file_path, buf, GV_TOPO_ELEMENT, G_mapset());
	if (stat(file_path, &info) == 0)	/* file exists? */
	    unlink(file_path);

	G__file_name(file_path, buf, GV_SIDX_ELEMENT, G_mapset());
	if (stat(file_path, &info) == 0)	/* file exists? */
	    unlink(file_path);

	G__file_name(file_path, buf, GV_CIDX_ELEMENT, G_mapset());
	if (stat(file_path, &info) == 0)	/* file exists? */
	    unlink(file_path);
    }

    return (level);
}

/*!
 * \brief Open existing vector for reading
 *
 * In case of error, the functions respect fatal error settings.
 *
 * \param[out] Map vector map
 * \param name name of vector map
 * \param mapset mapset name
 *
 * \return level of openness [1, 2, (3)]
 * \return -1 on error
 */
int Vect_open_old(struct Map_info *Map, const char *name, const char *mapset)
{
    return (Vect__open_old(Map, name, mapset, 0, 0));
}

/*!
 * \brief Open existing vector for reading/writing
 *
 * In case of error, the functions respect fatal error settings.
 *
 * \param[out] Map vector map
 * \param name name of vector map to update
 * \param mapset mapset name
 *
 * \return level of openness [1, 2, (3)]
 * \return -1 on error
 */
int
Vect_open_update(struct Map_info *Map, const char *name, const char *mapset)
{
    int ret;

    ret = Vect__open_old(Map, name, mapset, 1, 0);

    if (ret > 0) {
	Map->plus.do_uplist = 1;

	Map->plus.uplines = NULL;
	Map->plus.n_uplines = 0;
	Map->plus.alloc_uplines = 0;
	Map->plus.upnodes = NULL;
	Map->plus.n_upnodes = 0;
	Map->plus.alloc_upnodes = 0;

	/* read spatial index */

	/* Build spatial index from topo */
	/* Vect_build_sidx_from_topo(Map); */
    }

    return ret;
}

/*! 
 * \brief Reads only info about vector map from headers of 'head',
 * 'dbln', 'topo' and 'cidx' file.
 *
 * In case of error, the functions respect fatal error settings.
 * 
 * \param[out] Map pointer to Map_info structure
 * \param name name of vector map to read
 * \param mapset mapset name
 *
 * \return level of openness [1, 2, (3)]
 * \return -1 on error
 */
int Vect_open_old_head(struct Map_info *Map, const char *name, const char *mapset)
{
    return (Vect__open_old(Map, name, mapset, 0, 1));
}

/*!
 * \brief Open old vector head for updating (mostly for database link updates)
 *
 * In case of error, the functions respect fatal error settings.
 *
 * \param[out] Map vector map
 * \param name name of vector map to update
 * \param mapset mapset name
 *
 * \return level of openness [1, 2, (3)]
 * \return -1 on error
 */
int
Vect_open_update_head(struct Map_info *Map, const char *name,
		      const char *mapset)
{
    int ret;

    ret = Vect__open_old(Map, name, mapset, 1, 1);

    if (ret > 0) {		/* Probably not important */
	Map->plus.do_uplist = 1;

	Map->plus.uplines = NULL;
	Map->plus.n_uplines = 0;
	Map->plus.alloc_uplines = 0;
	Map->plus.upnodes = NULL;
	Map->plus.n_upnodes = 0;
	Map->plus.alloc_upnodes = 0;
    }

    return ret;
}

/*!
 * \brief Open new vector for reading/writing
 *
 * \param[in,out] Map pointer to Map_info structure
 * \param name name of vector map
 * \param with_z non-zero value for 3D vector data
 *
 * \return 1 on success
 * \return -1 on error
 */
int Vect_open_new(struct Map_info *Map, const char *name, int with_z)
{
    int ret, ferror;
    char errmsg[2000], buf[500];
    char xname[GNAME_MAX], xmapset[GMAPSET_MAX];

    G_debug(2, "Vect_open_new(): name = %s", name);

    Vect__init_head(Map);
    ferror = Vect_get_fatal_error();
    Vect_set_fatal_error(GV_FATAL_EXIT);

    if (G__name_is_fully_qualified(name, xname, xmapset)) {
	if (strcmp(xmapset, G_mapset()) != 0) {
	    sprintf(errmsg, _("%s is not in the current mapset (%s)"), name,
		    G_mapset());
	    fatal_error(ferror, errmsg);
	}
	name = xname;
    }

    /* check for [A-Za-z][A-Za-z0-9_]* in name */
    if (Vect_legal_filename(name) < 0) {
	sprintf(errmsg, _("Vector map name is not SQL compliant"));
	fatal_error(ferror, errmsg);
	return (-1);
    }

    /* Check if map already exists */
    if (G_find_vector2(name, G_mapset()) != NULL) {
	G_warning(_("Vector map <%s> already exists and will be overwritten"),
		  name);

	ret = Vect_delete(name);
	if (ret == -1) {
	    sprintf(errmsg, _("Unable to delete vector map <%s>"), name);
	    fatal_error(ferror, errmsg);
	    return (-1);
	}
    }

    Map->name = G_store(name);
    Map->mapset = G_store(G_mapset());
    Map->location = G_store(G_location());
    Map->gisdbase = G_store(G_gisdbase());

    Map->format = GV_FORMAT_NATIVE;

    if (V1_open_new_nat(Map, name, with_z) < 0) {
	sprintf(errmsg, _("Unable to create vector map <%s>"),
		Vect_get_full_name(Map));
	fatal_error(ferror, errmsg);
	return (-1);
    }

    /* Open history file */
    sprintf(buf, "%s/%s", GV_DIRECTORY, Map->name);
    Map->hist_fp = G_fopen_new(buf, GV_HIST_ELEMENT);
    if (Map->hist_fp == NULL) {
	sprintf(errmsg, _("Unable to open history file for vector map <%s>"),
		Vect_get_full_name(Map));
	fatal_error(ferror, errmsg);
	return (-1);
    }

    Open_level = 0;

    /* initialize topo */
    dig_init_plus(&(Map->plus));

    /* initialize spatial index */
    Vect_open_sidx(Map, 2);

    Map->open = VECT_OPEN_CODE;
    Map->level = 1;
    Map->head_only = 0;
    Map->support_updated = 0;
    Map->plus.built = GV_BUILD_NONE;
    Map->mode = GV_MODE_RW;
    Map->Constraint_region_flag = 0;
    Map->Constraint_type_flag = 0;
    Map->head.with_z = with_z;
    Map->plus.do_uplist = 0;

    Map->dblnk = Vect_new_dblinks_struct();

    return 1;
}

/*!
 * \brief Update Coor_info structure
 *
 * \param Map pointer to Map_info structure
 * \param[out] Info pointer to Coor_info structure
 *
 * \return 1 on success
 * \return 0 on error
 */
int Vect_coor_info(const struct Map_info *Map, struct Coor_info *Info)
{
    char buf[2000], path[2000];
    struct stat stat_buf;

    switch (Map->format) {
    case GV_FORMAT_NATIVE:
	sprintf(buf, "%s/%s", GV_DIRECTORY, Map->name);
	G__file_name(path, buf, GV_COOR_ELEMENT, Map->mapset);
	G_debug(1, "get coor info: %s", path);
	if (0 != stat(path, &stat_buf)) {
	    G_warning(_("Unable to stat file <%s>"), path);
	    Info->size = -1L;
	    Info->mtime = -1L;
	}
	else {
	    Info->size = (off_t) stat_buf.st_size;	/* file size */
	    Info->mtime = (long)stat_buf.st_mtime;	/* last modified time */
	}
	/* stat does not give correct size on MINGW 
	 * if the file is opened */
#ifdef __MINGW32__
	if (Map->open == VECT_OPEN_CODE) {
	    dig_fseek(&(Map->dig_fp), 0L, SEEK_END);
	    G_debug(2, "ftell = %d", dig_ftell(&(Map->dig_fp)));
	    Info->size = dig_ftell(&(Map->dig_fp));
	}
#endif
	break;
    case GV_FORMAT_OGR:
	Info->size = 0L;
	Info->mtime = 0L;
	break;
    }
    G_debug(1, "Info->size = %lu, Info->mtime = %ld",
	    (unsigned long)Info->size, Info->mtime);

    return 1;
}

/*!
 * \brief Gets maptype (native, shape, postgis)
 *
 * Note: string is allocated by G_store(). Free allocated memory with
 * G_free().
 *
 * \param Map vector map
 *
 * \return maptype string on success
 * \return error message on error
 */
const char *Vect_maptype_info(const struct Map_info *Map)
{
    char maptype[1000];

    switch (Map->format) {
    case GV_FORMAT_NATIVE:
	sprintf(maptype, "native");
	break;
    case GV_FORMAT_OGR:
	sprintf(maptype, "ogr");
	break;
    default:
	sprintf(maptype, "unknown %d (update Vect_maptype_info)",
		Map->format);
    }

    return G_store(maptype);
}


/*!
 * \brief Open topo file
 *
 * \param[in,out] Map pointer to Map_info structure
 * \param head_only open only head
 *
 * \return 0 on success
 * \return 1 file does not exist
 * \return -1 on error
 */
int Vect_open_topo(struct Map_info *Map, int head_only)
{
    int err, ret;
    char buf[500], file_path[2000];
    struct gvfile fp;
    struct Coor_info CInfo;
    struct Plus_head *Plus;
    struct stat info;

    G_debug(1, "Vect_open_topo(): name = %s mapset= %s", Map->name,
	    Map->mapset);

    Plus = &(Map->plus);

    sprintf(buf, "%s/%s", GV_DIRECTORY, Map->name);
    G__file_name(file_path, buf, GV_TOPO_ELEMENT, Map->mapset);

    if (stat(file_path, &info) != 0)	/* does not exist */
	return 1;

    dig_file_init(&fp);
    fp.file = G_fopen_old(buf, GV_TOPO_ELEMENT, Map->mapset);

    if (fp.file == NULL) {	/* topo file is not available */
	G_debug(1, "Cannot open topo file for vector '%s@%s'.",
		Map->name, Map->mapset);
	return -1;
    }

    /* get coor info */
    Vect_coor_info(Map, &CInfo);

    /* load head */
    if (dig_Rd_Plus_head(&fp, Plus) == -1)
	return -1;

    G_debug(1, "Topo head: coor size = %lu, coor mtime = %ld",
	    (unsigned long)Plus->coor_size, Plus->coor_mtime);

    /* do checks */
    err = 0;
    if (CInfo.size != Plus->coor_size) {
	G_warning(_("Size of 'coor' file differs from value saved in topology file"));
	err = 1;
    }
    /* Do not check mtime because mtime is changed by copy */
    /*
       if ( CInfo.mtime != Plus->coor_mtime ) {
       G_warning ( "Time of last modification for 'coor' file differs from value saved in topo file.\n");
       err = 1;
       }
     */
    if (err) {
	G_warning(_("Please rebuild topology for vector map <%s@%s>"),
		  Map->name, Map->mapset);
	return -1;
    }

    /* load file to the memory */
    /* dig_file_load ( &fp); */

    /* load topo to memory */
    ret = dig_load_plus(Plus, &fp, head_only);

    fclose(fp.file);
    /* dig_file_free ( &fp); */

    if (ret == 0)
	return -1;

    return 0;
}

/*!
 * \brief Open spatial index file ('sidx')
 *
 * \param[in,out] Map pointer to Map_info
 * \param mode 0 old, 1 update, 2 new
 *
 * \return 0 on success
 * \return -1 on error
 */
int Vect_open_sidx(struct Map_info *Map, int mode)
{
    char buf[500], file_path[2000];
    int err;
    struct Coor_info CInfo;
    struct Plus_head *Plus;
    struct stat info;

    G_debug(1, "Vect_open_sidx(): name = %s mapset= %s mode = %s", Map->name,
	    Map->mapset, mode == 0 ? "old" : (mode == 1 ? "update" : "new"));

    if (Map->plus.Spidx_built == 1) {
	G_warning("Spatial index already opened");
	return 0;
    }

    Plus = &(Map->plus);

    dig_file_init(&(Map->plus.spidx_fp));

    if (mode < 2) {
	sprintf(buf, "%s/%s", GV_DIRECTORY, Map->name);
	G__file_name(file_path, buf, GV_SIDX_ELEMENT, Map->mapset);

	if (stat(file_path, &info) != 0)	/* does not exist */
	    return 1;

	Map->plus.spidx_fp.file =
	    G_fopen_old(buf, GV_SIDX_ELEMENT, Map->mapset);

	if (Map->plus.spidx_fp.file == NULL) {	/* sidx file is not available */
	    G_debug(1, "Cannot open spatial index file for vector '%s@%s'.",
		    Map->name, Map->mapset);
	    return -1;
	}

	/* get coor info */
	Vect_coor_info(Map, &CInfo);

	/* initialize spatial index */
	Map->plus.Spidx_new = 0;

	dig_spidx_init(Plus);

	/* load head */
	if (dig_Rd_spidx_head(&(Map->plus.spidx_fp), Plus) == -1) {
	    fclose(Map->plus.spidx_fp.file);
	    return -1;
	}

	G_debug(1, "Sidx head: coor size = %lu, coor mtime = %ld",
		(unsigned long)Plus->coor_size, Plus->coor_mtime);

	/* do checks */
	err = 0;
	if (CInfo.size != Plus->coor_size) {
	    G_warning(_("Size of 'coor' file differs from value saved in sidx file"));
	    err = 1;
	}
	/* Do not check mtime because mtime is changed by copy */
	/*
	   if ( CInfo.mtime != Plus->coor_mtime ) {
	   G_warning ( "Time of last modification for 'coor' file differs from value saved in topo file.\n");
	   err = 1;
	   }
	 */
	if (err) {
	    G_warning(_("Please rebuild topology for vector map <%s@%s>"),
		      Map->name, Map->mapset);
	    fclose(Map->plus.spidx_fp.file);
	    return -1;
	}
    }

    if (mode) {
	/* open new spatial index */
	Map->plus.Spidx_new = 1;

	dig_spidx_init(Plus);

	if (mode == 1) {
	    /* load spatial index for update */
	    if (dig_Rd_spidx(&(Map->plus.spidx_fp), Plus) == -1) {
		fclose(Map->plus.spidx_fp.file);
		return -1;
	    }
	}
    }

    Map->plus.Spidx_built = 1;

    return 0;
}
