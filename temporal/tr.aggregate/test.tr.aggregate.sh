# Test the extraction of a subset of a space time raster input

# We need to set a specific region in the
# @preprocess step of this test. We generate
# raster with r.mapcalc and create two space time raster inputs
# with relative and absolute time
# The region setting should work for UTM and LL test locations
g.region s=0 n=80 w=0 e=120 b=0 t=50 res=10 res3=10 -p3

r.mapcalc --o expr="prec_1 = rand(0, 550)"
r.mapcalc --o expr="prec_2 = rand(0, 450)"
r.mapcalc --o expr="prec_3 = rand(0, 320)"
r.mapcalc --o expr="prec_4 = rand(0, 510)"
r.mapcalc --o expr="prec_5 = rand(0, 300)"
r.mapcalc --o expr="prec_6 = rand(0, 650)"

t.create --o type=strds temporaltype=absolute output=precip_abs1 title="A test" descr="A test"
tr.register -i input=precip_abs1 maps=prec_1,prec_2,prec_3,prec_4,prec_5,prec_6 start="2001-01-15 12:05:45" increment="14 days"

# The first @test

tr.aggregate --o --v input=precip_abs1 output=precip_abs2 base=prec_sum granularity="2 days" method=average sampling=start,during
t.info type=strds input=precip_abs2
tr.aggregate --o --v input=precip_abs1 output=precip_abs2 base=prec_sum granularity="1 months" method=maximum sampling=start,during
t.info type=strds input=precip_abs2
tr.aggregate --o --v input=precip_abs1 output=precip_abs2 base=prec_sum granularity="2 months" method=minimum sampling=start,during
t.info type=strds input=precip_abs2
tr.aggregate --o --v input=precip_abs1 output=precip_abs2 base=prec_sum granularity="3 months" method=sum sampling=start,during
t.info type=strds input=precip_abs2

t.remove type=rast input=prec_1,prec_2,prec_3,prec_4,prec_5,prec_6
t.remove type=strds input=precip_abs1,precip_abs2
