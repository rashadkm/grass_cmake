/*!
 * \file gis/set_window.c
 *
 * \brief GIS Library - Set window (map region)
 *
 * (C) 2001-2009 by the GRASS Development Team
 *
 * This program is free software under the GNU General Public License
 * (>=v2). Read the file COPYING that comes with GRASS for details.
 *
 * \author Original author CERL
 */

#include <grass/gis.h>
#include <grass/glocale.h>
#include "G.h"

/*!
 * \brief Get the current working window (region)
 *
 * The current working window values are returned in the structure
 * <i>window</i>.
 *
 * \param[in,out] window window structure to be set
 */
void G_get_set_window(struct Cell_head *window)
{
    G__init_window();
    G_copy(window, &G__.window, sizeof(*window));
}


/*!
 * \brief Establishes 'window' as the current working window.
 * 
 * Any opened cell files has its file-to-window mapping reworked.
 *
 * \param window window to become operative window
 * 
 * \return -1 on error
 * \return  1 on success
 */
int G_set_window(struct Cell_head *window)
{
    int i;
    int maskfd;
    const char *err;

    /* adjust window, check for valid window */
    /* adjust the real one, not a copy
       G_copy (&twindow, window, sizeof(struct Cell_head));
       window = &twindow;
     */

    if ((err = G_adjust_Cell_head(window, 0, 0))) {
	G_warning("G_set_window(): %s", err);
	return -1;
    }

    /* except for MASK, cell files open for read must have same projection
     * and zone as new window
     */
    maskfd = G__.auto_mask > 0 ? G__.mask_fd : -1;
    for (i = 0; i < G__.fileinfo_count; i++) {
	struct fileinfo *fcb = &G__.fileinfo[i];
	if (fcb->open_mode == OPEN_OLD) {
	    if (fcb->cellhd.zone == window->zone &&
		fcb->cellhd.proj == window->proj)
		continue;
	    if (i != maskfd) {
		G_warning(_("G_set_window(): projection/zone differs from that of "
			    "currently open raster maps"));
		return -1;
	    }
	}
    }

    /* close the mask */
    if (G__.auto_mask > 0) {
	G_close_cell(maskfd);
	/* G_free (G__.mask_buf); */
	G__.mask_fd = -1;
	G__.auto_mask = -1;	/* turn off masking */
    }

    /* copy the window to the current window */
    G_copy((char *)&G__.window, (char *)window, sizeof(*window));

    G__.window_set = 1;

    /* now for each possible open cell file, recreate the window mapping */
    /*
     * also the memory for reading and writing must be reallocated for all opened
     * cell files
     */
    for (i = 0; i < G__.fileinfo_count; i++) {
	struct fileinfo *fcb = &G__.fileinfo[i];

	if (fcb->open_mode != OPEN_OLD &&
	    fcb->open_mode != OPEN_NEW_UNCOMPRESSED &&
	    fcb->open_mode != OPEN_NEW_COMPRESSED)
	    continue;

	if (fcb->open_mode == OPEN_OLD)
	    G__create_window_mapping(i);
	/* code commented 10/1999 due to problems */
#if 0
	else
	{
	    /* opened for writing */
	    G_free (fcb->data);
	    fcb->data = (unsigned char *) G_calloc (G__.window.cols,
						    G_raster_size(fcb->map_type));
	}

	/* allocate null bitstream buffers for reading/writing null rows */
	for (j=0;j< NULL_ROWS_INMEM; j++)
	{
	    G_free (fcb->NULL_ROWS[j]);
	    fcb->NULL_ROWS[j] = G__allocate_null_bits(G__.window.cols);
	}


	/* initialize : no NULL rows in memory */
	fcb->min_null_row = (-1) * NULL_ROWS_INMEM;
	if(fcb->null_cur_row > 0)
	{
	  G_warning(_("Calling G_set_window() in the middle of writing map %s"), 
		    fcb->name);
	    fcb->null_cur_row = 0;
	}
#endif
    }

    /* turn masking (back) on if necessary */
    G__check_for_auto_masking();

    /* we want the number of bytes per cell to be maximum
       so that there is enough memory for reading and writing rows */

    return 1;
}
