#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gis.h"
#include "Vect.h"
#include "conv.h"
#include "local_proto.h"

int read_line ( GVFILE *, struct line_pnts *);

/* read old 3.0 or 4.0 dig file into array 
   returns number of elements read into array
   or -1 on error */
int read_dig ( FILE *Digin, struct Map_info *Mapout, 
               struct Line **plines , int endian, int att )
{
    char	      buf[100];
    struct dig_head   In_head;
    int               lalloc, line=0, type, portable=1;
    int    npoints=0, nlines=0, nbounds=0;     
    int    ndpoints=0, ndlines=0, ndbounds=0, nunknown=0;         
    struct Line *lines;
    struct line_pnts *nline;
    struct line_cats *cat_out;
    double dbuf;
    int    ibuf;
    long   lbuf;
    GVFILE gvf;

    dig_file_init ( &gvf );
    gvf.file = Digin;
    
    Vect__init_head (Mapout);
    /* set conversion matrices */
    dig_init_portable (&(In_head.port), endian);

    /* Version 3 dig files were not portable and some version 4 
     * files may be also non portable */

    fprintf(stdout,"Reading dig file...\n");

    /* read and copy head */
    dig_fseek (&gvf, 0L, SEEK_SET) ;   /* set to beginning */

    if (0 >= dig__fread_port_C ( buf, DIG4_ORGAN_LEN, &gvf)) return -1;
    buf[DIG4_ORGAN_LEN-1] = '\0'; 
    Vect_set_organization ( Mapout, buf );

    if (0 >= dig__fread_port_C ( buf, DIG4_DATE_LEN, &gvf)) return -1;
    buf[DIG4_DATE_LEN-1] = '\0';
    Vect_set_date ( Mapout, buf );
    
    if (0 >= dig__fread_port_C ( buf, DIG4_YOUR_NAME_LEN, &gvf)) return -1;
    buf[DIG4_YOUR_NAME_LEN-1] = '\0';
    Vect_set_person ( Mapout, buf );

    if (0 >= dig__fread_port_C ( buf, DIG4_MAP_NAME_LEN, &gvf)) return -1;
    buf[DIG4_MAP_NAME_LEN-1] = '\0';
    Vect_set_map_name ( Mapout, buf );

    if (0 >= dig__fread_port_C ( buf, DIG4_SOURCE_DATE_LEN, &gvf)) return -1;
    buf[DIG4_SOURCE_DATE_LEN-1] = '\0';
    Vect_set_map_date ( Mapout, buf );

    if (0 >= dig__fread_port_C ( buf, DIG4_LINE_3_LEN, &gvf)) return -1;
    buf[DIG4_LINE_3_LEN-1] = '\0';
    Vect_set_comment ( Mapout, buf );

    if (0 >= dig__fread_port_C( buf, VERS_4_DATA_SIZE, &gvf)) return -1; 

    if (buf[0] != '%' || buf[1] != '%') { /* Version3.0 */
	In_head.Version_Major = 3;
	portable = 0;  /* input vector is not portable format*/
        fprintf(stdout,"Input file is version 3.\n") ;	
    } else {
	In_head.Version_Major = 4;
	fprintf(stdout,"Input file is version 4.\n") ;	
	/* determine if in portable format or not */
	if (buf[6] == 1 && (~buf[6]&0xff) == (buf[7]&0xff)) {   /* portable ? */
	    portable = 1;  /* input vector is portable format*/
	} else {	
	    portable = 0;  /* input vector is not portable format*/
	}
    }
    if ( portable == 1) {
	fprintf(stdout,"Input file is portable.\n") ;
    } else {
	fprintf(stdout,"WARNING: Input file is not portable.\n"
		       "We will attempt to convert anyway but conversion may fail.\n"
		       "Please read manual for detail information.\n") ;	    
    }
	    
    /* set Cur_Head because it is used by dig__*_convert()
       called by dig__fread_port_*() */
    dig_set_cur_port ( &(In_head.port) );

    if (0 >= dig__fread_port_L ( &lbuf, 1, &gvf)) return -1;
    Vect_set_scale ( Mapout, (int) lbuf );
    if (0 >= dig__fread_port_I ( &ibuf, 1, &gvf)) return -1;
    Vect_set_zone ( Mapout, ibuf );
    if (0 >= dig__fread_port_D ( &dbuf, 1, &gvf)) return -1;  /* W */
    if (0 >= dig__fread_port_D ( &dbuf, 1, &gvf)) return -1; /* E */    
    if (0 >= dig__fread_port_D ( &dbuf, 1, &gvf)) return -1; /* S */
    if (0 >= dig__fread_port_D ( &dbuf, 1, &gvf)) return -1; /* N */
    if (0 >= dig__fread_port_D ( &dbuf, 1, &gvf)) return -1;
    Vect_set_thresh ( Mapout, dbuf );

    /* reading dig file body (elements) */
    nline = Vect_new_line_struct ();
    cat_out = Vect_new_cats_struct();
    
    lalloc = 0;
    lines = NULL;
    
