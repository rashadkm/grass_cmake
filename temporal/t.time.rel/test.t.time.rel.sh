# We test the relative valid time interval creation with t.time.rel

# We need to set a specific region in the
# @preprocess step of this test. We generate
# raster input with r.mapcalc
# The region setting should work for UTM and LL test locations
g.region s=0 n=80 w=0 e=120 b=0 t=50 res=10 res3=10 -p3

r.mapcalc --o expr="prec_1 = rand(0, 550)"
r.mapcalc --o expr="prec_2 = rand(0, 450)"
r.mapcalc --o expr="prec_3 = rand(0, 320)"
r.mapcalc --o expr="prec_4 = rand(0, 510)"
r.mapcalc --o expr="prec_5 = rand(0, 300)"
r.mapcalc --o expr="prec_6 = rand(0, 650)"

t.create --v --o type=strds temporaltype=relative output=precip_rel1 title="A test" descr="A test"
t.create --v --o type=strds temporaltype=relative output=precip_rel2 title="A test" descr="A test"
t.create --v --o type=strds temporaltype=relative output=precip_rel3 title="A test" descr="A test"

t.time.rel --v input=prec_1,prec_2,prec_3 start=5 increment=2
t.info type=rast input=prec_1
t.info type=rast input=prec_2
t.info type=rast input=prec_3

tr.register --v input=precip_rel1 maps=prec_1,prec_2,prec_3
tr.register --v input=precip_rel2 maps=prec_1,prec_2,prec_3
tr.register --v input=precip_rel3 maps=prec_1,prec_2,prec_3
# Check if the space time inputs are updated correctly
t.time.rel --v input=prec_1,prec_2,prec_3 start=0 increment=1000
t.info type=strds input=precip_rel1
t.topology type=strds input=precip_rel1
t.topology -m type=strds input=precip_rel1

t.time.rel --v -i input=prec_1,prec_2,prec_3 start=0 increment=1000 -i
t.info type=strds input=precip_rel1
t.topology type=strds input=precip_rel1
t.topology -m type=strds input=precip_rel1

t.time.rel --v input=prec_4,prec_5 start=5000 end=6000
t.info type=rast input=prec_4
t.info type=rast input=prec_5
t.time.rel --v input=prec_6 start=6000
t.info type=rast input=prec_6

t.remove --v type=rast input=prec_1,prec_2,prec_3,prec_4,prec_5,prec_6
t.remove --v type=strds input=precip_rel1,precip_rel2,precip_rel3
