/* 
 * $Id$
 * added little/big endian test Markus Neteler 9/2000 
 * changed 10/99 Jaro*/

#include "image.h"

unsigned short rbuf[8192];
unsigned short gbuf[8192];
unsigned short bbuf[8192];


void
ierrfunc(ebuf)
char *ebuf;
{
    fprintf(stderr, "%s\n",ebuf);
    return ;
}


GS_write_rgb(name)
char *name;
{
    int y, x;
    unsigned int xsize, ysize;
    IMAGE *image;
    unsigned long *pixbuf;

 /* endian test added from ./src.contrib/GMSL/NVIZ2.2/TOGL/apps/image.c
  * Markus Neteler
  */
    union {
        int testWord;
        char testByte[4];
    } endianTest;
    int swapFlag;

    endianTest.testWord = 1;
    if (endianTest.testByte[0] == 1) {
        swapFlag = 1; /*true: little endian */
    } else {
        swapFlag = 0;
    }


    gsd_getimage(&pixbuf, &xsize, &ysize);

    if(pixbuf){
	i_seterror(ierrfunc);
	if(NULL == (image = iopen(name,"w",VERBATIM(1),3,xsize,ysize,3)))
	{
	    fprintf(stderr,"Unable to open %s for writing.\n", name);
	    return (-1);
	}

	for(y=0; y<ysize; y++) {

	    for(x=0; x<xsize; x++){
		if (!swapFlag) {
			/* big endian: SUN et al. */
			rbuf[x] = (pixbuf[y*xsize + x] & 0xFF000000)>>24;
			gbuf[x] = (pixbuf[y*xsize + x] & 0x00FF0000)>>16;
			bbuf[x] = (pixbuf[y*xsize + x] & 0x0000FF00)>>8;
		}
		else {
			/* little endian: Linux et al. */
	                rbuf[x] = (pixbuf[y*xsize + x] & 0x000000FF);
        	        gbuf[x] = (pixbuf[y*xsize + x] & 0x0000FF00)>>8;
                	bbuf[x] = (pixbuf[y*xsize + x] & 0x00FF0000)>>16;
		}

		putrow(image,rbuf,y,0);		/* red row */
		putrow(image,gbuf,y,1);		/* green row */
		putrow(image,bbuf,y,2);		/* blue row */
	    }
	}
	free(pixbuf);
	iclose(image);
	return(0);
    }
    return(-1);

}




