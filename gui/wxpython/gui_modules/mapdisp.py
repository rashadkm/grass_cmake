"""
To be used either from GIS Manager or as p.mon backend

Usage:
    python mapdisp.py monitor-identifier /path/to/command/file

mapdisp Package

Classes:
* Command
* BufferedWindow
* DrawWindow
* MapFrame
* MapApp
"""

DEBUG = False

# Authors: Michael Barton and Jachym Cepicky
# COPYRIGHT:	(C) 1999 - 2006 by the GRASS Development Team
# Double buffered drawing concepts from the wxPython Cookbook

import wx
import wx.aui
import os, sys, time, glob, math

import render
import toolbars
import grassenv
import track
import menuform

import images
imagepath = images.__path__[0]
sys.path.append(imagepath)

from threading import Thread

gmpath = os.getenv("GISBASE") + "/etc/wx/gui_modules/"
sys.path.append(gmpath)

icons = ""

if not os.getenv("GRASS_ICONPATH"):
    icons = os.getenv("GISBASE") + "/etc/gui/icons/"
else:
    icons = os.environ["GRASS_ICONPATH"]

Map = render.Map() # instance of Map class to render GRASS display output to PPM file

# for cmdlinef
cmdfilename = None

class Command(Thread):
    """
    Creates  thread, which will observe the command file and see, if there
    is new command to be executed
    """
    def __init__ (self,parent,Map):
      Thread.__init__(self)

      global cmdfilename

      self.parent = parent
      self.map = Map #
      self.cmdfile = open(cmdfilename,"r")

    def run(self):
        """
        Run this in thread
        """
        dispcmd = []
        while 1:
            self.parent.redraw = False
            line = self.cmdfile.readline().strip()
            if line == "quit":
                break

            if line:
                try:
                    dispcmd = {}
                    name = None
                    mapset = None
                    opacity = 1

                    cmd = list(line.strip().split())
                    action = cmd[0]
                    cmd = cmd[1:]

                    for kv in cmd:
                        if kv[0] == '-': # flag
                            dispcmd[kv[1:]] = True
                        else: # option
                            try:
                                key,value = kv.split('=')
                            except:
                                # fisrt option
                                key = "map"
                                value = kv

                            if key == "opacity":
                                try:
                                    # opacity in [%]
                                    opacity = int (value) / 100.
                                except:
                                    pass
                            elif key == "map":
                                try:
                                    name,mapset = value.split('@')
                                except:
                                    name = value
                                    mapset = None
                            else:
                                dispcmd[key] = value


                    if DEBUG:
                        print "Command.run(): ",
                        print "opacity=%d name=%s mapset=%s" % (opacity, name, mapset),
                        print dispcmd

                    if action == "d.rast":
                        self.map.AddRasterLayer(name=name,
                                                mapset=mapset,
                                                l_opacity=opacity,
                                                dispcmd=dispcmd)
                    elif action == "d.vect":
                        self.map.AddVectorLayer(name=name,
                                                mapset=mapset,
                                                l_opacity=opacity,
                                                dispcmd=dispcmd)

                    self.parent.redraw =True

                except Exception, e:
                    print "Command Thread: ",e
                    pass

            time.sleep(0.1)

        sys.exit()

class BufferedWindow(wx.Window):
    """
    A Buffered window class.

    To use it, subclass it and define a Draw(DC) method that takes a DC
    to draw to. In that method, put the code needed to draw the picture
    you want. The window will automatically be double buffered, and the
    screen will be automatically updated when a Paint event is received.

    When the drawing needs to change, you app needs to call the
    UpdateMap() method. Since the drawing is stored in a bitmap, you
    can also save the drawing to file by calling the
    SaveToFile(self,file_name,file_type) method.
    """

    def __init__(self, parent, id,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE):

    	wx.Window.__init__(self, parent, id, pos, size, style)
        self.parent = parent
        self.Map = Map

        #
        # Flags
        #
    	self.render = True  # re-render the map from GRASS or just redraw image
    	self.resize = False # indicates whether or not a resize event has taken place
    	self.dragimg = None # initialize variable for map panning
    	self.pen = None     # pen for drawing zoom boxes, etc.

        #
        # Event bindings
        #
    	self.Bind(wx.EVT_PAINT,        self.OnPaint)
    	self.Bind(wx.EVT_SIZE,         self.OnSize)
    	self.Bind(wx.EVT_IDLE,         self.OnIdle)
    	self.Bind(wx.EVT_MOTION,       self.MouseActions)
    	self.Bind(wx.EVT_MOUSE_EVENTS, self.MouseActions)

        #
        # Render output objects
    	#
    	self.mapfile = None # image file to be rendered
    	self.img = ""       # wx.Image object (self.mapfile)
        self.ovldict = {}     # list of images for overlays
        self.ovlcoords = {} # positioning coordinates for decoration overlay
        self.imagedict = {} # images and their PseudoDC ID's for painting and dragging
        self.crop = {} # coordinates to crop overlays to their data, indexed by image ID
        self.select = {} # selecting/unselecting decorations for dragging
        self.ovlchk = {} # showing/hiding decorations
        self.textdict = {} # text, font, and color indexed by id
        self.currtxtid = None # PseudoDC id for currently selected text

        #
    	# mouse attributes like currently pressed buttons, position on
    	# the screen, begin and end of dragging, and type of drawing
        #
    	self.mouse = {
    	    'l': False,
    	    'r': False,
    	    'm': False,
    	    'pos': [None, None],
    	    'begin': [0, 0],
    	    'end': [0, 0],
    	    'box': "point"
    	    }

        self.zoomtype = 1  # 1 zoom in, 0 no zoom, -1 zoom out

    	# OnSize called to make sure the buffer is initialized.
    	# This might result in OnSize getting called twice on some
    	# platforms at initialization, but little harm done.
        #!!! self.OnSize(None)

        # create a PseudoDC for map decorations like scales and legends
        self.pdc = wx.PseudoDC()

        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)

        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0,0)

    def Draw(self, pdc, img=None, drawid=None, pdctype='image', coords=[0,0,0,0]):
        """
        Draws map decorations on top of map
        """

        if drawid == None:
            if pdctype == 'image' :
                drawid = imagedict[img]
            elif pdctype == 'clear':
                drawid == None
            else:
                drawid = wx.NewId()
        else:
            self.ovlcoords[drawid] = coords
            self.ovlchk[drawid] = True
            pdc.SetId(drawid)
            self.select[drawid] = False

        pdc.BeginDrawing()
        if drawid != 99:
            bg = wx.TRANSPARENT_BRUSH
        else:
            bg = wx.Brush(self.GetBackgroundColour())
        pdc.SetBackground(bg)
        pdc.Clear()
        self.Refresh()

        if pdctype == 'clear': # erase the display
            pdc.EndDrawing()
            return

        if pdctype == 'image':
            mask = None
            bitmap = wx.BitmapFromImage(img)
