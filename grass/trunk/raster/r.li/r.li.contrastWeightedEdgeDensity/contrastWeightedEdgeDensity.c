/*
 * \brief calculates contrast weighted edge density index
 *
 *   Author: Serena Pallecchi
 *
 *   This program is free software under the GPL (>=v2)
 *   Read the COPYING file that comes with GRASS for details.
 *
 */

#include <grass/gis.h>
#include <grass/glocale.h>

#include <fcntl.h> /* for O_RDONLY usage */

#include "../r.li.daemon/defs.h"
#include "../r.li.daemon/avlDefs.h"
#include "../r.li.daemon/daemon.h"

#include "cellWeighted.h"
#include "utility.h"

#define NMAX 512


int calculate (int fd, area_des ad,Coppie * cc, long totCoppie, double * result);
int calculateD (int fd, area_des ad,Coppie * cc, long totCoppie, double * result);
int calculateF (int fd, area_des ad,Coppie * cc, long totCoppie, double * result);

int main(int argc, char *argv[])
{
    struct Option *raster, *conf,*path, *output;
    struct GModule *module;
    char ** par = NULL;
    
    G_gisinit(argv[0]);
    module = G_define_module();
    module->description =_("Calculates contrast Weighted Edge Density index on a raster file");
    
    /* define options */
    
    raster = G_define_standard_option(G_OPT_R_MAP);
    
    conf = G_define_option();
    conf->key = "conf";
    conf->description = "configuration file in ~/.r.li/history/ folder (i.e conf=my_configuration)";
    conf->type = TYPE_STRING;
    conf->required = YES;
    conf->gisprompt = "file,file,file";
       
    path = G_define_option();
    path->key = "path";
    path->description = "input file that contains the weight to calculate the index";
    path->type = TYPE_STRING;
    path->required = YES;
	path->gisprompt = "file,file,file";

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    
    
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);
    
    if (path->answer ==NULL)
	par=NULL;
    else
	par=&path->answer;
    
    return calculateIndex(conf->answer, contrastWeightedEdgeDensity , par, raster->answer, output->answer);
    
}


