/* openvect.c */
char *openvect(char *);
/* what.c */
int what(int, int, int, int, int);
int show_buttons(int);
/* attr.c */
int disp_attr(char *, char *, char *, char *, int);

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL	extern
#endif

GLOBAL	char **vect;
GLOBAL	int nvects;
GLOBAL	struct Map_info *Map;
//GLOBAL	struct Categories *Cats;