#            if drawid in self.ovldict:
#                w,h = self.ovldict[drawid][1]
#            else:
            w,h = bitmap.GetSize()
            pdc.DrawBitmap(bitmap, coords[0], coords[1], True) # draw the composite map
            pdc.SetIdBounds(drawid, (coords[0],coords[1],w,h))

        elif pdctype == 'box': # draw a box on top of the map
            pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
            pdc.SetPen(self.pen)
            pdc.DrawRectangle(coords[0], coords[1], coords[2], coords[3])
            pdc.SetIdBounds(drawid,(coords[0], coords[1], coords[2], coords[3]))
            self.ovlcoords[drawid] = coords

        elif pdctype == 'line': # draw a line on top of the map
            pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
            pdc.SetPen(self.pen)
            dc.DrawLine(coords[0], coords[1], coords[2], coords[3])
            pdc.SetIdBounds(drawid,(coords[0], coords[1], coords[2], coords[3]))
            self.ovlcoords[drawid] = coords

        elif pdctype == 'point': #draw point
            pen = self.RandomPen()
            pdc.SetPen(pen)
            pdc.DrawPoint(coords[0], coords[1])
            coords[0] = coords[0] - 5
            coords[1] = coords[1] - 5
            coords[2] = coords[0] + 5
            coords[3] = coords[1] + 5
            pdc.SetIdBounds(drawid,(coords[0], coords[1], coords[2], coords[3]))
            self.ovlcoords[drawid] = coords

        elif pdctype == 'text': # draw text on top of map
            text = img[0]
            rotation = float(img[3])
            w,h = self.GetFullTextExtent(img[0])[0:2]
            pdc.SetFont(img[1])
            pdc.SetTextForeground(img[2])
            coords,w,h = self.textBounds(img,coords)
            if rotation == 0:
                pdc.DrawText(img[0], coords[0], coords[1])
            else:
                pdc.DrawRotatedText(img[0], coords[0], coords[1], rotation)
            pdc.SetIdBounds(drawid, (coords[0], coords[1], w, h))
            self.ovlcoords[drawid] = coords

        pdc.EndDrawing()
        self.Refresh()

    def textBounds(self, textinfo, coords):
        rotation = float(textinfo[3])
        self.Update()
        self.Refresh()
        self.SetFont(textinfo[1])
        w,h = self.GetTextExtent(textinfo[0])
        if rotation == 0:
            coords[2], coords[3] = coords[0] + w, coords[1] + h
            return coords,w,h
        else:
            boxh = math.fabs(math.sin(math.radians(rotation)) * w) + h
            boxw = math.fabs(math.cos(math.radians(rotation)) * w) + h
            coords[2] = coords[0] + boxw
            coords[3] = coords[1] + boxh
            return coords,boxw,boxh

    def OnPaint(self, event):
    	"""
        All that is needed here is to draw the buffer to screen
        """
    	dc = wx.BufferedPaintDC(self, self._Buffer)

        # use PrepateDC to set position correctly
        self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        # create a clipping rect from our position and size
        # and the Update Region
        rgn = self.GetUpdateRegion()
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc,r)


    def OnSize(self, event):
    	"""
        The Buffer init is done here, to make sure the buffer is always
    	the same size as the Window
        """

        # set size of the input image
    	self.Map.width, self.Map.height = self.GetClientSize()

    	# Make new off screen bitmap: this bitmap will always have the
    	# current drawing in it, so it can be used to save the image to
    	# a file, or whatever.
    	self._Buffer = wx.EmptyBitmap(self.Map.width, self.Map.height)

        # get the image to be rendered
    	self.img = self.GetImage()


        # update map display
    	if self.img and self.Map.width + self.Map.height > 0: # scale image during resize
    	    self.img = self.img.Scale(self.Map.width, self.Map.height)
    	    self.render = False
    	    self.UpdateMap()

        # re-render image on idle
    	self.resize = True

    def OnIdle(self, event):
    	"""
        Only re-render a compsite map image from GRASS during
    	idle time instead of multiple times during resizing.
        """

    	if self.resize:
    	    self.render = True
    	    self.UpdateMap()
    	event.Skip()

    def SaveToFile(self, FileName, FileType):
    	"""
        This will save the contents of the buffer
    	to the specified file. See the wx.Windows docs for
    	wx.Bitmap::SaveFile for the details
        """
    	self._Buffer.SaveFile(FileName, FileType)

    def GetOverlay(self):
        """
        Converts overlay files to wx.Image
        """
        self.ovldict = {}
        if self.Map.ovlist:
             for ovlfile in self.Map.ovlist:
                 if os.path.isfile(ovlfile) and os.path.getsize(ovlfile):
                     img = wx.Image(ovlfile, wx.BITMAP_TYPE_ANY)

                     left = right = top = bottom = 0
                     breakout = False