int contrastWeightedEdgeDensity(int fd, char ** par, area_des ad, double *result)
{
    double indice=0; /* the result */
   
    struct Cell_head hd;

    int i=0;
    int file_fd=-1;
    int l; /*number of read byte*/
    int ris=0; 

    char * mapset;
    char * file;
    char * strFile;
    
    char row [NMAX]; /* to read the file */

    char ** bufRighe; /* contains every valid file row */
    
    char separatore; /* separator to split a string */
    
    long totCoppie=0; /* number of cells pair */
    long totRow=0; /* of the file */
    long tabSize=10; /* array length */

    Coppie * cc = NULL; /* here store the pair of cell with the weight. these information are in the file */

   
    /* try to open file */
    file=par[0];
    file_fd=open(file,O_RDONLY);
    if (file_fd==-1)
    {
	G_fatal_error("can't  open file %s",file);
	return ERRORE;
    }
    
    
   
    strFile=concatena("","");
    if (strFile==NULL)
    {
	G_fatal_error("can't  concat strFile");
	return ERRORE;
    }
    
    while((l=read(file_fd,row,NMAX))>0)
    {
	strFile=concatena(strFile,row);
	if (strFile==NULL)
	{
	    G_fatal_error("can't  concat strFile 2");
	    return ERRORE;
	}
    }
    
    l = close(file_fd);
    
    if(l!=0)
    {
	G_warning("errore chiusura file %s",file);
    }
    
    /* 
     * every row of a rigth file has this layout
     * CELL1,CELL2,dissimilarity  
     */
    
    /* test if the file is ok and store every line in an array of CoppiaPesata*/
    separatore='\n';
    bufRighe=split_arg(strFile,separatore,&totRow);
    if (bufRighe==NULL)
    {
	G_fatal_error("can't  split buf_righe");
	return ERRORE;
    }
       
    cc=G_malloc(tabSize*sizeof(CoppiaPesata));
    if(cc==NULL)
    {
	G_fatal_error("malloc cc failed");	
	return ERRORE;
    }
    
    mapset = G_find_cell(ad->raster, "");
    
    if (G_get_cellhd(ad->raster, mapset, &hd) == - 1)
    {
	G_fatal_error("can't read raster header");
	return ERRORE;
    }
    
    
    for(i=0; i < totRow ;i++)
    {
	long num=0;
	char ** b;
	generic_cell c1,c2;
	double p;
	int ris;
	
	separatore=',';
	b=split_arg(bufRighe[i],separatore,&num);
	if (b==NULL)
	{
	    G_fatal_error("can't split bufRighe [%d]",i);
	    return ERRORE;
	}
		
	if(num!=1)
	{
	    if(num!=3 )
	    {
		G_fatal_error("wrong file format at line %d",i+1);
		return ERRORE;
	    }
	    
	    c1.t=ad->data_type;
	    c2.t=ad->data_type;
	    
	    switch(ad->data_type)
	    {
		case CELL_TYPE:
		{
		    c1.val.c=atoi(b[0]);
		    c2.val.c=atoi(b[1]);
		    return ERRORE;
		}
		case DCELL_TYPE:
		{
		    c1.val.dc=atof(b[0]);
		    c2.val.dc=atof(b[1]);
		    break;
		}
		case FCELL_TYPE:
		{
		    c1.val.fc=(float)atof(b[0]);
		    c2.val.fc=(float)atof(b[1]);
		    break;
		}
		default:
		{
		    G_fatal_error("data type unknown");
		    return ERRORE;
		}
	    }
	    
	    p=atof(b[2]);
	    
	    ris=addCoppia(cc,c1,c2,p,totCoppie,&tabSize);
	    
	    switch(ris)
	    {
		case ERR:
		{
		    G_fatal_error("add error");
		    return ERRORE;
		}	
		case ADD:
		{
		    totCoppie++;
		    break;
		}
		case PRES:
		{
		    break;
		}
		default:
		{
		    G_fatal_error("add unknown error");
		    return ERRORE;
		}
	    }	
	} 
	else ;
	/* num = 1  ---> in the line there is only 1 token 
	 * I ignore this line
	 */
    }
    
    
    
    
    switch(ad->data_type)
    {
	case CELL_TYPE:
	{    	    
	    ris=calculate(fd,ad,cc,totCoppie,&indice);
	    break;
	}
	case DCELL_TYPE:
	{ 	    
	    ris=calculateD(fd,ad,cc,totCoppie,&indice);
	    break;
	}
	case FCELL_TYPE:
	{ 
	    ris=calculateF(fd,ad,cc,totCoppie,&indice);
	    break;
	}
	default:
	{
	    G_fatal_error("data type unknown");
	    return ERRORE;
	}
    }
    
    if(ris!=OK)
    {
	return ERRORE;
    }

    *result=indice;
    
    G_free(cc);
    
    return OK;
}




