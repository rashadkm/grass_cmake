#include <stdio.h>
#include <signal.h>
#include "graph.h"
#include "monitors.h"
#include "gis.h"
#include <errno.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/msg.h>

extern int errno;

#define BUFFERSIZ   2048

/*
static unsigned char outbuf[BUFFERSIZ] ;
*/
static struct MESS {long mtype; unsigned char outbuf[BUFFERSIZ];} sb,rb;
static int cursiz = 0 ;
static int n_read = 0 ;
static int atbuf = 0 ;
static int no_mon ;

static int _rfd;
static int _wfd;

char *getenv();

static int unlock_driver (int);
static int find_process (int);
static int get_ids (char *,int *,int);
static char *who_locked_driver();
static int lock_driver (int);
static int lockfile(char *);
static int fifoto( char *,char *,int);
static int sync_driver(char *);
static void dead(int);
static void (*sigalarm)();
static void (*sigint)();
static void (*sigquit)();
static int _get(char *,int);
static int _rec (char *);


int
_send_ident(anint)
    int anint ;
{
    unsigned char achar ;
    achar = anint;

    if( (cursiz+2) >= BUFFERSIZ)
        flushout() ;
    sb.outbuf[cursiz++] = COMMAND_ESC ;
    sb.outbuf[cursiz++] = achar ;

    return 0;
}

int
_send_char (achar)
    unsigned char *achar ;
{
    if( (cursiz+2) >= BUFFERSIZ)
        flushout() ;
    sb.outbuf[cursiz++] = *achar ;
    if (*achar == COMMAND_ESC)
        sb.outbuf[cursiz++] = 0 ;

    return 0;
}

int
_send_char_array(num, achar)
    register int num ;
    register unsigned char *achar ;
{
    while (num-- > 0)
        _send_char (achar++);

    return 0;
}

int
_send_int_array(num, anint)
    int num ;
    int *anint ;
{
    _send_char_array(num * sizeof(int), (unsigned char *)anint) ;

    return 0;
}

int
_send_float_array(num, afloat)
    int num ;
    float *afloat ;
{
    _send_char_array(num * sizeof(float), (unsigned char *)afloat) ;

    return 0;
}

int
_send_int(anint)
    int *anint ;
{
    _send_char_array(sizeof(int), (unsigned char *)anint) ;

    return 0;
}

int
_send_float(afloat)
    float *afloat ;
{
    _send_char_array(sizeof(float), (unsigned char *)afloat) ;

    return 0;
}

int
_send_text(text)
    char *text ;
{
    _send_char_array(1 + strlen(text), (unsigned char *)text) ;

    return 0;
}

int
_get_char(achar)
    char *achar ;
{
    flushout() ;
    _get (achar, 1);

    return 0;
}

int
_get_int(anint)
    int *anint ;
{
    flushout() ;
    _get( (char *)anint, sizeof(int));

    return 0;
}

int
_get_float(afloat)
    float *afloat ;
{
    flushout() ;
    _get( (char *)afloat, sizeof(float));

    return 0;
}

int
_get_text (buf)
    char *buf;
{
    char *b;

    b = buf;
    do
	_get_char (b);
    while (*b++ != 0);

    return 0;
}

static int
_get(buf, n)
char *buf;
int n;
{
    int stat;
    while (n-- > 0) _rec(buf++);

    return 0;
}


static int
_rec (buf)
    char *buf;
{
    if (atbuf == n_read)
    {
	atbuf = 0;
        n_read = msgrcv (_rfd, (struct msgbuff *) &rb, sizeof rb.outbuf , 0L ,0);
    }
    *buf = rb.outbuf[atbuf++];

    return 0;
}

int
flushout(void)
{
    sb.mtype = 1L;
    if (cursiz)
    {
        msgsnd (_wfd, (struct msgbuff *) &sb, (size_t) cursiz, 0);
        cursiz = 0 ;
    }

    return 0;
}



/* R_open_driver for communication over fifos -- 7 Oct 87 */
/* In verbose mode, errors print a message and exit.  In quiet mode, errors */
/* return a code and no messages are printed.  The flag quiet is set */
/* by calling R__open_quiet just before calling R_open_driver. */
/* Returns in quiet mode opens are defined in open.h */

