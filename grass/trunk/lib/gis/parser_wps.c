
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#if defined(HAVE_LANGINFO_H)
#include <langinfo.h>
#endif
#if defined(__MINGW32__) && defined(USE_NLS)
#include <localcharset.h>
#endif

#include "parser_local_proto.h"

/* Defines and prototypes for WPS process_description XML document generation
 */
#define TYPE_OTHER -1
#define TYPE_RASTER 0
#define TYPE_VECTOR 1
#define TYPE_PLAIN_TEXT 2
#define TYPE_RANGE 3
#define TYPE_LIST 4
#define WPS_INPUT 0
#define WPS_OUTPUT 1


static void wps_print_process_descriptions_begin(void);
static void wps_print_process_descriptions_end(void);
static void wps_print_process_description_begin(int , int , const char *, const char *, const char *, const char **, int );
static void wps_print_process_description_end(void);
static void wps_print_data_inputs_begin(void);
static void wps_print_data_inputs_end(void);
static void wps_print_process_outputs_begin(void);
static void wps_print_process_outputs_end(void);
static void wps_print_bounding_box_data(void);
static void wps_print_mimetype_text_plain(void);
static void wps_print_mimetype_raster_tiff(void);
static void wps_print_mimetype_raster_png(void);
static void wps_print_mimetype_raster_grass_binary(void);
static void wps_print_mimetype_raster_grass_ascii(void);
static void wps_print_mimetype_vector_gml310(void);
static void wps_print_mimetype_vector_grass_ascii(void);
static void wps_print_mimetype_vector_grass_binary(void);
static void wps_print_ident_title_abstract(const char *, const char *, const char *);
static void wps_print_complex_input(int , int , const char *, const char *, const char *, int , int );
static void wps_print_complex_output(const char *, const char *, const char *, int );
static void wps_print_comlpex_input_output(int , int , int , const char *, const char *, const char *, int , int );
static void wps_print_literal_input_output(int , int , int , const char *,
                                const char *, const char *, const char *, int ,
                                const char **, int , const char *, int );

static void print_escaped_for_xml(FILE * fp, const char *str)
{
    for (; *str; str++) {
	switch (*str) {
	case '&':
	    fputs("&amp;", fp);
	    break;
	case '<':
	    fputs("&lt;", fp);
	    break;
	case '>':
	    fputs("&gt;", fp);
	    break;
	default:
	    fputc(*str, fp);
	}
    }
}

/*!
 * \brief Print the WPS 1.0.0 process description XML document to stdout
 *
 * A module started with the parameter "--wps-process-description"
 * will write a process description XML document to stdout and exit.
 *
 * Currently only raster and vector modules are supported, but the
 * generation works with any module (more or less meaningful).
 * Most of the input options are catched:
 * * single and multiple raster and vector maps
 * * single and multiple string, float and integer data with default
 * values and value options (range is missing)
 * Flags are supported as boolean values.
 *
 * The mime types for vector maps are GML 3.1 and grass ascii and binary vectors.
 * mime type: application/grass-vector-ascii  -> a text file generated with v.out.asci
 * Example.: urn:file:///path/name
 * mime type: application/grass-vector-binary -> the binary vectors must be addressed with a non standard urn:
 * Example: urn:grass:vector:location/mapset/name
 *
 * The mime types for raster maps are tiff and png as well as grass ascii
 * and binary raster maps, following the same scheme as the vector maps
 *
 * The mime types are reflecting the capabilities of gdal and may be extended.
 *
 * BoundignBox support is currently not available for inputs and outputs.
 * Literal data output (string, float or integer)  is currently not supported.
 *
 * In case no output parameter was set (new raster of vector map) the stdout output
 * is noticed as output parameter of mime type text/plain.
 *
 * Multiple vector or raster map outputs marked as one option are not supported (wps 1.0.0 specification
 * does not allow multiple outputs with only one identifier).
 * Multiple outputs must be wrapped via a python script.
 *
 * There is not support for optional outputs.
 *
 * */