int calculate (int fd, area_des ad, Coppie * cc,  long totCoppie, double * result)
{
    
    double indice=0;
    double somma=0;
    double area=0;
    
    int i=0,j;
    int mask_fd=-1;
    int masked=FALSE;
    int * mask_corr,* mask_sup;
		    
    CELL * buf_corr, * buf_sup;
    CELL prevCell, corrCell, supCell;
    
    generic_cell c1;
    generic_cell c2;
    
    
    
    /* open mask if needed */
    if (ad->mask == 1)
    {
	if ( (mask_fd = open(ad->mask_name, O_RDONLY, 0755)) < 0)
	{
	    G_fatal_error("can't open mask");
	    return ERRORE;
	}
	
	mask_corr = G_malloc(ad->cl * sizeof(int));
	if (mask_corr==NULL)
	{
	    G_fatal_error("malloc mask_corr failed");
	    return ERRORE;
	}
	
	mask_sup = G_malloc(ad->cl * sizeof(int));
	if (mask_sup==NULL)
	{
	    G_fatal_error("malloc mask_sup failed");
	    return ERRORE;
	}
	
	masked=TRUE;
    }
    
    
    buf_sup=G_allocate_cell_buf();
    if (buf_sup==NULL)
    {
	G_fatal_error("malloc buf_sup failed");
	return ERRORE;
    }
    
    c1.t=CELL_TYPE;
    c2.t=CELL_TYPE;
    
    buf_corr=G_allocate_cell_buf();
    if (buf_corr==NULL)
    {
	G_fatal_error("error malloc buf_corr");
	return ERRORE;
    }
    
    G_set_c_null_value(buf_sup+ad->x,ad->cl); /*the first time buf_sup is all null*/
    
    for(j = 0; j< ad->rl; j++)/* for each row*/
    {
	buf_corr = RLI_get_cell_raster_row(fd, j+ad->y, ad);/* read row of raster*/
	if(j>0)/* not first row */
	{ 
	    buf_sup= RLI_get_cell_raster_row(fd, j-1+ad->y, ad);
	}
	/*read mask if needed*/
	if (masked)
	{
	    printf("MASK");/*TODO to delete*/
	    if(read(mask_fd,mask_corr,(ad->cl * sizeof (int)))<0)
	    {
		G_fatal_error("reading mask_corr");
		return ERRORE;
	    }
	}
	
	G_set_c_null_value(&prevCell,1);
	G_set_c_null_value(&corrCell,1);
	
	for(i=0; i < ad->cl; i++)/* for each cell in the row */
	{
	    area++;
	    corrCell=buf_corr[i+ad->x];
	    if(masked && mask_corr[i+ad->x]==0)
	    {
		area--;
		G_set_c_null_value(&corrCell,1);
	    }
	    if(!(G_is_null_value(&corrCell,CELL_TYPE)))
	    {				
		supCell=buf_sup[i+ad->x];
		/* calculate how many edge the cell has*/
		if(   ( (!G_is_null_value(&prevCell,CELL_TYPE)) ) && (corrCell!=prevCell)   )
		{
		    int r=0;
		    c1.val.c=corrCell;
		    c2.val.c=prevCell;
		    r=updateCoppia(cc,c1,c2,totCoppie);
		}			
		
		if(   ( !(G_is_null_value(&supCell,CELL_TYPE)) ) && (corrCell!=supCell)   )
		{
		    int r=0;
		    c1.val.c=corrCell;
		    c2.val.c=prevCell;
		    r=updateCoppia(cc,c1,c2,totCoppie);
		}
	    }	
	    prevCell=buf_corr[i+ad->x];
	}
	
	if (masked)
	    mask_sup=mask_corr;
    }
    
    
    /* calcolo dell'indice */
    if(area==0)
	indice=0;
    else
    {
	for (i=0;i<totCoppie;i++)
	{
	    double ee,dd;
	    ee=(double)(cc[i]->e);
	    dd=(double)(cc[i]->d);
	    somma=somma+(ee*dd);
	}
	indice=somma*10000/area;
    }
    *result=indice;
    
    if (masked)
    {
	G_free(mask_corr);
        G_free(mask_sup);
    }
    return OK; 	
}


