#ifndef GRASS_ROWIO_H
#define GRASS_ROWIO_H

typedef struct
{
    int fd;         /* file descriptor for reading */
    int nrows;      /* number of rows to be held in memory */
    int len;        /* buffer length */
    int cur;        /* current row in memory */
    char *buf;      /* current data buf */
    int (*getrow)();/* routine to do the row reads */
    int (*putrow)();/* routine to do the row reads */

    struct ROWIO_RCB
    {
	char *buf;  /* data buffer */
	int age;    /* for order of access */
	int row;    /* row number */
	int dirty;
    } *rcb;
} ROWIO;

int rowio_fileno(ROWIO *);
void rowio_forget (ROWIO *,int);
char *rowio_get (ROWIO *,int );
int rowio_flush( ROWIO *);
int rowio_put ( ROWIO *, char *,int);
void rowio_release (ROWIO *);
int rowio_setup (ROWIO *,int , int , int , int (*)(), int (*)());

#endif
