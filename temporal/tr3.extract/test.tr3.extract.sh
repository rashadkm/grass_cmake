# Test the extraction of a subset of a space time raster input

# We need to set a specific region in the
# @preprocess step of this test. We generate
# raster with r.mapcalc and create two space time raster inputs
# with relative and absolute time
# The region setting should work for UTM and LL test locations
g.region s=0 n=80 w=0 e=120 b=0 t=50 res=10 res3=10 -p3

r3.mapcalc --o expr="prec_1 = rand(0, 550)"
r3.mapcalc --o expr="prec_2 = rand(0, 450)"
r3.mapcalc --o expr="prec_3 = rand(0, 320)"
r3.mapcalc --o expr="prec_4 = rand(0, 510)"
r3.mapcalc --o expr="prec_5 = rand(0, 300)"
r3.mapcalc --o expr="prec_6 = rand(0, 650)"

t.create --o type=str3ds temporaltype=absolute output=precip_abs1 title="A test" descr="A test"
t.register -i type=rast3d input=precip_abs1 maps=prec_1,prec_2,prec_3,prec_4,prec_5,prec_6 start="2001-01-01" increment="3 months"

# The first @test
# We create the space time raster inputs and register the raster maps with absolute time interval

tr3.extract --o input=precip_abs1 output=precip_abs2 where="start_time > '2001-06-01'" expression=" if(precip_abs1 > 400, precip_abs1, null())" base=new_prec

t.info type=str3ds input=precip_abs2

t.unregister type=rast3d maps=prec_1,prec_2,prec_3,prec_4,prec_5,prec_6
t.remove type=str3ds input=precip_abs1,precip_abs2