#                     # auto-crop scales and legends
#                     for w in range(img.GetWidth()): # set left edge
#                         for h in range(img.GetHeight()-1):
#                             if img.IsTransparent(w,h) == False:
#                                 left = w
#                                 breakout = True
#                                 break
#                         if breakout:
#                             breakout = False
#                             break
#                     for w in range(img.GetWidth()-1, 0, -1): # set right edge
#                         for h in range(img.GetHeight()-1):
#                             if img.IsTransparent(w,h) == False:
#                                 right = w
#                                 breakout = True
#                                 break
#                         if breakout:
#                             breakout = False
#                             break
#                     for h in range(img.GetHeight()): # set top edge
#                         for w in range(left,right):
#                             if img.IsTransparent(w,h) == False:
#                                 top = h
#                                 breakout = True
#                                 break
#                         if breakout:
#                             breakout = False
#                             break
#                     for h in range(img.GetHeight()-1, 0, - 1): # set top edge
#                         for w in range(left,right):
#                             if img.IsTransparent(w,h) == False:
#                                 bottom = h
#                                 breakout = True
#                                 break
#                         if breakout:
#                             breakout = False
#                             break
#                     cropwidth = right - left
#                     cropheight = bottom - top
                     pdc_id = self.Map.ovlist.index(ovlfile)
#                     self.ovldict[pdc_id] = img,(cropwidth,cropheight)  # image and cropping information for each overlay image
                     self.ovldict[pdc_id] = img  # image information for each overlay image
                     self.imagedict[img] = pdc_id # set image PeudoDC ID

        return self.ovldict


    def GetImage(self):
        """
        Converts files to wx.Image
        """
        if self.Map.mapfile and os.path.isfile(self.Map.mapfile) and \
                os.path.getsize(self.Map.mapfile):
            img = wx.Image(self.Map.mapfile, wx.BITMAP_TYPE_ANY)
        else:
            img = None

        self.imagedict[img] = 99 # set image PeudoDC ID
        return img


    def UpdateMap(self, img=None):
        """
    	This would get called if the drawing needed to change, for whatever reason.

    	The idea here is that the drawing is based on some data generated
    	elsewhere in the system. IF that data changes, the drawing needs to
    	be updated.

    	"""

        if DEBUG:
            print "Buffered Window.UpdateMap(%s): render=%s" % (img, self.render)

        if self.render:
            # render new map images
            self.Map.width, self.Map.height = self.GetClientSize()
            self.mapfile = self.Map.Render(force=self.render)
            self.img = self.GetImage()
            self.resize = False

        if not self.img: return
        try:
            id = self.imagedict[self.img]
        except:
            return

        # paint images to PseudoDC
        self.pdc.Clear()
        self.pdc.RemoveAll()
        self.Draw(self.pdc, self.img, drawid=id) # draw map image background
        self.ovldict = self.GetOverlay() # list of decoration overlay images
        if self.ovldict != {}: # draw scale and legend overlays
            for id in self.ovldict:
                img = self.ovldict[id]
                if id not in self.ovlcoords: self.ovlcoords[id] = wx.Rect(0,0,0,0)
                if id not in self.ovlchk: self.ovlchk[id] = False
                if self.ovlchk[id] == True: # draw any active and defined overlays
                    self.Draw(self.pdc, img=img, drawid=id,
                             pdctype='image', coords=self.ovlcoords[id])

        if self.textdict != None: # draw text overlays
            for id in self.textdict:
                self.Draw(self.pdc, img=self.textdict[id], drawid=id,
                          pdctype='text', coords=self.ovlcoords[id])

    	self.resize = False

        # update statusbar
        self.parent.statusbar.SetStatusText("Extent: %d,%d : %d,%d" %
                                            (self.Map.region["w"], self.Map.region["e"],
                                             self.Map.region["n"], self.Map.region["s"]), 0)

    def EraseMap(self):
        """
        Erase the map display
        """
#    	dc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
#    	self.Draw(dc, dctype='clear')
        self.Draw(self.pdc, pdctype='clear')

    def DragMap(self, moveto):
    	"""
        Drag a bitmap image for panning.
        """

    	dc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
    	dc.SetBackground(wx.Brush("White"))
    	bitmap = wx.BitmapFromImage(self.img)
    	self.dragimg = wx.DragImage(bitmap)
    	self.dragimg.BeginDrag((0, 0), self)
    	self.dragimg.GetImageRect(moveto)
    	self.dragimg.Move(moveto)
    	dc.Clear()
    	self.dragimg.DoDrawImage(dc, moveto)
    	self.dragimg.EndDrag()

    def DragItem(self, id, event):
        x,y = self.lastpos
        dx = event.GetX() - x
        dy = event.GetY() - y
        self.pdc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        r = self.pdc.GetIdBounds(id)
        if self.dragid > 100: # text dragging
            rtop = (r[0],r[1]-r[3],r[2],r[3])
            r = r.Union(rtop)
            rleft = (r[0]-r[2],r[1],r[2],r[3])
            r = r.Union(rleft)
        self.pdc.TranslateId(id, dx, dy)
        r2 = self.pdc.GetIdBounds(id)
        r = r.Union(r2)
        r.Inflate(4,4)
        self.Update()
        self.RefreshRect(r, False)
        self.lastpos = (event.GetX(),event.GetY())

    def MouseDraw(self):
    	"""
        Mouse zoom rectangles and lines
        """
        boxid = wx.ID_NEW
    	if self.mouse['box'] == "box":
    	    mousecoords = [self.mouse['begin'][0], self.mouse['begin'][1], \
    		self.mouse['end'][0] - self.mouse['begin'][0], \
    		self.mouse['end'][1] - self.mouse['begin'][1]]
            r = self.pdc.GetIdBounds(boxid)
            r.Inflate(4,4)
            self.pdc.ClearId(boxid)
            self.RefreshRect(r, False)
            self.pdc.SetId(boxid)
            self.Draw(self.pdc, drawid=boxid, pdctype='box', coords=mousecoords)
    	elif self.mouse['box'] == "line":
    	    mousecoords = [self.mouse['begin'][0], self.mouse['begin'][1], \
    		self.mouse['end'][0] - self.mouse['begin'][0], \
    		self.mouse['end'][1] - self.mouse['begin'][1]]
            r = self.pdc.GetIdBounds(boxid)
            r.Inflate(4,4)
            self.pdc.ClearId(boxid)
            self.RefreshRect(r, False)
            self.pdc.SetId(boxid)
            self.Draw(self.pdc, drawid=boxid, pdctype='line', coords=mousecoords)

    def MouseActions(self, event):
    	"""
    	Mouse motion and button click notifier
    	"""
        wheel = event.GetWheelRotation() # +- int
        hitradius = 10 # distance for selecting map decorations

        # left mouse button pressed; get decoration ID
        if event.LeftDown():
            self.lastpos = self.mouse['begin'] = event.GetPositionTuple()[:]
