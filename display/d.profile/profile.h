#include "gis.h"

/* Define ANOTHER_BUTTON to click conveniently for two button mouse */
#define ANOTHER_BUTTON

#define	LEFT	1

#ifndef ANOTHER_BUTTON
#	define MIDDLE	2
#	define RIGHT	3
#else
#	define MIDDLE	3
#	define RIGHT	2
#endif


struct windows
{
        char *name ;
        float bot, top, left, right ;
} ;

struct ProfileNode
   {
   CELL   cat;
   struct ProfileNode *next;
   };

struct Profile
   { 
   struct Cell_head window;
   double n1,
          e1,
          n2,
          e2;
   struct ProfileNode *ptr;
   long int count;
   CELL MinCat,
        MaxCat;
   }; 

#ifdef MAIN
struct windows windows[] =
        {
        {"mou", 85,  100,   0,  50},
        {"sta", 85,  100,  50, 100},
        {"map",  0,   85,   0,  50},
	{"orig", 0,  100,   0,  1009}
        } ;

struct windows profiles[] =
        {
        {"pro1", 64,  85,  50, 100},
        {"pro2", 43,  64,  50, 100},
        {"pro3", 22,  43,  50, 100},
        {"pro4",  0,  22,  50, 100}
        } ;
#else
extern struct windows windows[];
extern struct windows profiles[];
#endif MAIN

#define MOU     windows[0]
#define STA     windows[1]
#define MAP     windows[2]
#define ORIG     windows[3]

/* DrawText.c */
int DrawText(int, int, int, char *);
/* DumpProfile.c */
int DumpProfile(struct Profile);
/* ExtractProf.c */
int ExtractProfile(struct Profile *, char *, char *);
/* InitProfile.c */
int InitProfile(struct Profile *, struct Cell_head, double, double, double, double);
/* PlotProfile.c */
int PlotProfile(struct Profile, char *, int, int);
/* Range.c */
int WindowRange(char *, char *, int *, int *);
int quick_range(char *, char *, long *, long *);
int slow_range(char *, char *, long *, long *);
/* What.c */
int What(char *, char *, struct Cell_head, double, double);
/* bnw_line.c */
int black_and_white_line(int, int, int, int);
/* show.c */
int show_cat(int, char *, int, char *);
int show_utm(double, double);
int show_mouse(void);
