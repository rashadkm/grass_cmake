#include<stdio.h>
#include<stdlib.h>
#include<math.h>

double *dmax_exp (x, n)
  double *x;
  int n;
{
  static double y[2];
  double mean=0.0, zmax, tmax, *xcopy, t, z, fx;
  int i, dcmp();

  if ((xcopy = (double *) malloc (n * sizeof (double))) == NULL)
    fprintf (stderr, "Memory error in dmax_exp\n"), exit (-1);
 
  for (i = 0; i < n; ++i)
  {
    xcopy[i] = x[i];
    mean += x[i];
  }
  mean /=n;
  qsort (xcopy, n, sizeof (double), dcmp);
  for (i = 0; i < n; ++i)
  {
    fx = 1-exp(-xcopy[i]/mean);
    z = (double) (i+1) / (double) n - fx;
    t = fx - (double) i / (double) n;
    if (i == 0 || z > zmax)
      zmax = z;
    if (i == 0 || t > tmax)
      tmax = t;
  }
  y[0]=zmax;
  y[1]=tmax;
  free(xcopy);
  return y;
}
