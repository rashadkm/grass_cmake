#include <unistd.h>
#include <stdio.h>
#include <signal.h>
#include <sys/types.h>

#ifdef __MINGW32__
#  include <io.h>
#  include <fcntl.h>
#  include <process.h>
#else
#  include <sys/wait.h>
#  define tst(a,b)        (*mode == 'r'? (b) : (a))
#endif

#include "gis.h"

#define READ      0
#define WRITE     1

static  int     popen_pid[50];

FILE *G_popen(
    char    *cmd,
    char    *mode)
{

#ifdef __MINGW32__

    int thepipes[2];
    FILE *rv = NULL;

    fflush (stdout);
    fflush (stderr);

    /*setvbuf ( stdout, NULL, _IONBF, 0 );*/

    if ( _pipe ( thepipes, 256, O_BINARY ) != -1 ) {
        execl ( "cmd", "cmd", "/c", cmd, 0 );
	close ( thepipes[WRITE] );
	rv = fdopen ( thepipes[READ], mode ); 
    }

    return ( rv );

#else /* __MINGW32__ */

    int p[2];
    int me, you, pid;

    fflush (stdout);
    fflush (stderr);

    if(pipe(p) < 0)
	return NULL;
    me = tst(p[WRITE], p[READ]);
    you = tst(p[READ], p[WRITE]);
    if((pid = fork()) == 0)
    {
/* me and you reverse roles in child */
	close(me);
	close(tst(0, 1));
	dup(you);
	close(you);
	execl("/bin/sh", "sh", "-c", cmd, 0);
	_exit(1);
    }

    if(pid == -1)
	return NULL;
    popen_pid[me] = pid;
    close(you);

    return(fdopen(me, mode));

#endif /* __MINGW32__ */

}

int G_pclose( FILE *ptr)
{
#ifdef __MINGW32__
    void (*sigint)();
#else    
    void (*sighup)(), (*sigint)(), (*sigquit)();
#endif
    int f, r;
    int status;

    f = fileno(ptr);
    fclose(ptr);

    sigint  = signal(SIGINT, SIG_IGN);
#ifdef __MINGW32__
    _cwait ( &status, popen_pid[f], WAIT_CHILD );
    if ( 0 & status ) {
      status = -1;
    }
#else
    sigquit = signal(SIGQUIT, SIG_IGN);
    sighup  = signal(SIGHUP, SIG_IGN);
    while((r = wait(&status)) != popen_pid[f] && r != -1)
	    ;
    if(r == -1)
	status = -1;
#endif

    signal(SIGINT, sigint);

#ifndef __MINGW32__
    signal(SIGQUIT, sigquit);
    signal(SIGHUP, sighup);
#endif

    return(status);
}