#include "open.h"
static int quiet = 0;        /* #9 Sep 87 */


int
R_open_driver()
{
    int verbose;
    int try, key, lock;
    char our_input_file[512], our_output_file[512];
    struct MON_CAP *mon, *R_parse_monitorcap();
    char *name, *G__getenv(), *getenv(), *key_string;
    char *user, *who_locked_driver();

    verbose = !quiet;
    quiet = 0;
    if ((name = G__getenv("MONITOR")) == NULL)
    {
        if (verbose)           /* #31 Aug 87 - want error stuff */
        {
            fprintf(stderr,"No graphics monitor has been selected for output.\n");
            fprintf(stderr,"Please run \"d.mon\" to select a graphics monitor.\n");
            exit(-1);
        }
        else
        {
            return(NO_MON);
        }
    }
    else
    {
        if ((mon = R_parse_monitorcap(MON_NAME,name)) == NULL)
        {
            if (verbose)
            {
                fprintf(stderr,"No such graphics monitor as <%s>.\n",name);
                fprintf(stderr,"Please run \"d.mon\" to select a valid graphics monitor.\n");
                exit(-1);
            }
            else
            {
                return(NO_MON);
            }
        }
        else
        {
            key_string = getenv("GIS_LOCK");
            if (key_string == NULL || sscanf(key_string,"%d",&key) != 1 || key <= 0)
		key = 0;
            lock = lock_driver(key);
            if (lock == 0)
            {
                if (verbose)
                {
                    if ((user = who_locked_driver()) == NULL)
                        fprintf(stderr,"Error - Monitor <%s> is in use.\n",name);
                    else
                        fprintf(stderr,"Error - Monitor <%s> is in use by %s.\n",name,user);
                    exit(-1);
                }
                else
                {
                    return(LOCKED);
                }
            }
            if (lock < 0)
            {
                if (verbose)
                {
		    char file[512];
                    fprintf(stderr,"Error - Could not complete locking process for monitor <%s>.\n",name);
		    lockfile(file);
		    fprintf (stderr, "Lock file is %s\n", file);
                    exit(-1);
                }
                else
                {
                    return(LOCK_FAILED);
                }
            }
            sscanf(mon->link,"%s %s",our_output_file,our_input_file);
            if (verbose)
            {
                for (try = 0; try < 2; try++)
                {
                    switch (fifoto (our_input_file,our_output_file,try?15:3))
                    {
                    case -1:
                        fprintf(stderr, "\07Error - Can't set up pipe to graphics device.\n");
                        unlock_driver(1);
                        exit(-1);
                    case 0:
                        if (try)
                        {
                            fprintf (stderr, "Error - Graphics monitor <%s> not running!\n",name);
                            unlock_driver(1);
                            exit(1);
                        }
                        fprintf (stderr, "\07Please start graphics monitor <%s>.\n",name);
                        break;
                    default:
                        sync_driver(name); /* syncronize driver */
                        return(0);
                    }             /* switch */
                }               /* for */
            }
            else /* non-verbose mode */
            {
            /*  switch (fifoto(our_input_file,our_output_file,3)) */
                switch (fifoto(our_input_file,our_output_file,1))
                {
                case -1:
                    unlock_driver(1);
                    return(NO_OPEN);
                case 0:
                    unlock_driver(1);
                    return(NO_RUN);
                default:
                    return(OKOK);
                }
            }
        }
    }

    return 0;
}

int
R__open_quiet()
{
    quiet = 1;

    return 0;
}


/*************************************************
* fifoto(alarm_time)
*      this is the plumbing, the idea is to
*      open fifo pipes for read/write.
*************************************************/

#define READ  0
#define WRITE 1

static int
fifoto(input,output,alarm_time)
    char *input, *output;
{
    no_mon = 0;
    _wfd = msgget(ftok(output,0), 0600);
    _rfd = msgget(ftok(input,0),  0600) ;
    if( (_wfd == -1) || (_rfd == -1) )
        return -1;

    return 1 ;
}

