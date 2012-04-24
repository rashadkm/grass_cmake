"""!@package grass.temporal

@brief GRASS Python scripting module (temporal GIS functions)

Temporal GIS unit tests

Usage:

@code
import grass.temporal as tgis

tgis.test_increment_datetime_by_string()
...
@endcode

(C) 2008-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""
from datetime import datetime, date, time, timedelta
import grass.script.core as core
from temporal_granularity import *
from datetime_math import *
from space_time_datasets import *

###############################################################################

def test_increment_datetime_by_string():

    # First test
    print "# Test 1"
    dt = datetime(2001, 9, 1, 0, 0, 0)
    string = "60 seconds, 4 minutes, 12 hours, 10 days, 1 weeks, 5 months, 1 years"

    dt1 = datetime(2003,2,18,12,5,0)
    dt2 = increment_datetime_by_string(dt, string)

    print dt
    print dt2

    delta = dt1 -dt2

    if delta.days != 0 or delta.seconds != 0:
        core.error("increment computation is wrong %s" % (delta))

    # Second test
    print "# Test 2"
    dt = datetime(2001, 11, 1, 0, 0, 0)
    string = "1 months"

    dt1 = datetime(2001,12,1)
    dt2 = increment_datetime_by_string(dt, string)

    print dt
    print dt2

    delta = dt1 -dt2

    if delta.days != 0 or delta.seconds != 0:
        core.error("increment computation is wrong %s" % (delta))

    # Third test
    print "# Test 3"
    dt = datetime(2001, 11, 1, 0, 0, 0)
    string = "13 months"

    dt1 = datetime(2002,12,1)
    dt2 = increment_datetime_by_string(dt, string)

    print dt
    print dt2

    delta = dt1 -dt2

    if delta.days != 0 or delta.seconds != 0:
        core.error("increment computation is wrong %s" % (delta))

    # 4. test
    print "# Test 4"
    dt = datetime(2001, 1, 1, 0, 0, 0)
    string = "72 months"

    dt1 = datetime(2007,1,1)
    dt2 = increment_datetime_by_string(dt, string)

    print dt
    print dt2

    delta = dt1 -dt2

    if delta.days != 0 or delta.seconds != 0:
        core.error("increment computation is wrong %s" % (delta))

###############################################################################

def test_adjust_datetime_to_granularity():

    # First test
    print "Test 1"
    dt = datetime(2001, 8, 8, 12,30,30)
    result = adjust_datetime_to_granularity(dt, "5 seconds")
    correct =  datetime(2001, 8, 8, 12,30,30)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # Second test
    print "Test 2"
    result = adjust_datetime_to_granularity(dt, "20 minutes")
    correct =  datetime(2001, 8, 8, 12,30,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # Third test
    print "Test 2"
    result = adjust_datetime_to_granularity(dt, "20 minutes")
    correct =  datetime(2001, 8, 8, 12,30,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 4. test
    print "Test 4"
    result = adjust_datetime_to_granularity(dt, "3 hours")
    correct =  datetime(2001, 8, 8, 12,00,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 5. test
    print "Test 5"
    result = adjust_datetime_to_granularity(dt, "5 days")
    correct =  datetime(2001, 8, 8, 00,00,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 6. test
    print "Test 6"
    result = adjust_datetime_to_granularity(dt, "2 weeks")
    correct =  datetime(2001, 8, 6, 00,00,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 7. test
    print "Test 7"
    result = adjust_datetime_to_granularity(dt, "6 months")
    correct =  datetime(2001, 8, 1, 00,00,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 8. test
    print "Test 8"
    result = adjust_datetime_to_granularity(dt, "2 years")
    correct =  datetime(2001, 1, 1, 00,00,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 9. test
    print "Test 9"
    result = adjust_datetime_to_granularity(dt, "2 years, 3 months, 5 days, 3 hours, 3 minutes, 2 seconds")
    correct =  datetime(2001, 8, 8, 12,30,30)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 10. test
    print "Test 10"
    result = adjust_datetime_to_granularity(dt, "3 months, 5 days, 3 minutes")
    correct =  datetime(2001, 8, 8, 12,30,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

    # 11. test
    print "Test 11"
    result = adjust_datetime_to_granularity(dt, "3 weeks, 5 days")
    correct =  datetime(2001, 8, 8, 00,00,00)

    delta = correct - result 

    if delta.days != 0 or delta.seconds != 0:
        core.error("Granularity adjustment computation is wrong %s" % (delta))

###############################################################################

def test_compute_datetime_delta():

    print "Test 1"
    start = datetime(2001, 1, 1, 00,00,00)
    end = datetime(2001, 1, 1, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["second"]
    correct = 0

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 2"
    start = datetime(2001, 1, 1, 00,00,14)
    end = datetime(2001, 1, 1, 00,00,44)

    comp = compute_datetime_delta(start, end)

    result = comp["second"]
    correct = 30

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 3"
    start = datetime(2001, 1, 1, 00,00,44)
    end = datetime(2001, 1, 1, 00,01,14)

    comp = compute_datetime_delta(start, end)

    result = comp["second"]
    correct = 30

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 4"
    start = datetime(2001, 1, 1, 00,00,30)
    end = datetime(2001, 1, 1, 00,05,30)

    comp = compute_datetime_delta(start, end)

    result = comp["second"]
    correct = 300

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 5"
    start = datetime(2001, 1, 1, 00,00,00)
    end = datetime(2001, 1, 1, 00,01,00)

    comp = compute_datetime_delta(start, end)

    result = comp["minute"]
    correct = 1

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 6"
    start = datetime(2011,10,31, 00,45,00)
    end = datetime(2011,10,31, 01,45,00)

    comp = compute_datetime_delta(start, end)

    result = comp["minute"]
    correct = 60

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 7"
    start = datetime(2011,10,31, 00,45,00)
    end = datetime(2011,10,31, 01,15,00)

    comp = compute_datetime_delta(start, end)

    result = comp["minute"]
    correct = 30

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 8"
    start = datetime(2011,10,31, 00,45,00)
    end = datetime(2011,10,31, 12,15,00)

    comp = compute_datetime_delta(start, end)

    result = comp["minute"]
    correct = 690

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 9"
    start = datetime(2011,10,31, 00,00,00)
    end = datetime(2011,10,31, 01,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["hour"]
    correct = 1

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 10"
    start = datetime(2011,10,31, 00,00,00)
    end = datetime(2011,11,01, 01,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["hour"]
    correct = 25

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 11"
    start = datetime(2011,10,31, 12,00,00)
    end = datetime(2011,11,01, 06,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["hour"]
    correct = 18

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 12"
    start = datetime(2011,11,01, 00,00,00)
    end = datetime(2011,12,01, 01,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["hour"]
    correct = 30 * 24 + 1

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))


    print "Test 13"
    start = datetime(2011,11,01, 00,00,00)
    end = datetime(2011,11,05, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["day"]
    correct = 4

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 14"
    start = datetime(2011,10,06, 00,00,00)
    end = datetime(2011,11,05, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["day"]
    correct = 30

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 15"
    start = datetime(2011,12,02, 00,00,00)
    end = datetime(2012,01,01, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["day"]
    correct = 30

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 16"
    start = datetime(2011,01,01, 00,00,00)
    end = datetime(2011,02,01, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["month"]
    correct = 1

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 17"
    start = datetime(2011,12,01, 00,00,00)
    end = datetime(2012,01,01, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["month"]
    correct = 1

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 18"
    start = datetime(2011,12,01, 00,00,00)
    end = datetime(2012,06,01, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["month"]
    correct = 6

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 19"
    start = datetime(2011,06,01, 00,00,00)
    end = datetime(2021,06,01, 00,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["year"]
    correct = 10

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 20"
    start = datetime(2011,06,01, 00,00,00)
    end = datetime(2012,06,01, 12,00,00)

    comp = compute_datetime_delta(start, end)

    result = comp["hour"]
    d = end - start
    correct = 12 + d.days * 24

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 21"
    start = datetime(2011,06,01, 00,00,00)
    end = datetime(2012,06,01, 12,30,00)

    comp = compute_datetime_delta(start, end)

    result = comp["minute"]
    d = end - start
    correct = d.days * 24 * 60 + 12 * 60 + 30

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 22"
    start = datetime(2011,06,01, 00,00,00)
    end = datetime(2012,06,01, 12,00,05)

    comp = compute_datetime_delta(start, end)

    result = comp["second"]
    d = end - start
    correct = 5 + 60 * 60 * 12 + d.days * 24 * 60 * 60

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 23"
    start = datetime(2011,06,01, 00,00,00)
    end = datetime(2012,06,01, 00,30,00)

    comp = compute_datetime_delta(start, end)

    result = comp["minute"]
    d = end - start
    correct = 30 + d.days * 24 * 60

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

    print "Test 24"
    start = datetime(2011,06,01, 00,00,00)
    end = datetime(2012,06,01, 00,00,05)

    comp = compute_datetime_delta(start, end)

    result = comp["second"]
    d = end - start
    correct = 5 + d.days * 24 * 60 * 60

    delta = correct - result 

    if delta != 0:
        core.error("Compute datetime delta is wrong %s" % (delta))

###############################################################################

def test_compute_relative_time_granularity():            
    

    # First we test intervals

    print "Test 1"
    maps = []
    fact = 5
    start = 1
    end = start * fact
    for i in range(6):
        end = start * fact
        map = raster_dataset(None)
        map.set_relative_time(start, end, "years")
        maps.append(map)
        start = end

    fact = fact - 1
    gran = round(compute_relative_time_granularity(maps))
    if fact - gran != 0:
        core.error("Wrong granularity reference %i != gran %i" % (fact, gran))
 
    print "Test 2"
    maps = []
    fact = 3
    start = 1.0/86400
    end = start * fact
    for i in range(10):
        end = start * fact
        map = raster_dataset(None)
        map.set_relative_time(start, end, "years")
        maps.append(map)
        start = end

    fact = fact - 1
    gran = round(compute_relative_time_granularity(maps) * 86400)
    if fact - gran != 0:
        core.error("Wrong granularity reference %i != gran %i" % (fact, gran))

    print "Test 3 with gaps"
    maps = []
    fact = 3
    start = 1
    end = start + fact
    for i in range(10):
        shift = i*2*fact
        start = shift
        end = start + fact

        map = raster_dataset(None)
        map.set_relative_time(start, end)
        maps.append(map)

    gran = round(compute_relative_time_granularity(maps))
    if fact - gran != 0:
        core.error("Wrong granularity reference %i != gran %i" % (fact, gran))

    # Second we test intervals and points mixed

    print "Test 4 intervals and points"
    maps = []
    fact = 5
    start = 1
    end = start * fact
    count = 0
    for i in range(6):
        end = start * fact
        map = raster_dataset(None)
        if count % 2 == 0:
            map.set_relative_time(start, end)
        else:
            map.set_relative_time(start, None)
        maps.append(map)
        start = end
        count += 1

    fact = fact - 1
    gran = round(compute_relative_time_granularity(maps))
    if fact - gran != 0:
        core.error("Wrong granularity reference %i != gran %i" % (fact, gran))
 
    # Second we test points only
 
    print "Test 5 points only"
    maps = []
    fact = 3
    start = 1.0/86400
    for i in range(10):
        point = (i + 1)*fact*start
        map = raster_dataset(None)
        map.set_relative_time(point, None)
        maps.append(map)

    gran = round(compute_relative_time_granularity(maps) * 86400)
    if fact - gran != 0:
        core.error("Wrong granularity reference %i != gran %i" % (fact, gran))

###############################################################################

def test_compute_absolute_time_granularity():
 

    # First we test intervals

    print "Test 1"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "1 years"
    for i in range(10):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 2"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "3 years"
    for i in range(10):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 3"
    maps = []
    a = datetime(2001, 5, 1)
    increment = "1 months"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 4"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "3 months"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 3"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "1 days"
    for i in range(6):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 4"
    maps = []
    a = datetime(2001, 1, 14)
    increment = "14 days"
    for i in range(6):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 5"
    maps = []
    a = datetime(2001, 3, 1)
    increment = "1 months, 4 days"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    increment = "1 days"
    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 6"
    maps = []
    a = datetime(2001, 2, 11)
    increment = "1 days, 1 hours"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    increment = "25 hours"
    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 7"
    maps = []
    a = datetime(2001, 6, 12)
    increment = "6 hours"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 8"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "20 minutes"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 9"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "5 hours, 25 minutes"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    increment = "325 minutes"
    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 10"
    maps = []
    a = datetime(2001, 1, 1)
    increment = "5 minutes, 30 seconds"
    for i in range(20):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    increment = "330 seconds"
    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 11"
    maps = []
    a = datetime(2001,12,31)
    increment = "60 minutes, 30 seconds"
    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    increment = "3630 seconds"
    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 12"
    maps = []
    a = datetime(2001,12,31, 12, 30, 30)
    increment = "3600 seconds"
    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    # Test absolute time points    

    print "Test 13"
    maps = []
    a = datetime(2001,12,31, 12, 30, 30)
    increment = "3600 seconds"
    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = None
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 14"
    maps = []
    a = datetime(2001,12,31, 00, 00, 00)
    increment = "20 days"
    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = None
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 15"
    maps = []
    a = datetime(2001,12,01, 00, 00, 00)
    increment = "5 months"
    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = None
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    # Test absolute time interval and points    

    print "Test 16"
    maps = []
    a = datetime(2001,12,31, 12, 30, 30)
    increment = "3600 seconds"

    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    a = datetime(2002,02,01, 12, 30, 30)
    for i in range(24):
        start = increment_datetime_by_string(a, increment, i)
        end = None
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

    print "Test 17"
    maps = []
    a = datetime(2001,1,1)
    increment = "2 days"

    for i in range(8):
        start = increment_datetime_by_string(a, increment, i)
        end = increment_datetime_by_string(a, increment, i + 1)
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    a = datetime(2001,02,02)
    for i in range(8):
        start = increment_datetime_by_string(a, increment, i)
        end = None
        map = raster_dataset(None)
        map.set_absolute_time(start, end)
        maps.append(map)

    gran = compute_absolute_time_granularity(maps)
    if increment != gran:
        core.error("Wrong granularity reference %s != gran %s" % (increment, gran))

###############################################################################

def test_spatial_extent_intersection():
    # Generate the extents
    
    A = spatial_extent(north=80, south=20, east=60, west=10, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=80, south=20, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    C = A.intersect(B)
    C.print_info()
    
    if C.get_north() != B.get_north() or C.get_south() != B.get_south() or \
       C.get_west() != B.get_west() or C.get_east() != B.get_east() or \
       C.get_bottom() != B.get_bottom() or C.get_top() != B.get_top():
        core.error("Wrong intersection computation")
        
    B = spatial_extent(north=40, south=30, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    C = A.intersect(B)
    C.print_info()
    
    if C.get_north() != B.get_north() or C.get_south() != B.get_south() or \
       C.get_west() != B.get_west() or C.get_east() != B.get_east() or \
       C.get_bottom() != B.get_bottom() or C.get_top() != B.get_top():
        core.error("Wrong intersection computation")
        
    B = spatial_extent(north=40, south=30, east=60, west=30, bottom=-50, top=50)
    B.print_info()
    C = A.intersect(B)
    C.print_info()
    
    if C.get_north() != B.get_north() or C.get_south() != B.get_south() or \
       C.get_west() != B.get_west() or C.get_east() != B.get_east() or \
       C.get_bottom() != B.get_bottom() or C.get_top() != B.get_top():
        core.error("Wrong intersection computation")
    
    B = spatial_extent(north=40, south=30, east=60, west=30, bottom=-30, top=50)
    B.print_info()
    C = A.intersect(B)
    C.print_info()
    
    if C.get_north() != B.get_north() or C.get_south() != B.get_south() or \
       C.get_west() != B.get_west() or C.get_east() != B.get_east() or \
       C.get_bottom() != B.get_bottom() or C.get_top() != B.get_top():
        core.error("Wrong intersection computation")
    
    B = spatial_extent(north=40, south=30, east=60, west=30, bottom=-30, top=30)
    B.print_info()
    C = A.intersect(B)
    C.print_info()
    
    if C.get_north() != B.get_north() or C.get_south() != B.get_south() or \
       C.get_west() != B.get_west() or C.get_east() != B.get_east() or \
       C.get_bottom() != B.get_bottom() or C.get_top() != B.get_top():
        core.error("Wrong intersection computation")

###############################################################################

def test_spatial_relations():
    # Generate the extents
    
    A = spatial_extent(north=80, south=20, east=60, west=10, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=80, south=20, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "equivalent":
	core.error("Wrong spatial relation: %s"%(relation))
 
    B = spatial_extent(north=70, south=20, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=70, south=30, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = B.spatial_relation_2d(A)
    print relation
    if relation!= "covered":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = B.spatial_relation(A)
    print relation
    if relation!= "covered":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=70, south=30, east=50, west=10, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = B.spatial_relation_2d(A)
    print relation
    if relation!= "covered":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=70, south=30, east=50, west=20, bottom=-50, top=50)
    
    relation = B.spatial_relation(A)
    print relation
    if relation!= "covered":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=70, south=30, east=50, west=20, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "contain":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=70, south=30, east=50, west=20, bottom=-40, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "cover":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=70, south=30, east=50, west=20, bottom=-40, top=40)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "contain":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = B.spatial_relation(A)
    print relation
    if relation!= "in":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=90, south=30, east=50, west=20, bottom=-40, top=40)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "overlap":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "overlap":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=90, south=5, east=70, west=5, bottom=-40, top=40)
    A.print_info()
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "in":
	core.error("Wrong spatial relation: %s"%(relation))
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "overlap":
	core.error("Wrong spatial relation: %s"%(relation))
	
    B = spatial_extent(north=90, south=5, east=70, west=5, bottom=-40, top=60)
    A.print_info()
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "overlap":
	core.error("Wrong spatial relation: %s"%(relation))
	
	
    B = spatial_extent(north=90, south=5, east=70, west=5, bottom=-60, top=60)
    A.print_info()
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "in":
	core.error("Wrong spatial relation: %s"%(relation))
	
    A = spatial_extent(north=80, south=60, east=60, west=10, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=60, south=20, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    A = spatial_extent(north=60, south=40, east=60, west=10, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=80, south=60, east=60, west=10, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=40, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=90, south=30, east=60, west=40, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=70, south=50, east=60, west=40, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=60, south=20, east=60, west=40, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=40, south=20, east=60, west=40, bottom=-50, top=50)
    B.print_info()
    
    relation = A.spatial_relation_2d(B)
    print relation
    if relation!= "disjoint":
	core.error("Wrong spatial relation: %s"%(relation))
	
    relation = A.spatial_relation(B)
    print relation
    if relation!= "disjoint":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=60, south=20, east=60, west=40, bottom=-60, top=60)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=40, west=20, bottom=-50, top=50)
    A.print_info()
    B = spatial_extent(north=90, south=30, east=60, west=40, bottom=-40, top=40)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=0, top=50)
    A.print_info()
    B = spatial_extent(north=80, south=40, east=60, west=20, bottom=-50, top=0)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=0, top=50)
    A.print_info()
    B = spatial_extent(north=80, south=50, east=60, west=30, bottom=-50, top=0)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=0, top=50)
    A.print_info()
    B = spatial_extent(north=70, south=50, east=50, west=30, bottom=-50, top=0)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=0, top=50)
    A.print_info()
    B = spatial_extent(north=90, south=30, east=70, west=10, bottom=-50, top=0)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=0, top=50)
    A.print_info()
    B = spatial_extent(north=70, south=30, east=50, west=10, bottom=-50, top=0)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 ###
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=-50, top=0)
    A.print_info()
    B = spatial_extent(north=80, south=40, east=60, west=20, bottom=0, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=-50, top=0)
    A.print_info()
    B = spatial_extent(north=80, south=50, east=60, west=30, bottom=0, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=-50, top=0)
    A.print_info()
    B = spatial_extent(north=70, south=50, east=50, west=30, bottom=0, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=-50, top=0)
    A.print_info()
    B = spatial_extent(north=90, south=30, east=70, west=10, bottom=0, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
 
    A = spatial_extent(north=80, south=40, east=60, west=20, bottom=-50, top=0)
    A.print_info()
    B = spatial_extent(north=70, south=30, east=50, west=10, bottom=0, top=50)
    B.print_info()
    
    relation = A.spatial_relation(B)
    print relation
    if relation!= "meet":
	core.error("Wrong spatial relation: %s"%(relation))
	
def test_temporal_topology_builder():
    map_list = []
    count = 0
    for year in xrange(0,1):
	for month in xrange(1,6):
	    start = datetime(2001 + year, month, 01)
	    end = datetime(2001 + year, month + 1, 01)
	    _map = raster_dataset("%d@A"%(count))
	    _map.set_absolute_time(start, end)
	    map_list.append(_map)
	    count += 1

    tb = temporal_topology_builder()
    tb.build(map_list, True)

    for _map in tb:
	_map.print_info()
 
    map_list = []
    for year in xrange(0,1):
	for month in xrange(1,6):
	    start = datetime(2001 + year, month, 01)
	    end = datetime(2001 + year, month + 1, 01)
	    _map = raster_dataset("%d@A"%(count))
	    _map.set_absolute_time(start, end)
	    map_list.append(_map)
	    count += 1
	    
	    start = datetime(2001 + year, month, 14)
	    end = datetime(2001 + year, month + 1, 14)
	    _map = raster_dataset("%d@A"%(count))
	    _map.set_absolute_time(start, end)
	    map_list.append(_map)
	    count += 1
	    
	    start = datetime(2001 + year, month, 8)
	    end = datetime(2001 + year, month + 1, 21)
	    _map = raster_dataset("%d@A"%(count))
	    _map.set_absolute_time(start, end)
	    map_list.append(_map)
	    count += 1

    tb = temporal_topology_builder()
    tb.build(map_list, False)
    for _map in tb:
	
	print _map.get_id()
	_map.absolute_time.print_info()
	_map.print_temporal_topology_info()
	
    # Test the performance of many overlapping maps
    count = 0
    for year in xrange(0,200):
	for month in xrange(1,12):
	    start = datetime(1901 + year, month, 01)
	    end = datetime(1904 + year, month + 1, 01)
	    _map = raster_dataset("%d@A"%(count))
	    _map.set_absolute_time(start, end)
	    map_list.append(_map)
	    count += 1
	    
    print "Build temporal topology with sorting for %i maps"%count
    tb = temporal_topology_builder()
    tb.build(map_list, True)
	
    print "Build temporal topology without sorting for %i maps"%count
    tb = temporal_topology_builder()
    tb.build(map_list, False)
    
if __name__ == "__main__":
    test_increment_datetime_by_string()
    test_adjust_datetime_to_granularity()
    test_spatial_extent_intersection()
    ##test_compute_relative_time_granularity()
    test_compute_absolute_time_granularity()
    test_compute_datetime_delta()
    test_spatial_extent_intersection()
    test_spatial_relations()
    test_temporal_topology_builder()