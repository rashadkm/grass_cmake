#include <grass/gis.h>
#include <grass/raster.h>

#include "../gis/G.h"
#include "R.h"

/*!
 * \brief Number of rows in active window.
 *
 * This routine returns the number of rows in the active module window. 
 * Before raster files can be read or written, it is necessary to
 * known how many rows are in the active window. For example:
 \code  
int nrows, cols;
int row, col;

nrows = Rast_window_rows();
ncols = Rast_window_cols();
for (row = 0; row < nrows; row++) {
    // read row ...
    for (col = 0; col < ncols; col++) {
        // process col ...
    }
}
 \endcode 
 *
 * \return number of rows
 */
int Rast_window_rows(void)
{
    G__init_window();

    return G__.window.rows;
}

/*!
 * \brief Number of columns in active window.
 *
 * These routines return the number of rows and columns (respectively)
 * in the active module region. Before raster maps can be read or
 * written, it is necessary to known how many rows and columns are in
 * the active region. For example:
 *
 \code  
int nrows, cols;
int row, col;

nrows = Rast_window_rows();
ncols = Rast_window_cols();
for (row = 0; row < nrows; row++) {
    // read row ...
    for (col = 0; col < ncols; col++) {
        // process col ...
    }
}
 \endcode 
 *
 * \return number of columns
 */
int Rast_window_cols(void)
{
    G__init_window();

    return G__.window.cols;
}

/*!
 * \brief Northing to row.
 *
 * Converts a <i>north</i>ing relative to a <i>window</i> to a row.

 * <b>Note:</b> The result is a double. Casting it to an integer will 
 * give the row number.
 *
 * \param north northing value
 * \param window pointer to Cell_head
 *
 * \return row number
 */

double Rast_northing_to_row(double north, const struct Cell_head *window)
{
    return (window->north - north) / window->ns_res;
}


/*!
 * \brief Easting to column.
 *
 * Converts <i>east</i> relative to a <i>window</i> to a column.

 * <b>Note:</b> The result is a <i>double</i>. Casting it to an 
 * <i>int</i> will give the column number.
 *
 * \param east east coordinate
 * \param window pointer to Cell_head
 *
 * \return column number
 */

double Rast_easting_to_col(double east, const struct Cell_head *window)
{
    east = G_adjust_easting(east, window);

    return (east - window->west) / window->ew_res;
}

/*!
 * \brief Row to northing.
 *
 * Converts a <i>row</i> relative to a <i>window</i> to a
 * northing.

 * <b>Note:</b> row is a double:
 *  - row+0.0 will return the northing for the northern edge of the row.
 *  - row+0.5 will return the northing for the center of the row.
 *  - row+1.0 will return the northing for the southern edge of the row.
 *
 * <b>Note:</b> The result is a <i>double</i>. Casting it to an
 * <i>int</i> will give the column number.
 *
 * \param row row number
 * \param[in] window pointer to Cell_head
 *
 * \return north coordinate
 */
double Rast_row_to_northing(double row, const struct Cell_head *window)
{
    return window->north - row * window->ns_res;
}

/*!
 * \brief Column to easting.
 *
 * Converts a <i>col</i> relative to a <i>window</i> to an easting.
 *
 * <b>Note:</b> <i>col</i> is a <i>double</i>:
 *  - col+0.0 will return the easting for the western edge of the column.
 *  - col+0.5 will return the easting for the center of the column.
 *  - col+1.0 will return the easting for the eastern edge of the column.
 *
 * \param col column number
 * \param[in] window pointer to Cell_head
 *
 * \return east coordinate
 */
double Rast_col_to_easting(double col, const struct Cell_head *window)
{
    return window->west + col * window->ew_res;
}