static int
sync_driver(name)
    char *name;
{
    int try;
    int count;
    unsigned char c;
    struct MESS {long mtype; char c[1];} cb;

    _send_ident (BEGIN);
    flushout();

/*
 * look for at least BEGIN_SYNC_COUNT zero bytes
 * then look for COMMAND_ESC
 *
 * try twice. first timeout is warning, second is fatal
 */
    count = 0;
    sigalarm = signal(SIGALRM, dead);
    for (try = 0; try < 2; try++)
    {
        no_mon = 0;
        alarm(try?10:5);
        while(no_mon == 0)
        {
            if (msgrcv (_rfd, (struct msgbuff *) &cb, (size_t) 1, 0L, 0 ) != 1)
            {
                if (no_mon)
                    break; /* from while */
                fprintf (stderr, "ERROR - eof from graphics monitor.\n");
                exit(-1);
            }
	    c = cb.c[0];
            if (c == 0)
                count++;
            else if (c == COMMAND_ESC && count >= BEGIN_SYNC_COUNT)
                break;
            else
                count = 0;  /* start over */
        }
        alarm(0);
        signal(SIGALRM, sigalarm);
        if (no_mon == 0)
            return 1;   /* ok! */
        if (try)
            break;

        fprintf (stderr, "\7Warning - no response from graphics monitor <%s>.\n",
            name);
        fprintf (stderr, "Check to see if the mouse is still active.\n");
        signal(SIGALRM, dead);
    }
    fprintf (stderr, "ERROR - no response from graphics monitor <%s>.\n",
        name);
    exit(-1);
}

static void
dead(int dummy)
{
    no_mon = 1 ;
}

int
_hold_signals (hold)
{
    if (hold)
    {
        sigint  = (void (*)()) signal (SIGINT, SIG_IGN);
        sigquit = (void (*)()) signal (SIGQUIT, SIG_IGN);
    }
    else
    {
        signal (SIGINT, sigint);
        signal (SIGQUIT, sigquit);
    }

    return 0;
}

/******************************************************************
* lock_driver (pid)
*
*   this routine "locks" the driver for process pid as follows:
*
*   1. if lockfile exists, 2 old pids are read out of the file.
*
*      the first pid is the global lock, the second is the
*      process id lock. If both match the pid and the current
*      pid, nothing needs to be done.
*
*   2. If the 2nd pid is not the same as the current process
*      and that process is still running, then can't lock
*
*   3. If the first pid is not the same and that process is still
*      running, then can't lock
*
*   4. the driver is locked by writing pid and curretn pid into the file.
*
*   5. The user's name is also written to the file
*
* note: since file is created by this routine, it shouldn't be
*       a file that is used for any other purpose.
*
*       also, this lock mechanism is advisory. programs must call this
*       routine and check the return status.
*
* returns:
*       1 ok lock is in place.
*       0 could not lock because another process has the file locked already
*      -1 error. could not create the lock file
*      -2 error. could not read the lock file.
*      -3 error. could not write the lock file.
******************************************************************/
#define LOCK_OK 1
#define ALREADY_LOCKED 0
#define CANT_CREATE -1
#define CANT_READ -2
#define CANT_WRITE -3

static int
lockfile(file)
    char *file;
{
	char *G__getenv();
	char *G_getenv();
	char *G__machine_name();
	char *name;
	char *disp, display[64] ;
	char *base ;
	char *hostname ;
	int mask;
	char lock_dir[256] ;

/* get machine name, if it has one */
    hostname = G__machine_name();
    if (hostname == NULL) hostname = "";
    for(name=hostname; *name!=NULL; name++) /* use only first part */
	if (*name == '.')
	{
	    *name = 0 ;
	    break ;
    }

    disp   = getenv("DISPLAY") ;
    name   = G__getenv ("MONITOR");
    base   = G_getenv ("GISBASE");

    if(disp)
	{
		if(strncmp(disp,"unix:",5))
			strcpy(display, disp) ;
		else
		{
			char *disptr ;
			disptr = disp + 5 ;
			sprintf(display,"%s:%s",hostname,disptr) ;
		}
        sprintf (file, "%s/locks/%s/%s/%s", base, hostname, display, name);
        sprintf (lock_dir, "%s/locks/%s/%s", base, hostname, display);
	}
    else
	{
        sprintf (file, "%s/locks/%s/%s", base, hostname, name);
        sprintf (lock_dir, "%s/locks/%s", base, hostname);
	}

	if (access(lock_dir, 0) == 0)
		return(0) ;

/* make sure lock directory exists */
    *file = 0;
    sprintf (lock_dir, "%s/locks/%s", base, hostname);
    mask=umask(0) ;
    mkdir(lock_dir,0777) ;
    umask(mask);

    if(disp)
    {
        sprintf (lock_dir, "%s/locks/%s/%s", base, hostname, display);
        mask=umask(0) ;
        mkdir(lock_dir,0777) ;
	umask(mask);
    }

    return 0;
}

