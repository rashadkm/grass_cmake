#include "Gwater.h"
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>


int do_cum(void)
{
    SHORT r, c, dr, dc;
    CELL is_swale, value, valued, aspect;
    int killer, threshold, count;
    SHORT asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    SHORT asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    G_message(_("SECTION 3: Accumulating Surface Flow with SFD."));

    count = 0;
    if (bas_thres <= 0)
	threshold = 60;
    else
	threshold = bas_thres;
    while (first_cum != -1) {
	G_percent(count++, do_points, 2);
	killer = first_cum;
	first_cum = astar_pts[killer].nxt;
	r = astar_pts[killer].r;
	c = astar_pts[killer].c;
	aspect = asp[SEG_INDEX(asp_seg, r, c)];
	if (aspect) {
	    dr = r + asp_r[ABS(aspect)];
	    dc = c + asp_c[ABS(aspect)];
	}
	else
	    dr = dc = -1;
	if (dr >= 0 && dr < nrows && dc >= 0 && dc < ncols) { /* if ((dr = astar_pts[killer].downr) > -1) { */
	    value = wat[SEG_INDEX(wat_seg, r, c)];
	    if ((int)(ABS(value) + 0.5) >= threshold)
		FLAG_SET(swale, r, c);
	    valued = wat[SEG_INDEX(wat_seg, dr, dc)];
	    if (value > 0) {
		if (valued > 0)
		    valued += value;
		else
		    valued -= value;
	    }
	    else {
		if (valued < 0)
		    valued += value;
		else
		    valued = value - valued;
	    }
	    wat[SEG_INDEX(wat_seg, dr, dc)] = valued;
	    valued = ABS(valued) + 0.5;
	    is_swale = FLAG_GET(swale, r, c);
	    /* update asp for depression */
	    if (is_swale && pit_flag) {
		if (aspect > 0 && asp[SEG_INDEX(asp_seg, dr, dc)] == 0) {
		    aspect = -aspect;
		    asp[SEG_INDEX(asp_seg, r, c)] = aspect;
		}
	    }
	    if (is_swale || ((int)valued) >= threshold) {
		FLAG_SET(swale, dr, dc);
	    }
	    else {
		if (er_flag && !is_swale)
		    slope_length(r, c, dr, dc);
	    }
	}
    }
    G_percent(count, do_points, 1);	/* finish it */
    G_free(astar_pts);

    return 0;
}

/***************************************
 * 
 * MFD references
 * 
 * original:
 * Quinn, P., Beven, K., Chevallier, P., and Planchon, 0. 1991. 
 * The prediction of hillslope flow paths for distributed hydrological 
 * modelling using digital terrain models, Hydrol. Process., 5, 59-79.
 * 
 * modified by Holmgren (1994):
 * Holmgren, P. 1994. Multiple flow direction algorithms for runoff 
 * modelling in grid based elevation models: an empirical evaluation
 * Hydrol. Process., 8, 327-334.
 * 
 * implemented here:
 * Holmgren (1994) with modifications to honour A * path in order to get
 * out of depressions and across obstacles with gracefull flow convergence
 * before depressions/obstacles and gracefull flow divergence after 
 * depressions/obstacles
 * 
 * ************************************/