void G__wps_print_process_description(void)
{
    struct Option *opt;
    struct Flag *flag;
    char *type;
    char *s, *top;
    const char *value = NULL;
    int i;
    char *encoding;
    int new_prompt = 0;
    int store = 1;
    int status = 1;
    const char *identifier = NULL;
    const char *title = NULL;
    const char *abstract = NULL;
    const char **keywords = NULL;
    int data_type, is_input, is_output;
    int min = 0, max = 0;
    int num_keywords = 0;
    int found_output = 0;
    new_prompt = G__uses_new_gisprompt();

    /* gettext converts strings to encoding returned by nl_langinfo(CODESET) */

#if defined(HAVE_LANGINFO_H)
    encoding = nl_langinfo(CODESET);
    if (!encoding || strlen(encoding) == 0) {
	encoding = "UTF-8";
    }
#elif defined(__MINGW32__) && defined(USE_NLS)
    encoding = locale_charset();
    if (!encoding || strlen(encoding) == 0) {
	encoding = "UTF-8";
    }
#else
    encoding = "UTF-8";
#endif

    if (!st->pgm_name)
	st->pgm_name = G_program_name();
    if (!st->pgm_name)
	st->pgm_name = "??";

    /* the identifier of the process is the module name */
    identifier = st->pgm_name;

    if (st->module_info.description) {
        title = st->module_info.description;
        abstract = st->module_info.description;
    }

    if (st->module_info.keywords) {
        keywords = st->module_info.keywords;
        num_keywords = st->n_keys;
    }

    wps_print_process_descriptions_begin();
    /* store and status are supported as default. The WPS server should change this if nessessary */
    wps_print_process_description_begin(store, status, identifier, title, abstract, keywords, num_keywords);
    wps_print_data_inputs_begin();

    /* We have two default options, which define the resolution of the created mapset */
    wps_print_literal_input_output(WPS_INPUT, 0, 1, "grass_resolution_ns", "Resolution of the mapset in north-south direction in [m] or [°]",
        "This parameter defines the north-south resolution of the mapset in meter or degrees, which should be used ot process the input and output raster data. To enable this setting, you need to specify north-south and east-west resolution.",
        "float", 0, NULL, 0, "25", TYPE_OTHER);
    wps_print_literal_input_output(WPS_INPUT, 0, 1, "grass_resolution_ew", "Resolution of the mapset in east-west direction in [m] or [°]",
        "This parameter defines the east-west resolution of the mapset in meters or degrees, which should be used ot process the input and output raster data.  To enable this setting, you need to specify north-south and east-west resolution.",
        "float", 0, NULL, 0, "25", TYPE_OTHER);
    wps_print_literal_input_output(WPS_INPUT, 0, 1, "grass_band_number", "Band to select for processing (default is all bands)",
        "This parameter defines band number of the input raster files which should be processed. As default all bands are processed and used as single and multiple inputs for raster modules.",
        "integer", 0, NULL, 0, NULL, TYPE_OTHER);

    /* Print the bounding box element with all the coordinate reference systems, which are supported by grass*/
    /* Currently Disabled! A list of all proj4 supported EPSG coordinate reference systems must be implemented*/
    if(1 == 0)
        wps_print_bounding_box_data();

    /* We parse only the inputs at the beginning */
    if (st->n_opts) {
	opt = &st->first_option;
	while (opt != NULL) {

            identifier = NULL;
            title = NULL;
            abstract = NULL;
            keywords = NULL;
            num_keywords = 0;
            value = NULL;
            is_input = 1;
            data_type = TYPE_OTHER;

	    if (opt->gisprompt) {
		const char *atts[] = { "age", "element", "prompt", NULL };
		top = G_calloc(strlen(opt->gisprompt) + 1, 1);
		strcpy(top, opt->gisprompt);
		s = strtok(top, ",");
		for (i = 0; s != NULL && atts[i] != NULL; i++) {

                    char *token = G_store(s);

                    /* we print only input parameter, sort out the output parameter */
                    if(strcmp(token, "new") == 0)
                        is_input = 0;
                    if(strcmp(token, "raster") == 0)
                    {
                        data_type = TYPE_RASTER;
                    }
                    if(strcmp(token, "vector") == 0)
                    {
                        data_type = TYPE_VECTOR;
                    }
                    if(strcmp(token, "file") == 0)
                    {
                        data_type = TYPE_PLAIN_TEXT;
                    }
                    s = strtok(NULL, ",");
                    G_free(token);
		}
		G_free(top);
	    }
            /* We have an input option */
            if(is_input == 1)
            {
                switch (opt->type) {
                case TYPE_INTEGER:
                    type = "integer";
                    break;
                case TYPE_DOUBLE:
                    type = "float";
                    break;
                case TYPE_STRING:
                    type = "string";
                    break;
                default:
                    type = "string";
                    break;
                }

                identifier = opt->key;
                if(opt->required == YES)
                    min = 1;
                else
                    min = 0;

                if(opt->multiple == YES)
                    max = 1024;
                else
                    max = 1;

                if (opt->description) {
                    title = opt->description;
                    abstract = opt->description;
                }
                if (opt->def) {
                    value = opt->def;
                }
                if (opt->options) {
                    /* TODO:
                     * add something like
                     *       <range min="xxx" max="xxx"/>
                     * to <values> */
                    i = 0;
                    while (opt->opts[i]) {
                        i++;
                    }
                    keywords = opt->opts;
                    num_keywords = i;
                }

                if(data_type == TYPE_RASTER || data_type == TYPE_VECTOR || data_type == TYPE_PLAIN_TEXT)
                {
                    /* 2048 is the maximum size of the map in mega bytes */
                    wps_print_complex_input(min, max, identifier, title, NULL, 2048, data_type);
                }
                else
                {
                    /* The keyword array is missused for options, type means the type of the value (integer, float ... )*/
                    wps_print_literal_input_output(WPS_INPUT, min, max, identifier, title, NULL, type, 0, keywords, num_keywords, value, TYPE_OTHER);
                }
            }
	    opt = opt->next_opt;
	}
    }

    /* Flags are always input options and can be false or true (boolean) */
    if (st->n_flags) {
	flag = &st->first_flag;
	while (flag != NULL) {

            /* The identifier is the flag "-x" */
            char* ident = (char*)G_calloc(3, sizeof(char));
            ident[0] = '-';
            ident[1] = flag->key;
            ident[2] = '\0';
            title = NULL;
            abstract = NULL;

	    if (flag->description) {
                title = flag->description;
                abstract = flag->description;
	    }
            const char *val[] = {"true","false"};
            wps_print_literal_input_output(WPS_INPUT, 0, 1, ident, title, NULL, "boolean", 0, val, 2, "false", TYPE_OTHER);
	    flag = flag->next_flag;
	}
    }

    /* End of inputs */
    wps_print_data_inputs_end();
    /* Start of the outputs */
    wps_print_process_outputs_begin();

    found_output = 0;

    /*parse the ouput. only raster and vector map and stdout are supported */
    if (st->n_opts) {
	opt = &st->first_option;
	while (opt != NULL) {

            identifier = NULL;
            title = NULL;
            abstract = NULL;
            value = NULL;
            is_output = 0;
            data_type = TYPE_OTHER;

	    if (opt->gisprompt) {
		const char *atts[] = { "age", "element", "prompt", NULL };
		top = G_calloc(strlen(opt->gisprompt) + 1, 1);
		strcpy(top, opt->gisprompt);
		s = strtok(top, ",");
		for (i = 0; s != NULL && atts[i] != NULL; i++) {

                    char *token = G_store(s);

                    /* we print only the output parameter */
                    if(strcmp(token, "new") == 0)
                        is_output = 1;
                    if(strcmp(token, "raster") == 0)
                    {
                        data_type = TYPE_RASTER;
                    }
                    if(strcmp(token, "vector") == 0)
                    {
                        data_type = TYPE_VECTOR;
                    }
                    if(strcmp(token, "file") == 0)
                    {
                        data_type = TYPE_PLAIN_TEXT;
                    }
                    s = strtok(NULL, ",");
                    G_free(token);
		}
		G_free(top);
	    }
            /* Only single module output is supported */
            if(is_output == 1 && opt->multiple == NO)
            {
                identifier = opt->key;
                if (opt->description) {
                    title = opt->description;
                    abstract = opt->description;
                }

                /* Only file, raster and vector output is supported by option */
                if(data_type == TYPE_RASTER || data_type == TYPE_VECTOR  || data_type == TYPE_PLAIN_TEXT)
                {
                    wps_print_complex_output(identifier, title, NULL, data_type);
                    found_output = 1;
                }
            }
	    opt = opt->next_opt;
	}
        /* we assume the computatuon output on stdout, if no raster/vector output was found*/
        if(found_output == 0)
            wps_print_complex_output("stdout", "Module output on stdout", "The output of the module written to stdout", TYPE_PLAIN_TEXT);
    }

    wps_print_process_outputs_end();
    wps_print_process_description_end();
    wps_print_process_descriptions_end();
}