#include <pwd.h>
static int
lock_driver (lock_pid)
{
    char file[512];
    int fd;
    int mask;
    int n;
    int id[3];
    int me;

    lockfile(file);
    me = getpid();
    if (access (file, 0) == 0)      /* file exists */
    {
        for (n = 0; n < 2; n++)
        {
            if (get_ids (file, id, 2))
                break;
            if (n == 0)
                sleep(1); /* allow time for file creator to write its pid */
        }
        if (n == 2)
            return CANT_READ;
        if (lock_pid == id[1] && me == id[0])
            return LOCK_OK;
        if (me != id[0] && id[0] >= 0 && find_process (id[0]))
            return ALREADY_LOCKED;
        if (lock_pid != id[1] && find_process (id[1]))
            return ALREADY_LOCKED;
    }
    mask = umask (0);
    fd = creat (file, 0666) ;
    umask (mask);
    if (fd < 0)
        return CANT_CREATE;
    id[0] = me;
    id[1] = lock_pid;
    id[2] = getuid();
    if (write(fd, id, sizeof id) != sizeof id)
    {
        close (fd);
        return CANT_WRITE;
    }
    close (fd);
    return LOCK_OK;
}

static char *
who_locked_driver()
{
    char file[512];
    int id[3];
    struct passwd *pw, *getpwuid();

    lockfile (file);
    if (!get_ids (file, id, 3))
        return ((char *)NULL);
    if ((pw = getpwuid(id[2])) == NULL)
        return ((char *)NULL);
    return (pw->pw_name);
}

static int
get_ids (file, id, x)
    char *file;
    int *id;
{
    int fd;
    int n;

    if ((fd = open (file, 0)) < 0)
        return 0;
    n = read (fd, id, x*sizeof (*id));
    close (fd);
    return (n == x*sizeof (*id));
}

static int
find_process (pid)
{
/* attempt to kill pid with NULL signal. if success, then
   process pid is still running. otherwise, must check if
   kill failed because no such process, or because user is
   not owner of process
*/
    if (pid <= 0)
	return 0;/* no such process */

    if (kill (pid, 0) == 0)
        return 1;
    return errno != ESRCH;
}

static int
unlock_driver (wipeout)
{
    char file[512];
    int fd;
    int pid;

    lockfile(file);
    if (*file == 0) return 0;
/*
 * two flavors of unlock.
 *   wipeout==0 for current process only
 *   wipeout==1 for global locking key as well
 */
    if (access (file,0) != 0)
        return 0;
    if (!wipeout)
    {
        fd = open (file, 1);
        if (fd < 0) wipeout = 1;
    }
    if (!wipeout)
    {
        pid = -1;
        if(write (fd, &pid, sizeof(pid)) != sizeof(pid))
            wipeout = 1;
        close (fd);
    }
    if (wipeout)
    {
        unlink (file);
        if (access (file,0) != 0)
            return 1;
    }
    return -1;
}

int
R_kill_driver()             /* #31 Aug 87 - stop a driver */
{
    _send_ident(GRAPH_CLOSE);       /* #31 Aug 87 - tell driver to exit */
    flushout();
/*
    msgctl (_rfd, IPC_RMID);
    msgctl (_wfd, IPC_RMID);
*/
    R_release_driver();

    return 0;
}

int
R_close_driver()
{
    R_stabilize();
/*
    msgctl (_rfd, IPC_RMID);
    msgctl (_wfd, IPC_RMID);
*/
    unlock_driver(0);

    return 0;
}

int
R_release_driver()
{
    unlock_driver (1);

    return 0;
}

int
R_stabilize()
{
    char c;

    flushout();
    _send_ident (RESPOND);
    _get_char (&c);

    return 0;
}
