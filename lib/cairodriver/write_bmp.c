
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include "cairodriver.h"

static unsigned char *put_2(unsigned char *p, unsigned int n)
{
    *p++ = n & 0xFF;
    n >>= 8;
    *p++ = n & 0xFF;
    return p;
}

static unsigned char *put_4(unsigned char *p, unsigned int n)
{
    *p++ = n & 0xFF;
    n >>= 8;
    *p++ = n & 0xFF;
    n >>= 8;
    *p++ = n & 0xFF;
    n >>= 8;
    *p++ = n & 0xFF;
    return p;
}

static void make_bmp_header(unsigned char *p)
{
    *p++ = 'B';
    *p++ = 'M';

    p = put_4(p, HEADER_SIZE + ca.width * ca.height * 4);
    p = put_4(p, 0);
    p = put_4(p, HEADER_SIZE);

    p = put_4(p, 40);
    p = put_4(p, ca.width);
    p = put_4(p, -ca.height);
    p = put_2(p, 1);
    p = put_2(p, 32);
    p = put_4(p, 0);
    p = put_4(p, ca.width * ca.height * 4);
    p = put_4(p, 0);
    p = put_4(p, 0);
    p = put_4(p, 0);
    p = put_4(p, 0);
}

void cairo_write_bmp(void)
{
    char header[HEADER_SIZE];
    FILE *output;

    output = fopen(ca.file_name, "wb");
    if (!output)
	G_fatal_error("cairo: couldn't open output file %s", ca.file_name);

    make_bmp_header(header);
    fwrite(header, sizeof(header), 1, output);

    fwrite(ca.grid, ca.stride, ca.height, output);

    fclose(output);
}