/**************************************************************************
 *
 * The remaining routines are all local (static) routines used to support
 * the the creation of the WPS process_description document.
 *
 **************************************************************************/

static void wps_print_process_descriptions_begin(void)
{
    fprintf(stdout, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
    fprintf(stdout, "<wps:ProcessDescriptions xmlns:wps=\"http://www.opengis.net/wps/1.0.0\"\n");
    fprintf(stdout, "xmlns:ows=\"http://www.opengis.net/ows/1.1\"\n");
    fprintf(stdout, "xmlns:xlink=\"http://www.w3.org/1999/xlink\"\n");
    fprintf(stdout, "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n");
    fprintf(stdout, "xsi:schemaLocation=\"http://www.opengis.net/wps/1.0.0\n http://schemas.opengis.net/wps/1.0.0/wpsDescribeProcess_response.xsd\"\n service=\"WPS\" version=\"1.0.0\" xml:lang=\"en-US\"> \n");
}

/* ************************************************************************** */

static void wps_print_process_descriptions_end(void)
{
    fprintf(stdout,"</wps:ProcessDescriptions>\n");
}

/* ************************************************************************** */

static void wps_print_process_description_begin(int store, int status, const char *identifier,
                                               const char *title, const char *abstract,
                                               const char **keywords, int num_keywords)
{
    int i;

    fprintf(stdout,"\t<ProcessDescription wps:processVersion=\"1\" storeSupported=\"%s\" statusSupported=\"%s\">\n", (store?"true":"false"), (status?"true":"false"));
       if(identifier)
    {
        fprintf(stdout,"\t\t<ows:Identifier>");
        print_escaped_for_xml(stdout, identifier);
        fprintf(stdout,"</ows:Identifier>\n");
    }

    if(title)
    {
        fprintf(stdout,"\t\t<ows:Title>");
        print_escaped_for_xml(stdout, title);
        fprintf(stdout, "</ows:Title>\n");
    }

    if(abstract)
    {
        fprintf(stdout,"\t\t<ows:Abstract>\n");
        fprintf(stdout, "\t\t\tThe manual page of this module is available here:\n");
        fprintf(stdout, "\t\t\thttp://grass.osgeo.org/grass70/manuals/html70_user/%s.html\n", identifier);
        fprintf(stdout, "\t\t</ows:Abstract>\n");
    }

    for(i = 0; i < num_keywords; i++)
    {
        fprintf(stdout,"\t\t<ows:Metadata xlink:title=\"");
        print_escaped_for_xml(stdout, keywords[i]);
        fprintf(stdout, "\" />\n");
    }
}

/* ************************************************************************** */

static void wps_print_process_description_end(void)
{
    fprintf(stdout,"\t</ProcessDescription>\n");
}

/* ************************************************************************** */

static void wps_print_data_inputs_begin(void)
{
    fprintf(stdout,"\t\t<DataInputs>\n");
}

/* ************************************************************************** */

static void wps_print_data_inputs_end(void)
{
    fprintf(stdout,"\t\t</DataInputs>\n");
}

/* ************************************************************************** */

static void wps_print_process_outputs_begin(void)
{
    fprintf(stdout,"\t\t<ProcessOutputs>\n");
}

/* ************************************************************************** */

static void wps_print_process_outputs_end(void)
{
    fprintf(stdout,"\t\t</ProcessOutputs>\n");
}

/* ************************************************************************** */

static void wps_print_complex_input(int min, int max, const char *identifier, const char *title, const char *abstract, int megs, int type)
{
    wps_print_comlpex_input_output(WPS_INPUT, min, max, identifier, title, abstract, megs, type);
}

/* ************************************************************************** */

static void wps_print_complex_output(const char *identifier, const char *title, const char *abstract, int type)
{
    wps_print_comlpex_input_output(WPS_OUTPUT, 0, 0, identifier, title, abstract, 0, type);
}

/* ************************************************************************** */

static void wps_print_comlpex_input_output(int inout_type, int min, int max, const char *identifier, const char *title, const char *abstract, int megs, int type)
{
    if(inout_type == WPS_INPUT)
        fprintf(stdout,"\t\t\t<Input minOccurs=\"%i\" maxOccurs=\"%i\">\n", min, max);
    else if(inout_type == WPS_OUTPUT)
        fprintf(stdout,"\t\t\t<Output>\n");

    wps_print_ident_title_abstract(identifier, title, abstract);

    if(inout_type == WPS_INPUT)
        fprintf(stdout,"\t\t\t\t<ComplexData maximumMegabytes=\"%i\">\n", megs);
    else if(inout_type == WPS_OUTPUT)
        fprintf(stdout,"\t\t\t\t<ComplexOutput>\n");

    fprintf(stdout,"\t\t\t\t\t<Default>\n");
    if(type == TYPE_RASTER)
    {
            wps_print_mimetype_raster_tiff();
    }
    else if(type == TYPE_VECTOR)
    {
            wps_print_mimetype_vector_gml310();
    }
    else if(type == TYPE_PLAIN_TEXT)
    {
            wps_print_mimetype_text_plain();
    }
    fprintf(stdout,"\t\t\t\t\t</Default>\n");
    fprintf(stdout,"\t\t\t\t\t<Supported>\n");
    if(type == TYPE_RASTER)
    {
            wps_print_mimetype_raster_tiff();
            /* These mime types are currently not meaningful */
            if(1 == 0) {
                wps_print_mimetype_raster_png();
                wps_print_mimetype_raster_grass_ascii();
                wps_print_mimetype_raster_grass_binary();
            }
    }
    else if(type == TYPE_VECTOR)
    {
            wps_print_mimetype_vector_gml310();
            /* These mime types are currently not meaningful */
            if(1 == 0) {
                wps_print_mimetype_vector_grass_ascii();
                wps_print_mimetype_vector_grass_binary();
            }
    }
    else if(type == TYPE_PLAIN_TEXT)
    {
            wps_print_mimetype_text_plain();
    }
    fprintf(stdout,"\t\t\t\t\t</Supported>\n");

    if(inout_type == WPS_INPUT)
        fprintf(stdout,"\t\t\t\t</ComplexData>\n");
    else if(inout_type == WPS_OUTPUT)
        fprintf(stdout,"\t\t\t\t</ComplexOutput>\n");

    if(inout_type == WPS_INPUT)
        fprintf(stdout,"\t\t\t</Input>\n");
    else if(inout_type == WPS_OUTPUT)
        fprintf(stdout,"\t\t\t</Output>\n");
}

/* ************************************************************************** */

static void wps_print_ident_title_abstract(const char *identifier, const char *title, const char *abstract)
{
    if(identifier)
    {
        fprintf(stdout,"\t\t\t\t<ows:Identifier>");
        print_escaped_for_xml(stdout, identifier);
        fprintf(stdout,"</ows:Identifier>\n");
    }

    if(title)
    {
        fprintf(stdout,"\t\t\t\t<ows:Title>");
        print_escaped_for_xml(stdout, title);
        fprintf(stdout, "</ows:Title>\n");
    }

    if(abstract)
    {
        fprintf(stdout,"\t\t\t\t<ows:Abstract>");
        print_escaped_for_xml(stdout, abstract);
        fprintf(stdout, "</ows:Abstract>\n");
    }
}

/* ************************************************************************** */

static void wps_print_literal_input_output(int inout_type, int min, int max, const char *identifier,
                                const char *title, const char *abstract, const char *datatype, int unitofmesure,
                                const char **choices, int num_choices, const char *default_value, int type)
{
    int i;

    if(inout_type == WPS_INPUT)
        fprintf(stdout,"\t\t\t<Input minOccurs=\"%i\" maxOccurs=\"%i\">\n", min, max);
    else if(inout_type == WPS_OUTPUT)
        fprintf(stdout,"\t\t\t<Output>\n");

    wps_print_ident_title_abstract(identifier, title, abstract);

    fprintf(stdout,"\t\t\t\t<LiteralData>\n");

    if(datatype)
        fprintf(stdout,"\t\t\t\t\t<ows:DataType ows:reference=\"xs:%s\">%s</ows:DataType>\n", datatype, datatype);

    if(unitofmesure)
    {
        fprintf(stdout,"\t\t\t\t\t<UOMs>\n");
        fprintf(stdout,"\t\t\t\t\t<Default>\n");
        fprintf(stdout,"\t\t\t\t\t\t<ows:UOM>meters</ows:UOM>\n");
        fprintf(stdout,"\t\t\t\t\t</Default>\n");
        fprintf(stdout,"\t\t\t\t\t<Supported>\n");
        fprintf(stdout,"\t\t\t\t\t\t<ows:UOM>meters</ows:UOM>\n");
        fprintf(stdout,"\t\t\t\t\t</Supported>\n");
        fprintf(stdout,"\t\t\t\t\t</UOMs>\n");
    }
    if(num_choices == 0 || choices == NULL)
        fprintf(stdout,"\t\t\t\t\t<ows:AnyValue/>\n");
    else
    {
        fprintf(stdout,"\t\t\t\t\t<ows:AllowedValues>\n");
        if(type == TYPE_RANGE && num_choices > 1)
        {
        fprintf(stdout,"\t\t\t\t\t\t<ows:Range ows:rangeClosure=\"%s\">\n", "0");
        fprintf(stdout,"\t\t\t\t\t\t\t<ows:MinimumValue>%s</ows:MinimumValue>\n", choices[0]);
        fprintf(stdout,"\t\t\t\t\t\t\t<ows:MaximumValue>%s</ows:MaximumValue>\n", choices[1]);
        fprintf(stdout,"\t\t\t\t\t\t</ows:Range>\n");
        }
        else
        {
            for(i = 0; i < num_choices; i++)
            {
                fprintf(stdout,"\t\t\t\t\t\t<ows:Value>");
                print_escaped_for_xml(stdout, choices[i]);
                fprintf(stdout,"</ows:Value>\n");
            }
        }
        fprintf(stdout,"\t\t\t\t\t</ows:AllowedValues>\n");
    }

    if(default_value)
    {
        fprintf(stdout,"\t\t\t\t\t<DefaultValue>");
        print_escaped_for_xml(stdout, default_value);
        fprintf(stdout,"</DefaultValue>\n");
    }
    fprintf(stdout,"\t\t\t\t</LiteralData>\n");


    if(inout_type == WPS_INPUT)
        fprintf(stdout,"\t\t\t</Input>\n");
    else if(inout_type == WPS_OUTPUT)
        fprintf(stdout,"\t\t\t</Output>\n");
}

/* ************************************************************************** */

static void wps_print_mimetype_text_plain(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>text/plain</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}
/* ************************************************************************** */

static void wps_print_mimetype_raster_tiff(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>image/tiff</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* ************************************************************************** */

static void wps_print_mimetype_raster_png(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>image/png</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* *** Native GRASS raster format urn:grass:raster:location/mapset/raster *** */

static void wps_print_mimetype_raster_grass_binary(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>application/grass-raster-binary</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* *** GRASS raster maps exported via r.out.ascii ************************** */

static void wps_print_mimetype_raster_grass_ascii(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>application/grass-raster-ascii</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* ************************************************************************** */

static void wps_print_mimetype_vector_gml310(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>text/xml</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<Encoding>UTF-8</Encoding>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<Schema>http://schemas.opengis.net/gml/3.1.0/polygon.xsd</Schema>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* *** GRASS vector format exported via v.out.ascii ************************** */

static void wps_print_mimetype_vector_grass_ascii(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>application/grass-vector-ascii</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* *** Native GRASS vector format urn:grass:vector:location/mapset/vector *** */

static void wps_print_mimetype_vector_grass_binary(void)
{
    fprintf(stdout,"\t\t\t\t\t\t<Format>\n");
    fprintf(stdout,"\t\t\t\t\t\t\t<MimeType>application/grass-vector-binary</MimeType>\n");
    fprintf(stdout,"\t\t\t\t\t\t</Format>\n");
}

/* Bounding box data input. Do not use! Under construction. A list of coordinate reference systems must be created.*/

static void wps_print_bounding_box_data(void)
{
    int i;

    fprintf(stdout,"\t\t\t<Input minOccurs=\"0\" maxOccurs=\"1\">\n");
    wps_print_ident_title_abstract("BoundingBox", "Bounding box to process data",
      "The bounding box is uesed to create the reference coordinate system in grass, as well as the lower left and upper right corner of the processing area.");
    fprintf(stdout,"\t\t\t\t<BoundingBoxData>\n");
    /* A meaningful default boundingbox should be chosen*/
    fprintf(stdout,"\t\t\t\t\t<Default>\n");
    fprintf(stdout,"\t\t\t\t\t\t<CRS>urn:ogc:def:crs,crs:EPSG:6.3:32760</CRS>\n");
    fprintf(stdout,"\t\t\t\t\t</Default>\n");
    /* A list of all proj4 supported EPSG coordinate systems should be created */
    fprintf(stdout,"\t\t\t\t\t<Supported>\n");
    for(i = 0; i < 1; i++)
        fprintf(stdout,"\t\t\t\t\t\t<CRS>urn:ogc:def:crs,crs:EPSG:6.3:32760</CRS>\n");
    fprintf(stdout,"\t\t\t\t\t</Supported>\n");
    fprintf(stdout,"\t\t\t\t</BoundingBoxData>\n");
    fprintf(stdout,"\t\t\t</Input>\n");
}

