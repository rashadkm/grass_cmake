
#ifndef  DIG__HEAD__FOO__
#define  DIG__HEAD__FOO__


#define DIG_ORGAN_LEN       30
#define DIG_DATE_LEN        20
#define DIG_YOUR_NAME_LEN   20
#define DIG_MAP_NAME_LEN    41
#define DIG_SOURCE_DATE_LEN 11
#define DIG_LINE_3_LEN      53	/* see below */

#define OLD_LINE_3_SIZE 73
#define NEW_LINE_3_SIZE 53
#define VERS_4_DATA_SIZE 20


struct dig_head
  {	  
    /*** HEAD_ELEMENT ***/
    char organization[30];
    char date[20];
    char your_name[20];
    char map_name[41];
    char source_date[11];
    long orig_scale;
    char line_3[73];
    int plani_zone;
    double W, E, S, N;
    double digit_thresh;
    double map_thresh;

    /* Programmers should NOT touch any thing below here */
    /* Library takes care of everything for you          */
    /*** COOR_ELEMENT ***/
    int Version_Major;
    int Version_Minor;
    int Back_Major;
    int Back_Minor;
    int byte_order; 
    int with_z;


    /* portability stuff, set in V1_open_new/old() */
    /* conversion matrices between file and native byte order */
    unsigned char dbl_cnvrt[PORT_DOUBLE];
    unsigned char flt_cnvrt[PORT_FLOAT];
    unsigned char lng_cnvrt[PORT_LONG];
    unsigned char int_cnvrt[PORT_INT];
    unsigned char shrt_cnvrt[PORT_SHORT];
    
    /* *_quick specify if native byte order of that type 
     * is the same as byte order of vector file (TRUE) 
     * or not (FALSE);*/
    int dbl_quick;
    int flt_quick;
    int lng_quick;
    int int_quick;
    int shrt_quick;

    struct Map_info *Map;	/* X-ref to Map_info struct ?? */
  };




#endif
