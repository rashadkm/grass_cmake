
# common dependencies and rules for building support programs

PACKAGE = "grassmods"

HTMLSRC = $(ETC)/$(PGM)$(EXE)

include $(MODULE_TOPDIR)/include/Make/Vars.make
include $(MODULE_TOPDIR)/include/Make/Rules.make
include $(MODULE_TOPDIR)/include/Make/Html.make
include $(MODULE_TOPDIR)/include/Make/Compile.make
include $(MODULE_TOPDIR)/include/Make/Rest.make

etc: $(ETC)/$(PGM)$(EXE) html rest

$(ETC)/$(PGM)$(EXE): $(ARCH_OBJS) $(DEPENDENCIES)
	$(call linker)

.PHONY: etc
