/**
   \file map_obj.cpp
   
   \brief Experimental C++ wxWidgets Nviz prototype -- map object management

   Used by wxGUI Nviz extension.

   Copyright: (C) by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the file COPYING that comes with GRASS
   for details.

   \author Martin Landa <landa.martin gmail.com> (Google SoC 2008)

   \date 2008
*/

#include "nviz.h"

/*!
  \brief Set surface topography

  \param id surface id
  \param map if true use map otherwise constant
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceTopo(int id, bool map, const char *value)
{
    return SetSurfaceAttr(id, ATT_TOPO, map, value);
}

/*!
  \brief Set surface color

  \param id surface id
  \param map if true use map otherwise constant
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceColor(int id, bool map, const char *value)
{
    return SetSurfaceAttr(id, ATT_COLOR, map, value);
}

/*!
  \brief Set surface mask

  @todo invert

  \param id surface id
  \param invert if true invert mask 
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceMask(int id, bool invert, const char *value)
{
    return SetSurfaceAttr(id, ATT_MASK, true, value);
}

/*!
  \brief Set surface mask

  @todo invert

  \param id surface id
  \param map if true use map otherwise constant
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceTransp(int id, bool map, const char *value)
{
    return SetSurfaceAttr(id, ATT_TRANSP, map, value);
}

/*!
  \brief Set surface shininess

  \param id surface id
  \param map if true use map otherwise constant
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceShine(int id, bool map, const char *value)
{
    return SetSurfaceAttr(id, ATT_SHINE, map, value);
}

/*!
  \brief Set surface emission

  \param id surface id
  \param map if true use map otherwise constant
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceEmit(int id, bool map, const char *value)
{
    return SetSurfaceAttr(id, ATT_EMIT, map, value);
}

/*!
  \brief Set surface attribute

  \param id surface id
  \param attr attribute desc
  \param map if true use map otherwise constant
  \param value map name of value

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetSurfaceAttr(int id, int attr, bool map, const char *value)
{
    int ret;

    if (map) {
	ret = Nviz_set_attr(id, MAP_OBJ_SURF, attr, MAP_ATT,
			    value, -1.0,
			    data);
    }
    else {
	float val;
	if (attr == ATT_COLOR) {
	    val = Nviz_color_from_str(value);
	}
	else {
	    val = atof(value);
	}
	ret = Nviz_set_attr(id, MAP_OBJ_SURF, attr, CONST_ATT,
			    NULL, val,
			    data);
    }
	
    G_debug(1, "Nviz::SetSurfaceAttr(): id=%d, attr=%d, map=%d, value=%s",
	    id, attr, map, value);

    return ret;
}

/*!
  \brief Unset surface mask

  \param id surface id

  \return 1 on success
  \return 0 on failure
*/

int Nviz::UnsetSurfaceMask(int id)
{
    return UnsetSurfaceAttr(id, ATT_MASK);
}

/*!
  \brief Unset surface transparency

  \param id surface id

  \return 1 on success
  \return 0 on failure
*/

int Nviz::UnsetSurfaceTransp(int id)
{
    return UnsetSurfaceAttr(id, ATT_TRANSP);
}

/*!
  \brief Unset surface emission

  \param id surface id

  \return 1 on success
  \return 0 on failure
*/

int Nviz::UnsetSurfaceEmit(int id)
{
    return UnsetSurfaceAttr(id, ATT_EMIT);
}

/*!
  \brief Unset surface attribute

  \param id surface id
  \param attr attribute descriptor

  \return 1 on success
  \return 0 on failure
*/
int Nviz::UnsetSurfaceAttr(int id, int attr)
{
    return Nviz_unset_attr(id, MAP_OBJ_SURF, attr);
}

/*!
  \brief Set surface resolution

  \param id surface id
  \param fine x/y fine resolution
  \param coarse x/y coarse resolution

  \return -1 on error
  \return 0 on success
*/
int Nviz::SetSurfaceRes(int id, int fine, int coarse)
{
    return GS_set_drawres(id, fine, fine, coarse, coarse);
}

/*!
  \brief Set draw style

  Draw styles:
   - DM_GOURAUD
   - DM_FLAT
   - DM_FRINGE
   - DM_WIRE
   - DM_COL_WIRE
   - DM_POLY
   - DM_WIRE_POLY
   - DM_GRID_WIRE
   - DM_GRID_SURF

  \param id surface id (<= 0 for all)
  \param style draw style

  \return 0 on success
  \return -1 on error
*/
int Nviz::SetSurfaceStyle(int id, int style)
{
    if (id > 0) {
	return GS_set_drawmode(id, style);
    }

    return GS_setall_drawmode(style);
}

/*!
  \brief Set color of wire

  \todo all

  \param surface id
  \param color color string (R:G:B)

  \return 1
*/
int Nviz::SetWireColor(int id, const char* color)
{
    GS_set_wire_color(id, Nviz_color_from_str(color));

    return 1;
}
