
#include <stdlib.h>

#include "expression.h"
#include "func_proto.h"

/**********************************************************************
float(x)
  converts x to float
**********************************************************************/

int 
f_float(int argc, const int *argt, void **args)
{
	FCELL *res = args[0];
	int i;

	if (argc < 1)
		return E_ARG_LO;
	if (argc > 1)
		return E_ARG_HI;

	if (argt[0] != FCELL_TYPE)
		return E_RES_TYPE;

	switch (argt[1])
	{
	case CELL_TYPE:
	{
		CELL *arg1 = args[1];
		for (i = 0; i < columns; i++)
			if (IS_NULL_C(&arg1[i]))
				SET_NULL_F(&res[i]);
			else
				res[i] = (FCELL) arg1[i];
		return 0;
	}
	case FCELL_TYPE:
	{
		FCELL *arg1 = args[1];
		for (i = 0; i < columns; i++)
			if (IS_NULL_F(&arg1[i]))
				SET_NULL_F(&res[i]);
			else
				res[i] = (FCELL) arg1[i];
		return 0;
	}
	case DCELL_TYPE:
	{
		DCELL *arg1 = args[1];
		for (i = 0; i < columns; i++)
			if (IS_NULL_D(&arg1[i]))
				SET_NULL_F(&res[i]);
			else
				res[i] = (FCELL) arg1[i];
		return 0;
	}
	default:
		return E_INV_TYPE;
	}
}

int 
c_float(int argc, int *argt)
{
	if (argc < 1)
		return E_ARG_LO;
	if (argc > 1)
		return E_ARG_HI;

	argt[0] = FCELL_TYPE;
/*	argt[1] = argt[1];	*/

	return 0;
}

