set BATCH=%OSGEO4W_ROOT%\bin\@GRASS_EXECUTABLE@.bat

del "%OSGEO4W_STARTMENU%\GRASS GIS @VERSION@.lnk"
del "%ALLUSERSPROFILE%\Desktop\GRASS GIS @VERSION@.lnk"

del "%BATCH%"
del "%OSGEO4W_ROOT%"\apps\grass\grass-@VERSION@\etc\fontcap
del "%OSGEO4W_ROOT%"\apps\msys\bin\libintl3.dll
del "%OSGEO4W_ROOT%"\apps\msys\bin\libiconv2.dll
del "%OSGEO4W_ROOT%"\apps\msys\bin\regex2.dll