int calculateD (int fd, area_des ad, Coppie * cc,  long totCoppie, double * result)
{
    
    double indice=0;
    double somma=0;
    double area=0;
    
    int i=0,j;
    int mask_fd=-1;
    int masked=FALSE;
    int * mask_corr,* mask_sup;
    
    DCELL * buf_corr, * buf_sup;
    DCELL prevCell, corrCell, supCell;
    
    generic_cell c1;
    generic_cell c2;
    
    
    
    /* open mask if needed */
    if (ad->mask == 1)
    {
	if ( (mask_fd = open(ad->mask_name, O_RDONLY, 0755)) < 0)
	{
	    G_fatal_error("can't  open mask");
	    return ERRORE;
	}
	
	mask_corr = G_malloc(ad->cl * sizeof(int));
	if (mask_corr==NULL)
	{
	    G_fatal_error("malloc mask_corr failed");
	    return ERRORE;
	}
	
	mask_sup = G_malloc(ad->cl * sizeof(int));
	if (mask_sup==NULL)
	{
	    G_fatal_error("malloc mask_corr failed");
	    return ERRORE;
	}
	
	masked=TRUE;
    }
    
    
    buf_sup=G_allocate_d_raster_buf ();
    if (buf_sup==NULL)
    {
	G_fatal_error("malloc buf_sup failed");
	return ERRORE;
    }
    
    c1.t=DCELL_TYPE;
    c2.t=DCELL_TYPE;
    
    buf_corr=G_allocate_d_raster_buf ();
    
    G_set_d_null_value(buf_sup+ad->x,ad->cl); /*the first time buf_sup is all null*/
    
    for(j = 0; j< ad->rl; j++)/* for each row*/
    {
	buf_corr = RLI_get_dcell_raster_row(fd, j+ad->y, ad);/* read row of raster*/
	if(j>0)/* not first row */
	{ 
	    buf_sup= RLI_get_dcell_raster_row(fd, j-1+ad->y, ad);
	}
	/*read mask if needed*/
	if (masked)
	{
	    printf("MASK");/*TODO to delete*/
	    if(read(mask_fd,mask_corr,(ad->cl * sizeof (int)))<0)
	    {
		G_fatal_error("reading mask_corr");
		return ERRORE;
	    }
	}
	G_set_d_null_value(&prevCell,1);
	G_set_d_null_value(&corrCell,1);
	for(i=0; i < ad->cl; i++)/* for each cell in the row */
	{
	    area++;
	    corrCell=buf_corr[i+ad->x];
	    if(masked && mask_corr[i+ad->x]==0)
	    {
		G_set_d_null_value(&corrCell,1);
		area--;
	    }
	    if(!(G_is_null_value(&corrCell,DCELL_TYPE)))
	    {
		supCell=buf_sup[i+ad->x];
		/* calculate how many edge the cell has*/
		if(   ( (!G_is_null_value(&prevCell,DCELL_TYPE)) ) && (corrCell!=prevCell)   )
		{
		    int r=0;
		    c1.val.dc=corrCell;
		    c2.val.dc=prevCell;
		    r=updateCoppia(cc,c1,c2,totCoppie);
		}
		
		
		if(   ( !(G_is_null_value(&supCell,DCELL_TYPE)) ) && (corrCell!=supCell)   )
		{
		    int r=0;
		    c1.val.dc=corrCell;
		    c2.val.dc=prevCell;
		    r=updateCoppia(cc,c1,c2,totCoppie);
		}
		
	    }	
	    prevCell=buf_corr[i+ad->x];
	}
	
	if (masked)
	    mask_sup=mask_corr;
    }
    
    
    /* calcolo dell'indice */
    if(area==0)
	indice=0;
    else
    {
	for (i=0;i<totCoppie;i++)
	{
	    double ee,dd;
	    ee=(double)(cc[i]->e);
	    dd=(double)(cc[i]->d);
	    somma=somma+(ee*dd);
	}
	indice=somma*10000/area;
    }
    *result=indice;
    if (masked)
    {
    	G_free(mask_corr);
        G_free(mask_sup);
    }
    return OK; 	
}



