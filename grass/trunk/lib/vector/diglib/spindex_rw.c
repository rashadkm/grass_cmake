/*!
  \file diglib/spindex.c
 
  \brief Vector library - spatial index - read/write (lower level functions)
  
  Lower level functions for reading/writing/manipulating vectors.
  
  (C) 2001-2009 by the GRASS Development Team
  
  This program is free software under the GNU General Public License
  (>=v2). Read the file COPYING that comes with GRASS for details.
  
  \author Original author CERL, probably Dave Gerdes
  \author Update to GRASS 5.7 Radim Blazek
*/

#include <grass/config.h>
#include <sys/types.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>

/*!
  \brief Write spatial index to the file
  
  \param[in,out] fp pointer to GVFILE
  \param ptr pointer to Plus_head structure

  \return 0 on success
  \return -1 on error
*/
static int dig_Wr_spindx_head(GVFILE * fp, struct Plus_head *ptr)
{
    unsigned char buf[5];
    long length = 42;

    dig_rewind(fp);
    dig_set_cur_port(&(ptr->spidx_port));

    /* bytes 1 - 5 */
    buf[0] = GV_SIDX_VER_MAJOR;
    buf[1] = GV_SIDX_VER_MINOR;
    buf[2] = GV_SIDX_EARLIEST_MAJOR;
    buf[3] = GV_SIDX_EARLIEST_MINOR;
    buf[4] = ptr->spidx_port.byte_order;
    if (0 >= dig__fwrite_port_C((const char *)buf, 5, fp))
	return (-1);

    /* get required offset size */
    if (ptr->off_t_size == 0) {
	/* should not happen, topo is written first */
	if (ptr->coor_size > (off_t)PORT_LONG_MAX)
	    ptr->off_t_size = 8;
	else
	    ptr->off_t_size = 4;
    }

    /* adjust header size for large files */
    if (ptr->off_t_size == 8) {
	/* 7 offset values and coor file size: add 8 * 4 */
	length += 32;
    }

    /* bytes 6 - 9 : header size */
    if (0 >= dig__fwrite_port_L(&length, 1, fp))
	return (0);

    /* byte 10 : dimension 2D or 3D */
    buf[0] = ptr->spidx_with_z;
    if (0 >= dig__fwrite_port_C((const char*) buf, 1, fp))
	return (-1);

    /* bytes 11 - 38 (large files 11 - 66) : Offsets */
    if (0 >= dig__fwrite_port_O(&(ptr->Node_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fwrite_port_O(&(ptr->Edge_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fwrite_port_O(&(ptr->Line_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fwrite_port_O(&(ptr->Area_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fwrite_port_O(&(ptr->Isle_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fwrite_port_O(&(ptr->Volume_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fwrite_port_O(&(ptr->Hole_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);

    G_debug(3, "spidx offset node = %lu line = %lu, area = %lu isle = %lu",
	    (long unsigned) ptr->Node_spidx_offset, (long unsigned) ptr->Line_spidx_offset,
	    (long unsigned) ptr->Area_spidx_offset, (long unsigned) ptr->Isle_spidx_offset);

    /* bytes 39 - 42 (large files 67 - 74) : Offsets */
    if (0 >= dig__fwrite_port_O(&(ptr->coor_size), 1, fp, ptr->off_t_size))
	return (-1);

    G_debug(2, "spidx body offset %lu", (long unsigned) dig_ftell(fp));

    return (0);
}

/*!
  \brief Read spatial index to the file
  
  \param fp pointer to GVFILE
  \param[in,out] ptr pointer to Plus_head structure

  \return 0 on success
  \return -1 on error
*/
static int dig_Rd_spindx_head(GVFILE * fp, struct Plus_head *ptr)
{
    unsigned char buf[5];
    int byte_order;
    off_t coor_size;

    dig_rewind(fp);

    /* bytes 1 - 5 */
    if (0 >= dig__fread_port_C((char*) buf, 5, fp))
	return (-1);
    ptr->spidx_Version_Major = buf[0];
    ptr->spidx_Version_Minor = buf[1];
    ptr->spidx_Back_Major = buf[2];
    ptr->spidx_Back_Minor = buf[3];
    byte_order = buf[4];

    G_debug(2, "Sidx header: file version %d.%d , supported from GRASS version %d.%d",
	    ptr->spidx_Version_Major, ptr->spidx_Version_Minor,
	    ptr->spidx_Back_Major, ptr->spidx_Back_Minor);

    G_debug(2, "  byte order %d", byte_order);

    /* check version numbers */
    if (ptr->spidx_Version_Major > GV_SIDX_VER_MAJOR ||
	ptr->spidx_Version_Minor > GV_SIDX_VER_MINOR) {
	/* The file was created by GRASS library with higher version than this one */

	if (ptr->spidx_Back_Major > GV_SIDX_VER_MAJOR ||
	    ptr->spidx_Back_Minor > GV_SIDX_VER_MINOR) {
	    /* This version of GRASS lib is lower than the oldest which can read this format */
	    G_fatal_error(_("Spatial index format version %d.%d is not "
			    "supported by this release."
			    " Try to rebuild topology or upgrade GRASS."),
			    ptr->spidx_Version_Major, ptr->spidx_Version_Minor);
	    return (-1);
	}

	G_warning(_("Your GRASS version does not fully support "
		    "spatial index format %d.%d of the vector."
		    " Consider to rebuild topology or upgrade GRASS."),
		  ptr->spidx_Version_Major, ptr->spidx_Version_Minor);
    }

    dig_init_portable(&(ptr->spidx_port), byte_order);
    dig_set_cur_port(&(ptr->spidx_port));

    /* bytes 6 - 9 : header size */
    if (0 >= dig__fread_port_L(&(ptr->spidx_head_size), 1, fp))
	return (-1);
    G_debug(2, "  header size %ld", ptr->spidx_head_size);

    /* byte 10 : dimension 2D or 3D */
    if (0 >= dig__fread_port_C((char *)buf, 1, fp))
	return (-1);
    ptr->spidx_with_z = buf[0];
    G_debug(2, "  with_z %d", ptr->spidx_with_z);

   /* get required offset size */
    if (ptr->off_t_size == 0) {
	/* should not happen, topo is opened first */
	if (ptr->coor_size > (off_t)PORT_LONG_MAX)
	    ptr->off_t_size = 8;
	else
	    ptr->off_t_size = 4;
    }
    /* as long as topo is always opened first, off_t size check is not needed here */

    /* bytes 11 - 38 (large files 11 - 66) : Offsets */
    if (0 >= dig__fread_port_O(&(ptr->Node_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fread_port_O(&(ptr->Edge_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fread_port_O(&(ptr->Line_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fread_port_O(&(ptr->Area_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fread_port_O(&(ptr->Isle_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fread_port_O(&(ptr->Volume_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);
    if (0 >= dig__fread_port_O(&(ptr->Hole_spidx_offset), 1, fp, ptr->off_t_size))
	return (-1);

    /* bytes 39 - 42 (large files 67 - 74) : Offsets */
    if (0 >= dig__fread_port_O(&coor_size, 1, fp, ptr->off_t_size))
	return (-1);
    G_debug(2, "  coor size %lu", (long unsigned) coor_size);

    dig_fseek(fp, ptr->spidx_head_size, SEEK_SET);

    return (0);
}

static int rtree_dump_node(FILE *, const struct Node *, int);

/*!
  \brief Dump R-tree branch to the file

  \param fp pointer to FILE
  \param b pointer to Branch structure
  \param with_z non-zero value for 3D vector data
  \param level level value

  \return 0
*/
static int rtree_dump_branch(FILE * fp, const struct Branch *b, int with_z, int level)
{
    const struct Rect *r;

    r = &(b->rect);

    if (level == 0)
	fprintf(fp, "  id = %d ", (int)b->child);

    fprintf(fp, " %f %f %f %f %f %f\n", r->boundary[0], r->boundary[1],
	    r->boundary[2], r->boundary[3], r->boundary[4], r->boundary[5]);

    if (level > 0) {
	rtree_dump_node(fp, b->child, with_z);
    }
    return 0;
}

/*!
  \brief Dump R-tree node to the file

  \param fp pointer to FILE
  \param n pointer to Node structure
  \param with_z non-zero value for 3D vector data

  \return 0
*/
int rtree_dump_node(FILE * fp, const struct Node *n, int with_z)
{
    int i, nn;

    fprintf(fp, "Node level=%d  count=%d\n", n->level, n->count);

    if (n->level > 0)
	nn = NODECARD;
    else
	nn = LEAFCARD;

    for (i = 0; i < nn; i++) {
	if (n->branch[i].child) {
	    fprintf(fp, "  Branch %d", i);
	    rtree_dump_branch(fp, &n->branch[i], with_z, n->level);
	}
    }

    return 0;
}

static int rtree_write_node(GVFILE *, const struct Node *, int);

/*!
  \brief Write R-tree node to the file

  \param fp pointer to GVFILE
  \param b pointer to Branch structure
  \param with_z non-zero value for 3D vector data
  \param level level value

  \return -1 on error
  \return 0 on success
*/
static int rtree_write_branch(GVFILE * fp, const struct Branch *b, int with_z, int level)
{
    const struct Rect *r;
    int i;

    r = &(b->rect);

    /* rectangle */
    if (with_z) {
	if (0 >= dig__fwrite_port_D(&(r->boundary[0]), 6, fp))
	    return (-1);
    }
    else {
	if (0 >= dig__fwrite_port_D(&(r->boundary[0]), 2, fp))
	    return (-1);
	if (0 >= dig__fwrite_port_D(&(r->boundary[3]), 2, fp))
	    return (-1);
    }
    if (level == 0) {		/* write data (element id) */
	i = (int) b->child;
	if (0 >= dig__fwrite_port_I(&i, 1, fp))
	    return (-1);
    }
    else {
	rtree_write_node(fp, b->child, with_z);
    }
    return 0;
}

/*!
  \brief Write R-tree node to the file

  \param fp pointer to GVFILE
  \param n pointer to Node structure
  \param with_z non-zero value for 3D vector data
  
  \return -1 on error
  \return 0 on success
*/
int rtree_write_node(GVFILE * fp, const struct Node *n, int with_z)
{
    int i, nn;

    /* level ( 0 = leaf, data ) */
    if (0 >= dig__fwrite_port_I(&(n->level), 1, fp))
	return (-1);

    /* count */
    if (0 >= dig__fwrite_port_I(&(n->count), 1, fp))
	return (-1);

    if (n->level > 0)
	nn = NODECARD;
    else
	nn = LEAFCARD;
    for (i = 0; i < nn; i++) {
	if (n->branch[i].child) {
	    rtree_write_branch(fp, &n->branch[i], with_z, n->level);
	}
    }

    return 0;
}

static int rtree_read_node(GVFILE * fp, struct Node *n, int with_z);

/*!
  \brief Read R-tree branch from the file

  \param fp pointer to GVFILE
  \param b pointer to Branch structure
  \param with_z non-zero value for 3D vector data
  \param level level value

  \return -1 on error
  \return 0 on success
*/
static int rtree_read_branch(GVFILE * fp, struct Branch *b, int with_z, int level)
{
    struct Rect *r;
    int i;

    G_debug(3, "rtree_read_branch()");

    r = &(b->rect);

    /* rectangle */
    if (with_z) {
	if (0 >= dig__fread_port_D(&(r->boundary[0]), 6, fp))
	    return (-1);
    }
    else {
	if (0 >= dig__fread_port_D(&(r->boundary[0]), 2, fp))
	    return (-1);
	if (0 >= dig__fread_port_D(&(r->boundary[3]), 2, fp))
	    return (-1);
	r->boundary[2] = 0;
	r->boundary[5] = 0;
    }

    if (level == 0) {		/* read data (element id) */
	if (0 >= dig__fread_port_I(&i, 1, fp))
	    return (-1);
	b->child = (struct Node *)i;
    }
    else {
	/* create new node */
	b->child = RTreeNewNode();
	rtree_read_node(fp, b->child, with_z);
    }
    return 0;
}

/*!
  \brief Read R-tree node from the file

  \param fp pointer to GVFILE
  \param n pointer to Node structure
  \param with_z non-zero value for 3D vector data
  \param level level value

  \return -1 on error
  \return 0 on success
*/
int rtree_read_node(GVFILE * fp, struct Node *n, int with_z)
{
    int level, count, i;

    G_debug(3, "rtree_read_node()");

    /* level ( 0 = leaf, data ) */
    if (0 >= dig__fread_port_I(&level, 1, fp))
	return (-1);
    n->level = level;

    /* count */
    if (0 >= dig__fread_port_I(&count, 1, fp))
	return (-1);
    n->count = count;

    for (i = 0; i < count; i++) {
	if (0 > rtree_read_branch(fp, &n->branch[i], with_z, level))
	    return (-1);
    }

    return 0;
}

/*!
  \brief Write spatial index to the file

  \param[out] fp pointer to GVFILE
  \param Plus pointer to Plus_head structure

  \return 0
*/
int dig_write_spidx(GVFILE * fp, struct Plus_head *Plus)
{
    dig_set_cur_port(&(Plus->spidx_port));
    dig_rewind(fp);

    dig_Wr_spindx_head(fp, Plus);

    Plus->Node_spidx_offset = dig_ftell(fp);
    rtree_write_node(fp, Plus->Node_spidx, Plus->with_z);

    Plus->Line_spidx_offset = dig_ftell(fp);
    rtree_write_node(fp, Plus->Line_spidx, Plus->with_z);

    Plus->Area_spidx_offset = dig_ftell(fp);
    rtree_write_node(fp, Plus->Area_spidx, Plus->with_z);

    Plus->Isle_spidx_offset = dig_ftell(fp);
    rtree_write_node(fp, Plus->Isle_spidx, Plus->with_z);

    dig_rewind(fp);
    dig_Wr_spindx_head(fp, Plus);	/* rewrite with offsets */

    return 0;
}

/*!
  \brief Read spatial index from the file

  \param fp pointer to GVFILE
  \param[in,out] Plus pointer to Plus_head structure

  \return 0
*/
int dig_read_spidx(GVFILE * fp, struct Plus_head *Plus)
{
    G_debug(1, "dig_read_spindx()");

    /* TODO: free old tree */
    dig_spidx_init(Plus);

    dig_rewind(fp);
    dig_Rd_spindx_head(fp, Plus);
    dig_set_cur_port(&(Plus->spidx_port));

    dig_fseek(fp, Plus->Node_spidx_offset, 0);
    rtree_read_node(fp, Plus->Node_spidx, Plus->with_z);

    dig_fseek(fp, Plus->Line_spidx_offset, 0);
    rtree_read_node(fp, Plus->Line_spidx, Plus->with_z);

    dig_fseek(fp, Plus->Area_spidx_offset, 0);
    rtree_read_node(fp, Plus->Area_spidx, Plus->with_z);

    dig_fseek(fp, Plus->Isle_spidx_offset, 0);
    rtree_read_node(fp, Plus->Isle_spidx, Plus->with_z);

    return 0;
}

/*!
  \brief Dump spatial index

  \param[out] fp pointe to FILE
  \param Plus pointer to Plus_head structure

  \return 0
*/
int dig_dump_spidx(FILE * fp, const struct Plus_head *Plus)
{

    fprintf(fp, "Nodes\n");
    rtree_dump_node(fp, Plus->Node_spidx, Plus->with_z);

    fprintf(fp, "Lines\n");
    rtree_dump_node(fp, Plus->Line_spidx, Plus->with_z);

    fprintf(fp, "Areas\n");
    rtree_dump_node(fp, Plus->Area_spidx, Plus->with_z);

    fprintf(fp, "Isles\n");
    rtree_dump_node(fp, Plus->Isle_spidx, Plus->with_z);

    return 0;
}