#            idlist = self.pdc.FindObjectsByBBox(self.lastpos[0],self.lastpos[1])
            idlist  = self.pdc.FindObjects(self.lastpos[0],self.lastpos[1], hitradius)
            if idlist != []:
                self.dragid = idlist[0]

        # double click to select overlay decoration options dialog
        elif event.ButtonDClick():
            # start point of drag
            clickposition = event.GetPositionTuple()[:]

            # get decoration ID
#            idlist = self.pdc.FindObjectsByBBox(clickposition[0], clickposition[1])
            idlist  = self.pdc.FindObjects(clickposition[0], clickposition[1], hitradius)
            if idlist == []: return
            self.dragid = idlist[0]

            self.ovlcoords[self.dragid] = self.pdc.GetIdBounds(self.dragid)
            if self.dragid > 100:
                self.currtxtid = self.dragid
                self.Parent.addText(None)
            elif self.dragid == 0:
                self.Parent.addBarscale(None)
            elif self.dragid == 1:
                self.Parent.addLegend(None)

    	# left mouse button released and not just a pointer
        elif event.LeftUp():

            if self.mouse['box'] != "point" and self.mouse['box'] != "query":
                # end point of zoom box or drag
                self.mouse['end'] = event.GetPositionTuple()[:]

                # set region in zoom or pan
                self.Zoom(self.mouse['begin'], self.mouse['end'], self.zoomtype)
                # redraw map
                self.render=True
                self.UpdateMap()

            # digitizing
            elif self.parent.digittoolbar:
                if self.parent.digittoolbar.digitize == "point":
                    east,north= self.Pixel2Cell(self.mouse['begin'][0],self.mouse['begin'][1])
                    self.parent.digittoolbar.AddPoint(east,north)
                # redraw map
                self.render=True
                self.UpdateMap()

            # querying
            elif self.mouse["box"] == "query":
                east,north = self.Pixel2Cell(self.mouse['begin'][0],self.mouse['begin'][1])
                if self.parent.gismanager:
                    layer =  self.parent.gismanager.maptree.GetSelection()
                    type =   self.parent.gismanager.maptree.layertype[layer]
                    dcmd = self.parent.gismanager.maptree.GetPyData(layer)[0]
                    mapname = None
                    for item in dcmd.split(' '):
                        if 'map=' in item:
                            mapname = item.split('=')[1]

                    self.parent.QueryMap(mapname,type,east,north)
                else:
                    print "Quering without gis manager not implemented yet"

            # end drag of overlay decoration
            elif self.dragid != None:
                self.ovlcoords[self.dragid] = self.pdc.GetIdBounds(self.dragid)
                self.dragid = None
                self.currtxtid = None
                id = None
                self.Update()

        elif event.Dragging():
            currpos = event.GetPositionTuple()[:]
            end = (currpos[0]-self.mouse['begin'][0], \
                             currpos[1]-self.mouse['begin'][1])

            # dragging or drawing box with left button
            if self.mouse['box'] == 'pan':
                self.DragMap(end)
                self.DragItem(99, event)

            # dragging decoration overlay item
            elif self.mouse['box'] == 'point' and self.dragid != None and self.dragid != 99:
                self.DragItem(self.dragid, event)

            # dragging something else?
            else:
                self.mouse['end'] = event.GetPositionTuple()[:]
                self.MouseDraw()

    	# zoom with mouse wheel
    	elif wheel != 0:

    	    # zoom 1/2 of the screen
    	    begin = [self.Map.width/4, self.Map.height/4]
    	    end = [self.Map.width - self.Map.width/4,
    		self.Map.height - self.Map.height/4]

        elif event.RightDown():
            x,y = event.GetPositionTuple()[:]
            #l = self.pdc.FindObjectsByBBox(x, y)
            l = self.pdc.FindObjects(x, y, hitradius)
            if not l: return
            id = l[0]
            if self.pdc.GetIdGreyedOut(id) == True:
                self.pdc.SetIdGreyedOut(id, False)
            else:
                self.pdc.SetIdGreyedOut(id, True)
            r = self.pdc.GetIdBounds(id)
            r.Inflate(4,4)
            self.RefreshRect(r, False)

    	# store current mouse position
    	self.mouse['pos'] = event.GetPositionTuple()[:]

    def Pixel2Cell(self, x, y):
    	"""
    	Calculates real word coordinates to image coordinates

    	Input : x, y
    	Output: int x, int y
    	"""
    	newx = self.Map.region['w'] + x * self.Map.region["ewres"]
    	newy = self.Map.region['n'] - y * self.Map.region["nsres"]
    	return newx, newy

    def Zoom(self, begin, end, zoomtype):
        """
        Calculates new region while (un)zoom/pan-ing
        """
    	x1, y1, x2, y2 = begin[0], begin[1], end[0], end[1]
    	newreg = {}

    	# threshold - too small squares do not make sense
    	# can only zoom to windows of > 10x10 screen pixels
    	if x2 > 10 and y2 > 10 and zoomtype != 0:

    	    if x1 > x2:
    		x1, x2 = x2, x1
    	    if y1 > y2:
    		y1, y2 = y2, y1
    	    # zoom in
    	    if zoomtype > 0:
    		newreg['w'], newreg['n'] = self.Pixel2Cell(x1, y1)
    		newreg['e'], newreg['s'] = self.Pixel2Cell(x2, y2)

    	    # zoom out
    	    elif zoomtype < 0:
    		newreg['w'], newreg['n'] = self.Pixel2Cell(
    		    -x1*2,
    		    -y1*2)
                newreg['e'], newreg['s'] = self.Pixel2Cell(
    		    self.Map.width+2*(self.Map.width-x2),
    		    self.Map.height+2*(self.Map.height-y2))
    	# pan
    	elif zoomtype == 0:
    	    newreg['w'], newreg['n'] = self.Pixel2Cell(
    		x1-x2,
    		y1-y2)
    	    newreg['e'], newreg['s'] = self.Pixel2Cell(
    		self.Map.width+x1-x2,
    		self.Map.height+y1-y2)

    	# if new region has been calculated, set the values
    	if newreg :
    	    self.Map.region['n'] = newreg['n']
    	    self.Map.region['s'] = newreg['s']
    	    self.Map.region['e'] = newreg['e']
    	    self.Map.region['w'] = newreg['w']

