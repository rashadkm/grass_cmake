#include <stdlib.h>
#include "watershed.h"

int free_input (INPUT *input)
{
	if (input->com_line_ram) free (input->com_line_ram);
	if (input->com_line_seg) free (input->com_line_seg);
	free (input->haf_name);
	free (input->ar_file_name);
	free (input->accum_name);

	return 0;
}

int free_output (OUTPUT *output)
{
	int	c;

	free (output->basin_facts);
	free (output->file_name);
	for (c = output->num_maps - 1; c >= 0; c--) {
		free (output->maps[c].name);
	}
	free (output->maps);

	return 0;
}