int calculateF (int fd, area_des ad, Coppie * cc, long totCoppie, double * result)
{
    
    double indice=0;
    double somma=0;
    double area=0;
    
    int i=0,j;
    int mask_fd=-1;
    int masked=FALSE;
    int * mask_corr,* mask_sup;
    
    FCELL * buf_corr, * buf_sup;
    FCELL prevCell, corrCell, supCell;
    
    generic_cell c1;
    generic_cell c2;
    
    
    
    /* open mask if needed */
    if (ad->mask == 1)
    {
	if ( (mask_fd = open(ad->mask_name, O_RDONLY, 0755)) < 0)
	{
	    G_fatal_error("can't  open mask");
	    return ERRORE;
	}
	
	mask_corr = G_malloc(ad->cl * sizeof(int));
	if (mask_corr==NULL)
	{
	    G_fatal_error("malloc mask_corr failed");
	    return ERRORE;
	}
	
	mask_sup = G_malloc(ad->cl * sizeof(int));
	if (mask_sup==NULL)
	{
	    G_fatal_error("malloc mask_corr failed");
	    return ERRORE;
	}
	
	masked=TRUE;
    }
    
    /* allocate and inizialize buffers */
    buf_sup=G_allocate_f_raster_buf ();
    if (buf_sup==NULL)
	{
	    G_fatal_error("malloc buf_sup failed");
	    return ERRORE;
	}
    G_set_f_null_value(buf_sup+ad->x,ad->cl); /*the first time buf_sup is all null*/
    
    buf_corr=G_allocate_f_raster_buf ();
    if (buf_corr==NULL)
    {
	G_fatal_error("malloc buf_corr failed");
	return ERRORE;
    }
    
    c1.t=FCELL_TYPE;
    c2.t=FCELL_TYPE;
    
    
    for(j = 0; j< ad->rl; j++)/* for each row*/
    {
	buf_corr = RLI_get_fcell_raster_row(fd, j+ad->y, ad);/* read row of raster*/
	if(j>0)/* not first row */
	{ 
	    buf_sup= RLI_get_fcell_raster_row(fd, j-1+ad->y, ad);
	}
	/*read mask if needed*/
	if (masked)
	{
	    printf("MASK");/*TODO to delete*/
	    if(read(mask_fd,mask_corr,(ad->cl * sizeof (int)))<0)
	    {
		G_fatal_error("reading mask_corr");
		return ERRORE;
	    }
	}
	G_set_f_null_value(&prevCell,1);
	G_set_f_null_value(&corrCell,1);
	for(i=0; i < ad->cl; i++)/* for each cell in the row */
	{
	    area++;
	    corrCell=buf_corr[i+ad->x];
	    if(masked && mask_corr[i+ad->x]==0)
	    {
		G_set_f_null_value(&corrCell,1);
		area--;
	    }
	    if(!(G_is_null_value(&corrCell,FCELL_TYPE)))
	    {
		supCell=buf_sup[i+ad->x];
		
		if(   ( (!G_is_null_value(&prevCell,FCELL_TYPE)) ) && (corrCell!=prevCell)   )
		{
		    int r=0;
		    c1.val.dc=corrCell;
		    c2.val.dc=prevCell;
		    r=updateCoppia(cc,c1,c2,totCoppie);
		}
		
		
		if(   ( !(G_is_null_value(&supCell,FCELL_TYPE)) ) && (corrCell!=supCell)   )
		{
		    int r=0;
		    c1.val.fc=corrCell;
		    c2.val.fc=prevCell;
		    r=updateCoppia(cc,c1,c2,totCoppie);
		}
		
	    }	
	    prevCell=buf_corr[i+ad->x];
	}
	
	if (masked)
	    mask_sup=mask_corr;
    }
    
    
    /* calcolo dell'indice */
    if(area==0)
	indice=0;
    else
    {
	for (i=0;i<totCoppie;i++)
	{
	    double ee,dd;
	    ee=(double)(cc[i]->e);
	    dd=(double)(cc[i]->d);
	    somma=somma+(ee*dd);
	}
	indice=somma*10000/area;
    }
    *result=indice;
    if (masked)
    {
    	G_free(mask_corr);
        G_free(mask_sup);
    }
    return OK; 	
}