    line = 0;
    while ( 1 ) {
        type = read_line ( &gvf, nline);
	G_debug (3, "read line = %d, type = %d", line, type);
	if ( type == -2 ) break; /* EOF */
	switch (type) {
	    case GV_POINT:
		npoints++;
		break;
	    case GV_LINE:
		nlines++;
		break;
	    case GV_BOUNDARY:
		nbounds++;
		break;
	    case 0:          /* dead */
		break;
	    default:
		nunknown++;
		break;	    
	}
	if ( !(type & (GV_POINT | GV_LINE | GV_BOUNDARY )))  continue; 
	
	if ( (type & GV_BOUNDARY) || !att){
            Vect_write_line ( Mapout, type, nline, cat_out );
            /* reset In_head */
	    dig_set_cur_port ( &(In_head.port) );
	} else {   /* GV_POINT or GV_LINE */
	    if ( line >= lalloc ) {
	        lalloc += 10000;
	        lines = (struct Line *) realloc ( lines, lalloc * sizeof(struct Line));
	    }
	    lines[line].type = type;
	    lines[line].n_points = nline->n_points;
	    lines[line].cat = -1;
	    lines[line].x = (double *) malloc ( nline->n_points * sizeof (double));
	    lines[line].y = (double *) malloc ( nline->n_points * sizeof (double));
	    memcpy ( (void *) lines[line].x, (void *) nline->x,
		     nline->n_points * sizeof(double));
	    memcpy ( (void *) lines[line].y, (void *) nline->y,
		     nline->n_points * sizeof(double));
	    line++;
	}
    }
    if (att) {
        fprintf(stdout,"%-5d points read to memory\n", npoints);
        fprintf(stdout,"%-5d lines read to memory\n", nlines);
    } else {
        fprintf(stdout,"%-5d points read and written to output\n", npoints);
        fprintf(stdout,"%-5d lines read and written to output\n", nlines);
    }
    fprintf(stdout,"%-5d area boundaries read and written to output\n", nbounds);    
    fprintf(stdout,"%-5d dead points skipped\n", ndpoints);
    fprintf(stdout,"%-5d dead lines skipped\n", ndlines);    
    fprintf(stdout,"%-5d dead area boundaries skipped\n", ndbounds);        
    fprintf(stdout,"%-5d elements of unknown type skipped\n", nunknown);

    fprintf(stdout,"%-5d elements read to memory.\n", line);

    *plines = lines;
    return (line);
}

/* read_line() reads element from file
   returns element type
 */   
int read_line ( GVFILE *Gvf, struct line_pnts *nline )
{
    int n_points;
    long itype;

    if (0 >= dig__fread_port_L (&itype, 1, Gvf)) return (-2);
    itype = dig_old_to_new_type ((char) itype);

    if (0 >= dig__fread_port_I (&n_points, 1, Gvf)) return (-2);
 
    if (0 > dig_alloc_points ( nline, n_points))
       G_fatal_error ("Cannot allocate points");
 
    nline->n_points = n_points;
    if (0 >= dig__fread_port_D ( nline->x, n_points, Gvf)) return (-2);
    if (0 >= dig__fread_port_D ( nline->y, n_points, Gvf)) return (-2);    

    return ((int) itype);
}  

/* read old 3.0, 4.0 dig_att file into array*/
int read_att (FILE *Attin, struct Categ **pcats )
{
    int ctalloc=0, cat=0, type, ret, rcat; 
    int    npoints=0, nlines=0, ncentroids=0;     
    int    ndpoints=0, ndlines=0, ndcentroids=0, nunknown=0;         
    char buf[201], ctype;
    double x, y;
    struct Categ *cats;
    
    fprintf(stdout,"Reading dig_att file...\n");
    
    ctalloc = 0;
    cats = NULL;

    while ( fgets( buf, 200, Attin ) != NULL) {
        ret = sscanf( buf, "%c %lf %lf %d", &ctype, &x, &y, &rcat);
        if (ret != 4) { 
            fprintf(stderr,"Error: %s\n", buf);
	    continue;
	}
	switch (ctype) {
	    case 'P':
		type = GV_POINT;
		npoints++;
		break;
	    case 'L':
		type = GV_LINE;
		nlines++;
		break;
	    case 'A':
		type = GV_CENTROID;
		ncentroids++;
		break;
	    case 'p':
	    case 'l':
	    case 'a':
		type = 0;  /* dead */
            default:
                fprintf(stderr,"Unknown type: %c\n", ctype);
		type = 0;
		nunknown++;
                break;
        }
	if (!(type & (GV_POINT | GV_LINE | GV_CENTROID))) { continue;} 
			
	if ( cat >= ctalloc ) {
	    ctalloc += 10000;
	    cats = (struct Categ *) realloc ( cats, ctalloc * sizeof(struct Categ));
	}
        cats[cat].type = type;         
        cats[cat].x = x;         
        cats[cat].y = y;         
        cats[cat].cat = rcat;         
        cat++;
	
    }
    
    fprintf(stdout,"%-5d point categories read\n", npoints);
    fprintf(stdout,"%-5d line categories read\n", nlines);    
    fprintf(stdout,"%-5d centroids read\n", ncentroids);    
    fprintf(stdout,"%-5d dead point categories skipped\n", ndpoints);
    fprintf(stdout,"%-5d dead line categories skipped\n", ndlines);    
    fprintf(stdout,"%-5d dead centroids skipped\n", ndcentroids);        
    fprintf(stdout,"%-5d categories of unknown type skipped\n", nunknown);
    
    fprintf(stdout,"%-5d categories read into memory.\n", cat);
    
    *pcats = cats; 
    return (cat);    
}


