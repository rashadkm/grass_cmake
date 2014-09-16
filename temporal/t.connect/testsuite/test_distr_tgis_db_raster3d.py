"""test distributed temporal databases with str3ds

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

import grass.pygrass.modules as pymod
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
import os

class testRaster3dExtraction(TestCase):

    @classmethod
    def setUpClass(cls):
       os.putenv("GRASS_OVERWRITE", "1")
       for i in range(1, 5): 
            cls.runModule("g.mapset", flags="c", mapset="test3d%i"%i)
            cls.runModule("g.region",  s=0,  n=80,  w=0,  e=120,  b=0,  t=50,  res=10,  res3=10)
            # Use always the current mapset as temporal database
            cls.runModule("r3.mapcalc", expression="a1 = 100")
            cls.runModule("r3.mapcalc", expression="a2 = 200")
            cls.runModule("r3.mapcalc", expression="a3 = 300")
            
            cls.runModule("t.create",  type="str3ds",  temporaltype="absolute",  
                                         output="A",  title="A test3d",  description="A test3d")
            cls.runModule("t.register",  flags="i",  type="rast3d",  input="A",  
                                         maps="a1,a2,a3",  
                                         start="2001-01-01", increment="%i months"%i)

    def test_tlist(self):      
        self.runModule("g.mapset", mapset="test3d1")
        
        list_string = """A|test3d1|2001-01-01 00:00:00|2001-04-01 00:00:00|3
                                A|test3d2|2001-01-01 00:00:00|2001-07-01 00:00:00|3
                                A|test3d3|2001-01-01 00:00:00|2001-10-01 00:00:00|3
                                A|test3d4|2001-01-01 00:00:00|2002-01-01 00:00:00|3"""
                                
        entries = list_string.split("\n")
        
        t_list = SimpleModule("t.list", quiet=True, columns=["name","mapset,start_time","end_time","number_of_maps"],  type="str3ds")
        self.assertModule(t_list)
        
        out = t_list.outputs["stdout"].value
        
        for a,  b in zip(list_string.split("\n"),  out.split("\n")):
            self.assertEqual(a.strip(), b.strip())
        
    def test_trast_list(self):      
        self.runModule("g.mapset", mapset="test3d1")

        list_string = """a1|test3d1|2001-01-01 00:00:00|2001-02-01 00:00:00
                                a2|test3d1|2001-02-01 00:00:00|2001-03-01 00:00:00
                                a3|test3d1|2001-03-01 00:00:00|2001-04-01 00:00:00"""

        entries = list_string.split("\n")

        trast_list = SimpleModule("t.rast3d.list", quiet=True, flags="s",  input="A@test3d1")
        self.assertModule(trast_list)

        out = trast_list.outputs["stdout"].value

        for a,  b in zip(list_string.split("\n"),  out.split("\n")):
            self.assertEqual(a.strip(), b.strip())

        list_string = """a1|test3d2|2001-01-01 00:00:00|2001-03-01 00:00:00
                                a2|test3d2|2001-03-01 00:00:00|2001-05-01 00:00:00
                                a3|test3d2|2001-05-01 00:00:00|2001-07-01 00:00:00"""

        entries = list_string.split("\n")

        trast_list = SimpleModule("t.rast3d.list", quiet=True, flags="s",  input="A@test3d2")
        self.assertModule(trast_list)

        out = trast_list.outputs["stdout"].value

        for a,  b in zip(list_string.split("\n"),  out.split("\n")):
            self.assertEqual(a.strip(), b.strip())

        list_string = """a1|test3d3|2001-01-01 00:00:00|2001-04-01 00:00:00
                                a2|test3d3|2001-04-01 00:00:00|2001-07-01 00:00:00
                                a3|test3d3|2001-07-01 00:00:00|2001-10-01 00:00:00"""

        entries = list_string.split("\n")

        trast_list = SimpleModule("t.rast3d.list", quiet=True, flags="s",  input="A@test3d3")
        self.assertModule(trast_list)

        out = trast_list.outputs["stdout"].value

        for a,  b in zip(list_string.split("\n"),  out.split("\n")):
            self.assertEqual(a.strip(), b.strip())

        list_string = """a1|test3d4|2001-01-01 00:00:00|2001-05-01 00:00:00
                                a2|test3d4|2001-05-01 00:00:00|2001-09-01 00:00:00
                                a3|test3d4|2001-09-01 00:00:00|2002-01-01 00:00:00"""

        entries = list_string.split("\n")

        trast_list = SimpleModule("t.rast3d.list", quiet=True, flags="s",  input="A@test3d4")
        self.assertModule(trast_list)

        out = trast_list.outputs["stdout"].value

        for a,  b in zip(list_string.split("\n"),  out.split("\n")):
            self.assertEqual(a.strip(), b.strip())

    def test_strds_info(self):  
        self.runModule("g.mapset", mapset="test3d4")
        tinfo_string="""id=A@test3d1
                                    name=A
                                    mapset=test3d1
                                    start_time=2001-01-01 00:00:00
                                    end_time=2001-04-01 00:00:00
                                    granularity=1 month"""

        info = SimpleModule("t.info", flags="g", type="str3ds",  input="A@test3d1")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")
  
        self.runModule("g.mapset", mapset="test3d3")
        tinfo_string="""id=A@test3d2
                                    name=A
                                    mapset=test3d2
                                    start_time=2001-01-01 00:00:00
                                    end_time=2001-07-01 00:00:00
                                    granularity=2 months"""

        info = SimpleModule("t.info", flags="g", type="str3ds", input="A@test3d2")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")
  
        self.runModule("g.mapset", mapset="test3d2")
        tinfo_string="""id=A@test3d3
                                    name=A
                                    mapset=test3d3
                                    start_time=2001-01-01 00:00:00
                                    end_time=2001-10-01 00:00:00
                                    granularity=3 months"""

        info = SimpleModule("t.info", flags="g", type="str3ds", input="A@test3d3")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")
  
        self.runModule("g.mapset", mapset="test3d1")
        tinfo_string="""id=A@test3d4
                                    name=A
                                    mapset=test3d4
                                    start_time=2001-01-01 00:00:00
                                    end_time=2002-01-01 00:00:00
                                    granularity=4 months"""

        info = SimpleModule("t.info", flags="g", type="str3ds", input="A@test3d4")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")

    def test_raster_info(self):  
        self.runModule("g.mapset", mapset="test3d3")
        tinfo_string="""id=a1@test3d1
                                name=a1
                                mapset=test3d1
                                temporal_type=absolute
                                start_time=2001-01-01 00:00:00
                                end_time=2001-02-01 00:00:00 """

        info = SimpleModule("t.info", flags="g", type="rast3d",  input="a1@test3d1")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")

        tinfo_string="""id=a1@test3d2
                                name=a1
                                mapset=test3d2
                                temporal_type=absolute
                                start_time=2001-01-01 00:00:00
                                end_time=2001-03-01 00:00:00 """

        info = SimpleModule("t.info", flags="g", type="rast3d",  input="a1@test3d2")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")

        tinfo_string="""id=a1@test3d3
                                name=a1
                                mapset=test3d3
                                temporal_type=absolute
                                start_time=2001-01-01 00:00:00
                                end_time=2001-04-01 00:00:00 """

        info = SimpleModule("t.info", flags="g", type="rast3d",  input="a1@test3d3")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")

        tinfo_string="""id=a1@test3d4
                                name=a1
                                mapset=test3d4
                                temporal_type=absolute
                                start_time=2001-01-01 00:00:00
                                end_time=2001-05-01 00:00:00 """

        info = SimpleModule("t.info", flags="g", type="rast3d",  input="a1@test3d4")
        self.assertModuleKeyValue(module=info, reference=tinfo_string, precision=2, sep="=")

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
