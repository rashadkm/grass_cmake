/***** Fast Fourier Transformation of Two Dimensional Satellite Data *****/

#include <grass/config.h>

#if defined(HAVE_FFTW_H) || defined(HAVE_DFFTW_H) || defined(HAVE_FFTW3_H)

#ifdef HAVE_FFTW_H
#include <fftw.h>
#endif

#ifdef HAVE_DFFTW_H
#include <dfftw.h>
#endif

#ifdef HAVE_FFTW3_H
#include <fftw3.h>
#define c_re(c) ((c)[0])
#define c_im(c) ((c)[1])
#endif

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <grass/gmath.h>
#include <grass/gis.h>

/*****************************************************************************
 *                                                                           *
 * Fast Fourier Transform Routine for two-dimensional array                  *
 *                                                                           *
 * Input arguments: i_sign - direction of transform :                        *
 *                                -1 -> transform, +1 -> inverse transform   *
 *                  DATA   - pointer to a complex linear array in row major  *
 *                           order containing the data and the result.       *
 *                  NN     - value of DATA dimension  (dimc*dimr)            *
 *                  dimc   - value of image column dimension (max power of 2)*
 *                  dimr   - value of image row dimension (max power of 2)   *
 *                                                                           *
 * Note: if passing real data to fft() forward transform (especially when    *
 *       using fft() in a loop), you have to explicitly (re-)initialise the  *
 *       imaginary part to zero (DATA[1][i]=0.0)                             *
 *                                                                           *
 *****************************************************************************/

int fft(int i_sign, double *DATA[2], int NN, int dimc, int dimr)
{
#ifdef HAVE_FFTW3_H
	fftw_plan plan;
#else
	fftwnd_plan plan;
#endif
	fftw_complex *data;
	double norm;
	int i;

	norm = 1.0 / sqrt(NN);

	data = (fftw_complex *) G_malloc(NN * sizeof(fftw_complex));

	for (i = 0; i < NN; i++)
	{
		c_re(data[i]) = DATA[0][i];
		c_im(data[i]) = DATA[1][i];
	}

#ifdef HAVE_FFTW3_H
	plan = fftw_plan_dft_2d(
		dimc, dimr, data, data,
		(i_sign < 0) ? FFTW_FORWARD : FFTW_BACKWARD,
		FFTW_ESTIMATE);

	fftw_execute(plan);

	fftw_destroy_plan(plan);
#else
	plan = fftw2d_create_plan(
		dimc, dimr,
		(i_sign < 0) ? FFTW_FORWARD : FFTW_BACKWARD,
		FFTW_ESTIMATE | FFTW_IN_PLACE);

	fftwnd_one(plan, data, data);

	fftwnd_destroy_plan(plan);
#endif
	for (i = 0; i < NN; i++)
	{
		DATA[0][i] = c_re(data[i]) * norm;
		DATA[1][i] = c_im(data[i]) * norm;
	}

	G_free(data);

	return 0;
}

#endif