class MapFrame(wx.Frame):
    """
    Main frame for map display window. Drawing takes place in child double buffered
    drawing window.
    """

    def __init__(self, parent=None, id = wx.ID_ANY, title="Map display",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, toolbars=["map"], cb=None, idx=-1):


        """
            Main map display window with toolbars, statusbar and
            DrawWindow

            Parameters:
                parent  -- parent window, None, wx.Window()
                id      -- window ID, int, wx.NewId()
                title   -- window title, string
                pos     -- where to place it, tupple, wx.Position
                size    -- window size, tupple, wx.Size
                style   -- window style
                toolbars-- array of default toolbars, which should appear
                           map, digit
                cb      -- control book ID in GIS Manager
                idx     -- index of display
        """

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # most of the thime, this will be the gis manager
        self.gismanager = parent
        self.Map = Map

        #
        # Set the size
        #
        self.SetClientSize((600, 475))

        # Set variables to associate display with GIS Manager page
        self.ctrlbk = cb
        self.disp_idx = idx

        #
        # Fancy gui
        #
        self._mgr = wx.aui.AuiManager(self)
        self.SetIcon(wx.Icon(os.path.join(imagepath,'grass.map.gif'), wx.BITMAP_TYPE_ANY))

        #
        # Add toolbars
        #
        self.maptoolbar = None
        self.digittoolbar = None
        for toolb in toolbars:
            self.AddToolbar(toolb)

        #
        # Add statusbar
        #
    	self.statusbar = self.CreateStatusBar(number=2, style=0)
    	self.statusbar.SetStatusWidths([-2, -1])
    	map_frame_statusbar_fields = ["Extent: %d,%d : %d,%d" %
                                      (self.Map.region["w"], self.Map.region["e"],
                                       self.Map.region["n"], self.Map.region["s"]),
                                      "%s,%s" %(None, None)]
    	for i in range(len(map_frame_statusbar_fields)):
    	    self.statusbar.SetStatusText(map_frame_statusbar_fields[i], i)


        # d.barscale overlay added to rendering overlay list
        self.Map.addOverlay(type=0, command='d.barscale', l_active=True, l_render=False)
        # d.barscale overlay added to rendering overlay list as placeholder for d.legend
        self.Map.addOverlay(type=1, command='d.barscale', l_active=True, l_render=False)

        #
    	# Init map display
        #
    	self.InitDisplay() # initialize region values