int do_cum_mfd(void)
{
    int r, c, dr, dc;
    CELL is_swale;
    DCELL value, valued;
    int killer, threshold, count;

    /* MFD */
    int mfd_cells, stream_cells, swale_cells, astar_not_set, is_null;
    double *dist_to_nbr, *weight, sum_weight, max_weight;
    int r_nbr, c_nbr, r_max, c_max, ct_dir, np_side;
    double dx, dy;
    CELL ele, ele_nbr, aspect, is_worked;
    double prop, max_acc;
    int workedon, edge;
    SHORT asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    SHORT asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    G_message(_("SECTION 3: Accumulating Surface Flow with MFD."));
    G_debug(1, "MFD convergence factor set to %d.", c_fac);

    /* distances to neighbours */
    dist_to_nbr = (double *)G_malloc(sides * sizeof(double));
    weight = (double *)G_malloc(sides * sizeof(double));

    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	/* get r, c (r_nbr, c_nbr) for neighbours */
	r_nbr = nextdr[ct_dir];
	c_nbr = nextdc[ct_dir];
	/* account for rare cases when ns_res != ew_res */
	dy = ABS(r_nbr) * window.ns_res;
	dx = ABS(c_nbr) * window.ew_res;
	if (ct_dir < 4)
	    dist_to_nbr[ct_dir] = dx + dy;
	else
	    dist_to_nbr[ct_dir] = sqrt(dx * dx + dy * dy);
    }

    flag_clear_all(worked);
    workedon = 0;

    count = 0;
    if (bas_thres <= 0)
	threshold = 60;
    else
	threshold = bas_thres;

    while (first_cum != -1) {
	G_percent(count++, do_points, 2);
	killer = first_cum;
	first_cum = astar_pts[killer].nxt;
	r = astar_pts[killer].r;
	c = astar_pts[killer].c;
	aspect = asp[SEG_INDEX(asp_seg, r, c)];
	if (aspect) {
	    dr = r + asp_r[ABS(aspect)];
	    dc = c + asp_c[ABS(aspect)];
	}
	else
	    dr = dc = -1;
	if (dr >= 0 && dr < nrows && dc >= 0 && dc < ncols) { /* if ((dr = astar_pts[killer].downr) > -1) { */
	    value = wat[SEG_INDEX(wat_seg, r, c)];
	    valued = wat[SEG_INDEX(wat_seg, dr, dc)];

	    r_max = dr;
	    c_max = dc;

	    /* get weights */
	    max_weight = 0;
	    sum_weight = 0;
	    np_side = -1;
	    mfd_cells = 0;
	    stream_cells = 0;
	    swale_cells = 0;
	    astar_not_set = 1;
	    ele = alt[SEG_INDEX(alt_seg, r, c)];
	    is_null = 0;
	    edge = 0;
	    /* this loop is needed to get the sum of weights */
	    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
		/* get r, c (r_nbr, c_nbr) for neighbours */
		r_nbr = r + nextdr[ct_dir];
		c_nbr = c + nextdc[ct_dir];
		weight[ct_dir] = -1;
		/* check that neighbour is within region */
		if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 &&
		    c_nbr < ncols) {

		    /* check for swale or stream cells */
		    is_swale = FLAG_GET(swale, r_nbr, c_nbr);
		    if (is_swale)
			swale_cells++;
		    valued = wat[SEG_INDEX(wat_seg, r_nbr, c_nbr)];
		    if ((ABS(valued) + 0.5) >= threshold)
			stream_cells++;

		    is_worked = FLAG_GET(worked, r_nbr, c_nbr);
		    if (is_worked == 0) {
			ele_nbr = alt[SEG_INDEX(alt_seg, r_nbr, c_nbr)];
			is_null = Rast_is_c_null_value(&ele_nbr);
			edge = is_null;
			if (!is_null && ele_nbr <= ele) {
			    if (ele_nbr < ele) {
				weight[ct_dir] =
				    mfd_pow(((ele -
					      ele_nbr) / dist_to_nbr[ct_dir]),
					    c_fac);
			    }
			    if (ele_nbr == ele) {
				weight[ct_dir] =
				    mfd_pow((0.5 / dist_to_nbr[ct_dir]),
					    c_fac);
			    }
			    sum_weight += weight[ct_dir];
			    mfd_cells++;

			    if (weight[ct_dir] > max_weight) {
				max_weight = weight[ct_dir];
			    }

			    if (dr == r_nbr && dc == c_nbr) {
				astar_not_set = 0;
			    }
			}
		    }
		    if (dr == r_nbr && dc == c_nbr)
			np_side = ct_dir;
		}
		else
		    edge = 1;
		if (edge)
		    break;
	    }
	    /* do not distribute flow along edges, this causes artifacts */
	    if (edge) {
		is_swale = FLAG_GET(swale, r, c);
		if (is_swale && aspect > 0) {
		    aspect = -1 * drain[r - r_nbr + 1][c - c_nbr + 1];
		    asp[SEG_INDEX(asp_seg, r, c)] = aspect;
		}
		continue;
	    }

	    /* honour A * path 
	     * mfd_cells == 0: fine, SFD along A * path
	     * mfd_cells == 1 && astar_not_set == 0: fine, SFD along A * path
	     * mfd_cells > 0 && astar_not_set == 1: A * path not included, add to mfd_cells
	     */

	    /* MFD, A * path not included, add to mfd_cells */
	    if (mfd_cells > 0 && astar_not_set == 1) {
		mfd_cells++;
		sum_weight += max_weight;
		weight[np_side] = max_weight;
	    }

	    /* set flow accumulation for neighbours */
	    max_acc = -1;

	    if (mfd_cells > 1) {
		prop = 0.0;
		for (ct_dir = 0; ct_dir < sides; ct_dir++) {
		    /* get r, c (r_nbr, c_nbr) for neighbours */
		    r_nbr = r + nextdr[ct_dir];
		    c_nbr = c + nextdc[ct_dir];

		    /* check that neighbour is within region */
		    if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 &&
			c_nbr < ncols && weight[ct_dir] > -0.5) {
			is_worked = FLAG_GET(worked, r_nbr, c_nbr);
			if (is_worked == 0) {

			    weight[ct_dir] = weight[ct_dir] / sum_weight;
			    /* check everything sums up to 1.0 */
			    prop += weight[ct_dir];

			    valued = wat[SEG_INDEX(wat_seg, r_nbr, c_nbr)];
			    if (value > 0) {
				if (valued > 0)
				    valued += value * weight[ct_dir];
				else
				    valued -= value * weight[ct_dir];
			    }
			    else {
				if (valued < 0)
				    valued += value * weight[ct_dir];
				else
				    valued = value * weight[ct_dir] - valued;
			    }
			    wat[SEG_INDEX(wat_seg, r_nbr, c_nbr)] = valued;

			    /* get main drainage direction */
			    if (ABS(valued) >= max_acc) {
				max_acc = ABS(valued);
				r_max = r_nbr;
				c_max = c_nbr;
			    }
			}
			else if (ct_dir == np_side) {
			    /* check for consistency with A * path */
			    workedon++;
			}
		    }
		}
		if (ABS(prop - 1.0) > 5E-6f) {
		    G_warning(_("MFD: cumulative proportion of flow distribution not 1.0 but %f"),
			      prop);
		}
	    }

	    if (mfd_cells < 2) {
		valued = wat[SEG_INDEX(wat_seg, dr, dc)];
		if (value > 0) {
		    if (valued > 0)
			valued += value;
		    else
			valued -= value;
		}
		else {
		    if (valued < 0)
			valued += value;
		    else
			valued = value - valued;
		}
		wat[SEG_INDEX(wat_seg, dr, dc)] = valued;
	    }

	    /* update asp */
	    if (dr != r_max || dc != c_max) {
		aspect = drain[r - r_max + 1][c - c_max + 1];
		if (asp[SEG_INDEX(asp_seg, r, c)] < 0)
		    aspect = -aspect;
		asp[SEG_INDEX(asp_seg, r, c)] = aspect;
	    }
	    is_swale = FLAG_GET(swale, r, c);
	    /* update asp for depression */
	    if (is_swale && pit_flag) {
		if (aspect > 0 && asp[SEG_INDEX(asp_seg, r_max, c_max)] == 0) {
		    aspect = -aspect;
		    asp[SEG_INDEX(asp_seg, r, c)] = aspect;
		}
	    }
	    /* start new stream */
	    value = ABS(value) + 0.5;
	    if (!is_swale && (int)value >= threshold && stream_cells < 1 &&
		swale_cells < 1) {
		FLAG_SET(swale, r, c);
		is_swale = 1;
	    }
	    /* continue stream */
	    if (is_swale) {
		FLAG_SET(swale, r_max, c_max);
	    }
	    else {
		if (er_flag && !is_swale)
		    slope_length(r, c, r_max, c_max);
	    }
	    FLAG_SET(worked, r, c);
	}
    }
    G_percent(count, do_points, 1);	/* finish it */
    if (workedon)
	G_warning(_("MFD: A * path already processed when distributing flow: %d of %d cells"),
		  workedon, do_points);

    G_free(astar_pts);

    flag_destroy(worked);

    G_free(dist_to_nbr);
    G_free(weight);

    return 0;
}

double mfd_pow(double base, int exp)
{
    int x;
    double result;

    result = base;
    if (exp == 1)
	return result;

    for (x = 2; x <= exp; x++) {
	result *= base;
    }
    return result;
}
