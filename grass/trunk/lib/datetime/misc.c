#include "datetime.h"

int 
datetime_is_leap_year (int year, int ad)
{
    if (year == 0)
	return datetime_error (-1, "datetime_is_leap_year(): illegal year");
    if (!ad) return 0; /* BC */
    if (year < 0) return 0; /* ?? */

    return((year%4 == 0 && year%100 != 0) || year%400 == 0);
}

int 
datetime_days_in_year (int year, int ad)
{
    if (year == 0)
	return datetime_error (-1, "datetime_days_in_year(): illegal year");

    if(datetime_is_leap_year(year,ad))
	return 366;
    else
	return 365;
}

int 
datetime_days_in_month (int year, int month, int ad)
{
    static int days[12] = {31,28,31,30,31,30,31,31,30,31,30,31};

    if (month < 1 || month > 12)
	return datetime_error (-1, "datetime_days_in_month(): illegal month");

    if(month == 2 && datetime_is_leap_year(year,ad))
	    return(29);
    return(days[month - 1]);
}