#    	self.MapWindow = DrawWindow(self) # initialize buffered DC
        self.MapWindow = BufferedWindow(self, id = wx.ID_ANY) # initialize buffered DC
    	self.MapWindow.Bind(wx.EVT_MOTION, self.OnMotion)

        # decoration overlays
        self.ovlchk = self.MapWindow.ovlchk
        self.ovlcoords = self.MapWindow.ovlcoords
        self.params = {} # previously set decoration options parameters to insert into options dialog

        #
        # Bind various events
        # ONLY if we are running from GIS manager
        #
        if self.disp_idx > -1:
            self.Bind(wx.EVT_ACTIVATE, self.OnFocus)
            self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)

        #
        # Update fancy gui style
        #
        self._mgr.AddPane(self.MapWindow, wx.CENTER)
        self._mgr.Update()

        #
        # Create dictionary of available cursors
        #
        self.cursors = {
            "default" : wx.StockCursor (wx.CURSOR_DEFAULT),
            "cross"   : wx.StockCursor (wx.CURSOR_CROSS),
            "hand"    : wx.StockCursor (wx.CURSOR_HAND)
            }

    def AddToolbar(self, name):
        """
        Add defined toolbar to the window

        Currently known toolbars are:
            * map
            * digit
        """
        if name == "map":
            self.maptoolbar = toolbars.MapToolbar(self, self.Map)
            self._mgr.AddPane(self.maptoolbar.toolbar, wx.aui.AuiPaneInfo().
                          Name("maptoolbar").Caption("Map Toolbar").
                          ToolbarPane().Top().LeftDockable(False).RightDockable(False).
                          BottomDockable(True).CloseButton(False))

        if name == "digit":
            self.digittoolbar = toolbars.DigitToolbar(self,self.Map)
            self._mgr.AddPane(self.digittoolbar.toolbar, wx.aui.AuiPaneInfo().
                          Name("digittoolbar").Caption("Digit Toolbar").
                          ToolbarPane().Top().LeftDockable(False).RightDockable(False).
                          BottomDockable(True).CloseButton(False))
        self._mgr.Update()

    def InitDisplay(self):
        """
        Initialize map display, set dimensions and map region
        """
        self.width, self.height = self.GetClientSize()
        self.Map.geom = self.width, self.height
        self.Map.GetRegion()
        #FIXME
        #This was Map.getResolution().
        #I'm guessing at the moment that this is replaced by Map.SetRegion()
        self.Map.SetRegion()

    def OnFocus(self, event):
        """
        Store information about active display
        in tracking variables and change choicebook
        page to match display
        """
        #get index number of active display
        self.disp_idx = int(track.Track().GetDisp_idx(self))

        #set active display tuple in track
        track.Track().SetDisp(self.disp_idx, self)

        # change bookcontrol page to page associted with display if > 1 display
        pg = track.Track().GetCtrls(self.disp_idx, 1)
        pg_count = self.ctrlbk.GetPageCount()
        pgnum = '0'
        if pg_count > 0:
            for x in range(0,pg_count):
                if self.ctrlbk.GetPage(x) == pg:
                    pgnum = x
                    break

        self.ctrlbk.SetSelection(pgnum)
        event.Skip()

    def OnMotion(self, event):
        """
        Mouse moved
        Track mouse motion and update status bar
        """
        # store current mouse position
    	posx, posy = event.GetPositionTuple()


    	# upsdate coordinates
    	x, y = self.MapWindow.Pixel2Cell(posx, posy)
    	self.statusbar.SetStatusText("%d,%d" % (x, y), 1)

    	event.Skip()

    def ReDraw(self, event):
        """
        Redraw button clicked
        """
        self.MapWindow.UpdateMap()

    def Pointer(self, event):
        """Pointer button clicled"""
        self.MapWindow.mouse['box'] = "point"

        # change the cursor
        self.MapWindow.SetCursor (self.cursors["default"])

    def OnZoomIn(self, event):
        """
        Zoom in the map.
        Set mouse pointer and zoom direction
        """
    	self.MapWindow.mouse['box'] = "box"
    	self.MapWindow.zoomtype = 1
        self.MapWindow.pen = wx.Pen(colour='Red', width=2, style=wx.SHORT_DASH)

       # change the cursor
        self.MapWindow.SetCursor (self.cursors["cross"])

    def OnZoomOut(self, event):
        """
        Zoom out the map.
        Set mouse pointer and zoom direction
        """
    	self.MapWindow.mouse['box'] = "box"
    	self.MapWindow.zoomtype = -1
        self.MapWindow.pen = wx.Pen(colour='Red', width=2, style=wx.SHORT_DASH)

        # change the cursor
        self.MapWindow.SetCursor (self.cursors["cross"])

    def OnZoomBack(self, event):
        """
        Zoom last (previously stored position)
        """
        # FIXME
        pass

    def OnPan(self, event):
        """
        Panning, set mouse to drag
        """
    	self.MapWindow.mouse['box'] = "pan"
    	self.MapWindow.zoomtype = 0
    	event.Skip()

        # change the cursor
        self.MapWindow.SetCursor (self.cursors["hand"])

    def OnErase(self, event):
        """
        Erase the canvas
        """
        self.MapWindow.EraseMap()

    def OnZoomRegion(self, event):
        """
        Zoom to region
        """
    	self.Map.getRegion()
    	self.Map.getResolution()
    	self.UpdateMap()
    	event.Skip()

    def OnAlignRegion(self, event):
        """
        Align region
        """
        if not self.Map.alignRegion:
            self.Map.alignRegion = True
        else:
            self.Map.alignRegion = False
        event.Skip()

    def SaveToFile(self, event):
        """
        Save to file
        """
        dlg = wx.FileDialog(self, "Choose a file name to save the image as a PNG to",
            defaultDir = "",
            defaultFile = "",
            wildcard = "*.png",
            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.MapWindow.SaveToFile(dlg.GetPath(), wx.BITMAP_TYPE_PNG)
        dlg.Destroy()

    def OnCloseWindow(self, event):
        """
        Window closed
        """
        self.Map.Clean()
        self.Destroy()

        #close associated controls book page
        #get index number of active display
        self.disp_idx = track.Track().GetDisp_idx(self)

        # delete associated bookcontrol page if it exists
        if self.disp_idx != None:
            pg = track.Track().GetCtrls(self.disp_idx, 1)
            pg_count = self.ctrlbk.GetPageCount()
            pgnum = '0'
            if pg_count > 0:
                for x in range(0,pg_count):
                    if self.ctrlbk.GetPage(x) == pg:
                        pgnum = x
            track.Track().popCtrl(self.disp_idx)
            self.ctrlbk.DeletePage(pgnum)

    def getRender(self):
        """
        returns the current instance of render.Map()
        """
        return self.Map

    def OnQuery(self, event):
        """
        Query currrent or last map
        """
    	self.MapWindow.mouse['box'] = "query"
    	self.MapWindow.zoomtype = 0
    	#event.Skip()

        # change the cursor
        self.MapWindow.SetCursor (self.cursors["cross"])

    def QueryMap(self,mapname,type,x,y):
        """
        Run *.what command in gis manager output window
        """
        #set query snap distance for v.what at mapunit equivalent of 10 pixels
        qdist = 10.0 * ((self.Map.region['e'] - self.Map.region['w'])/self.Map.width)

        if type == "raster":
            cmd = "r.what -f input=%s east_north=%f,%f" %\
                    (mapname, float(x), float(y))

        elif type == "vector":
            cmd = "v.what -a map=%s east_north=%f,%f distance=%f" %\
                    (mapname, float(x), float(y), qdist)

        if self.gismanager:
            self.gismanager.goutput.runCmd(cmd)
        else:
            os.system(cmd)

    # toolBar button handlers
    def onDecoration(self, event):
        """
        Decorations overlay menu"
        """
        point = wx.GetMousePosition()
        decmenu = wx.Menu()
        # Add items to the menu
        addscale = wx.MenuItem(decmenu, -1,'Scalebar and north arrow')
        bmp = wx.Image(os.path.join(icons,'module-d.barscale.gif'), wx.BITMAP_TYPE_GIF)
        bmp.Rescale(16, 16)
        bmp = bmp.ConvertToBitmap()
        addscale.SetBitmap(bmp)
        decmenu.AppendItem(addscale)
        self.Bind(wx.EVT_MENU, self.addBarscale, addscale)

        addlegend = wx.MenuItem(decmenu, -1,'Legend')
        bmp = wx.Image(os.path.join(icons,'module-d.legend.gif'), wx.BITMAP_TYPE_GIF)
        bmp.Rescale(16, 16)
        bmp = bmp.ConvertToBitmap()
        addlegend.SetBitmap(bmp)
        decmenu.AppendItem(addlegend)
        self.Bind(wx.EVT_MENU, self.addLegend, addlegend)

        addtext = wx.MenuItem(decmenu, -1,'Text')
        bmp = wx.Image(os.path.join(icons,'gui-font.gif'), wx.BITMAP_TYPE_GIF)
        bmp.Rescale(16, 16)
        bmp = bmp.ConvertToBitmap()
        addtext.SetBitmap(bmp)
        decmenu.AppendItem(addtext)
        self.Bind(wx.EVT_MENU, self.addText, addtext)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(decmenu)
        decmenu.Destroy()

    def addBarscale(self, event):
        """
        Handler for scale/arrow map decoration menu selection.
        """
        ovltype = id = 0 # index for overlay layer in render
        if ovltype in self.params:
            params = self.params[ovltype]
        else:
            params = ''

        ovldict = self.MapWindow.GetOverlay()
        if id not in ovldict: return
        img = ovldict[id]

        if id not in self.ovlcoords: self.ovlcoords[id] = [10,10]

        # Decoration overlay control dialog
        dlg = DecDialog(self, wx.ID_ANY, 'Scale and North arrow', size=(350, 200),
                         style=wx.DEFAULT_DIALOG_STYLE,
                         ovltype=ovltype,
                         cmd='d.barscale',
                         drawid=id,
                         checktxt = "Show/hide scale and arrow",
                         ctrltxt = "scale object",
                         params = params)

        dlg.CenterOnScreen()

        # If OK button pressed in decoration control dialog
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            if self.ovlchk[id] == True:
                self.MapWindow.Draw(self.MapWindow.pdc, drawid=id,
                                       img=img, pdctype='image',
                                       coords=self.ovlcoords[id])

        self.MapWindow.UpdateMap()
        dlg.Destroy()

    def addLegend(self, event):
        """
        Handler for legend map decoration menu selection.
        """
        ovltype = id = 1 # index for overlay layer in render
        if ovltype in self.params:
            params = self.params[ovltype]
        else:
            params = ''

        ovldict = self.MapWindow.GetOverlay()
        if id not in ovldict: return
        img = ovldict[id]

        if id not in self.ovlcoords: self.ovlcoords[id] = [10,10]

        # Decoration overlay control dialog
        dlg = DecDialog(self, wx.ID_ANY, 'Legend', size=(350, 200),
                         style=wx.DEFAULT_DIALOG_STYLE,
                         ovltype=ovltype,
                         cmd='d.legend',
                         drawid=id,
                         checktxt = "Show/hide legend",
                         ctrltxt = "legend object",
                         params = params)

        dlg.CenterOnScreen()

        # If OK button pressed in decoration control dialog
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            if self.ovlchk[id] == True:
                self.MapWindow.Draw(self.MapWindow.pdc, drawid=id,
                                       img=img, pdctype='image',
                                       coords=self.ovlcoords[id])

        self.MapWindow.UpdateMap()
        dlg.Destroy()

    def addText(self, event):
        """
        Handler for text decoration menu selection.
        """
        ovltype = 2 # index for overlay layer in render
        maptext = ''
        textfont = self.GetFont()
        textcolor = wx.BLACK
        textcoords = [10,10,10,10]
        rotation = 0

        if self.MapWindow.currtxtid == None: # text doesn't already exist
            id = wx.NewId()+100
        else: # text already exists
            id = self.MapWindow.currtxtid
            textcoords=self.ovlcoords[id]

        dlg = TextDialog(self, wx.ID_ANY, 'Text', size=(400, 200),
                         style=wx.DEFAULT_DIALOG_STYLE,
                         ovltype=ovltype,
                         drawid=id)

        dlg.CenterOnScreen()

        # If OK button pressed in decoration control dialog
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            maptext = dlg.currText
            textfont = dlg.currFont
            textcolor = dlg.currClr
            rotation = dlg.currRot
            coords,w,h = self.MapWindow.textBounds((maptext,textfont,textcolor,rotation),textcoords)

        # delete object if if it has no text
        if maptext == '':
            self.MapWindow.pdc.ClearId(id)
            self.MapWindow.pdc.RemoveId(id)
            del self.MapWindow.textdict[id]
            del self.ovlcoords[id]
            return

        self.MapWindow.pdc.ClearId(id)
        self.MapWindow.pdc.SetId(id)
        self.MapWindow.textdict[id] = (maptext,textfont,textcolor,rotation)
        self.MapWindow.Draw(self.MapWindow.pdc, img=self.MapWindow.textdict[id],
                            drawid=id, pdctype='text', coords=textcoords)
        self.MapWindow.Update()


    def getOptData(self, dcmd, type, params):
        """
        Callback method for decoration overlay command generated by
        dialog created in menuform.py
        """

        # Reset comand and rendering options in render.Map. Always render decoration.
        # Showing/hiding handled by PseudoDC
        self.Map.changeOverlay(type=type, command=dcmd, l_active=True, l_render=False)
        self.params[type] = params

# end of class MapFrame

class DecDialog(wx.Dialog):
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE, ovltype=0, cmd='d.barscale',
            drawid=None, checktxt='', ctrltxt='', params=''):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        """
        Controls setting options and displaying/hiding map overlay decorations
        """

        self.ovltype = ovltype
        self.drawid = drawid
        self.ovlcmd = cmd
        self.ovlchk = self.Parent.MapWindow.ovlchk
        self.params = params #previously set decoration options to pass back to options dialog

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        self.chkbox = wx.CheckBox(self, wx.ID_ANY, checktxt)
        if drawid in self.ovlchk: self.chkbox.SetValue(self.ovlchk[drawid])
        box.Add(self.chkbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        optnbtn = wx.Button(self, wx.ID_ANY, "Set options")
        box.Add(optnbtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, ("Drag %s with mouse in pointer mode\nto position. Double-click to change options" % ctrltxt))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_CHECKBOX, self.onCheck, self.chkbox)
        self.Bind(wx.EVT_BUTTON, self.onOptions, optnbtn)

    def onCheck(self, event):
        """
        Handler for checkbox for displaying/hiding decoration
        """
        check = event.IsChecked()
        self.ovlchk[self.drawid] = check

    def onOptions(self, event):
        """
        Sets option for decoration map overlays
        """

        menuform.GUI().parseCommand(self.ovlcmd, gmpath,
                                    completed=(self.Parent.getOptData,self.ovltype,self.params),
                                    parentframe=None)