int addCoppia(Coppie * cc,  generic_cell ce1,  generic_cell ce2, double pe, long tc,long * siz)
{
    generic_cell cs;
    long it=0;
    CoppiaPesata * cp;
    CoppiaPesata * cp_tmp;
    int ris;
    
    
    ris=equalsGenericCell(ce1,ce2);
    if (ris==DIFFERENT_TYPE)
	return ERR;
    if (ris==HIGHER)
    {
	cs=ce2;
	ce2=ce1;
	ce1=cs;
    }
    
    switch(ce1.t)
    {
	case CELL_TYPE :
	{ 
	    if((G_is_null_value(&ce1.val.c,CELL_TYPE)) || (G_is_null_value(&ce2.val.c,CELL_TYPE)))
		return ERR;   
	    break;
	}
	case DCELL_TYPE :
	{ 
	    if((G_is_null_value(&ce1.val.dc,DCELL_TYPE)) || (G_is_null_value(&ce2.val.dc,DCELL_TYPE)))
		return ERR;
	    break;
	}
	case FCELL_TYPE:
	{
	    if((G_is_null_value(&ce1.val.fc,FCELL_TYPE)) || (G_is_null_value(&ce2.val.fc,FCELL_TYPE)))
		return ERR;
	    break;
	}
	default:
	{
	    G_fatal_error("data type unknown");
	    return ERRORE;
	}
    }
    
    while(it<tc)
    {
	cp_tmp=cc[it];

	if ((equalsGenericCell((cp_tmp->c1),ce1)==EQUAL) && (equalsGenericCell((cp_tmp->c2),ce2)==EQUAL))
	{
	    if((cp_tmp->d )!= pe)
	    {
		G_warning("different weight for the same cell type. I consider right the first");
	    }
	    
	    return PRES;
	}
	it++;
    }
    
    /* if the pair of cell there isn't, add the pair */
    cp=G_malloc(sizeof(CoppiaPesata));
    if (cp==NULL)
    {
	return ERR;
    }
    cp->c1=ce1;
    cp->c2=ce2;
    cp->d=pe;
    cp->e=0;

    
    if(it==(*siz))/*se l'array e' pieno aggiungo 10 posizioni*/
    {
	*siz=*siz+10;
	cc=G_realloc(cc,(*siz)*sizeof(CoppiaPesata));
    }
    if(cc==NULL)
	return ERR;
    
    cc [it]=G_malloc(sizeof(CoppiaPesata));
    if(cc[it]==NULL)
	return ERR;
    cc[it]=cp;
	
    return ADD;
}



int updateCoppia(Coppie * cc,  generic_cell c1,  generic_cell c2, long tc)		
{
    generic_cell cs;
    long k=0;
    int ris;
    
    
    if(cc==NULL)
	return ERR;
    
    switch(c1.t)
    {
	case CELL_TYPE:
	{ 
	    if((G_is_null_value(&(c1.val.c),CELL_TYPE)) || (G_is_null_value(&(c2.val.c),CELL_TYPE)))
		return ERR;	    
	    break;
	}
	case DCELL_TYPE:
	{ 
	    if((G_is_null_value(&(c1.val.dc),DCELL_TYPE)) || (G_is_null_value(&(c2.val.dc),DCELL_TYPE)))
		return ERR;
	    break;
	}
	case FCELL_TYPE:
	{
	    if((G_is_null_value(&(c1.val.fc),FCELL_TYPE)) || (G_is_null_value(&(c2.val.fc),FCELL_TYPE)))
		return ERR;
	    break;
	}
	default:
	{
	    G_fatal_error("data type unknown");
	    return ERRORE;
	}
    }    

    ris=equalsGenericCell(c1,c2);
    
    if (ris==UNKNOWN || ris==DIFFERENT_TYPE)
	return ERR;
    if (ris==HIGHER)
    {
	cs=c2;
	c2=c1;
	c1=cs;
    }
    
    while(k<tc)
    {

	if ((equalsGenericCell((cc[k]->c1),c1)==EQUAL) && (equalsGenericCell((cc[k]->c2),c2)==EQUAL) )
	{
	    (cc[k]->e)++;
	    return OK;
	}
	else
	{
	    ;
	}
	k++;
    }
    
    return OK;
}

 