class TextDialog(wx.Dialog):
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE,
            ovltype=2,drawid=None):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        """
        Controls setting options and displaying/hiding map overlay decorations
        """

        self.ovltype = ovltype
        self.drawid = drawid

        if drawid in self.Parent.MapWindow.textdict:
            self.currText,self.currFont,self.currClr,self.currRot = self.Parent.MapWindow.textdict[drawid]
        else:
          self.currClr = wx.BLACK
          self.currText = ''
          self.currFont = self.GetFont()
          self.currRot = 0

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Enter text:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.textentry = wx.TextCtrl(self, -1, "", size=(200,-1))
        self.textentry.SetFont(self.currFont)
        self.textentry.SetForegroundColour(self.currClr)
        self.textentry.SetValue(self.currText)
        box.Add(self.textentry, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Rotation:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.rotation = wx.SpinCtrl(self, id=wx.ID_ANY, value="", pos=(30, 50),
                        size=(75,-1), style=wx.SP_ARROW_KEYS)
        self.rotation.SetRange(-360,360)
        self.rotation.SetValue(int(self.currRot))
        box.Add(self.rotation, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        fontbtn = wx.Button(self, wx.ID_ANY, "Set font")
        box.Add(fontbtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, ("Drag text with mouse in pointer mode\nto position. Double-click to change options"))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_BUTTON, self.onSelectFont, fontbtn)
        self.textentry.Bind(wx.EVT_TEXT, self.onText)
        self.rotation.Bind(wx.EVT_TEXT, self.onRotation)

    def onText(self, event):
        self.currText = event.GetString()

    def onRotation(self, event):
        self.currRot = event.GetString()

    def onSelectFont(self, event):
        data = wx.FontData()
        data.EnableEffects(True)
        data.SetColour(self.currClr)         # set colour
        data.SetInitialFont(self.currFont)

        dlg = wx.FontDialog(self, data)

        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            self.currFont = data.GetChosenFont()
            self.currClr = data.GetColour()

            self.textentry.SetFont(self.currFont)
            self.textentry.SetForegroundColour(self.currClr)

            self.Layout()

        dlg.Destroy()

class MapApp(wx.App):
    """
    MapApp class
    """

    def OnInit(self):
        wx.InitAllImageHandlers()
        self.mapFrm = MapFrame(parent=None, id=wx.ID_ANY)
        #self.SetTopWindow(Map)
        self.mapFrm.Show()

        if __name__ == "__main__":
            # redraw map, if new command appears
            self.redraw = False
            status = Command(self, Map)
            status.start()
            self.timer = wx.PyTimer(self.watcher)
            # check each 0.1s
            self.timer.Start(100)

        return 1

    def OnExit(self):
        if __name__ == "__main__":
            # stop the timer
            self.timer.Stop()
            # terminate thread (a bit ugly)
            os.system("""echo "quit" >> %s""" % (cmdfilename))

    def watcher(self):
        """Redraw, if new layer appears"""
        if self.redraw:
            self.mapFrm.ReDraw(None)
        self.redraw = False
        return
# end of class MapApp

if __name__ == "__main__":

    ###### SET command variable
    if len(sys.argv) != 3:
        print __doc__
        sys.exit()

    title = sys.argv[1]
    cmdfilename = sys.argv[2]

    import gettext
    gettext.install("gm_map") # replace with the appropriate catalog name


    if not os.getenv("GRASS_ICONPATH"):
        os.environ["GRASS_ICONPATH"]=os.getenv("GISBASE")+"/etc/gui/icons/"

    print "Starting monitor <%s>" % (title)

    gm_map = MapApp(0)
    # set title
    gm_map.mapFrm.SetTitle ("Map display " + title)
    gm_map.MainLoop()

    if grassenv.env.has_key("MONITOR"):
        os.system("d.mon sel=%s" % grassenv.env["MONITOR"])

    os.remove(cmdfilename)
    os.system("""g.gisenv set="GRASS_PYCMDFILE" """)

    print "Stoping monitor <%s>" % (title)

    sys.exit()
