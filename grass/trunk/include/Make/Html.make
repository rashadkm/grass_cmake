#NOTE: parts of the header are generated in ../../lib/gis/parser.c

HTMLDIR = $(ARCH_DISTDIR)/docs/html

# generic html rules for all commands

ifdef CROSS_COMPILING

htmlcmd:

htmlscript:

htmletc:

htmldir:

htmlmulti:

else

$(HTMLDIR)/$(PGM).html: $(PGM).html $(PGM).tmp.html
	-test -d $(HTMLDIR) || $(MKDIR) $(HTMLDIR)
	$(MODULE_TOPDIR)/tools/mkhtml.sh $(PGM) > $@
	-for file in  *.png *.jpg ; do \
		head -n 1 $$file | grep '^\#!' > /dev/null ; \
		if [ $$? -ne 0 ] ; then \
		   $(INSTALL_DATA) $$file $(HTMLDIR) ; \
		fi \
		done 2> /dev/null ; true

$(PGM).tmp.html: $(HTMLSRC)
	if [ "$(HTMLSRC)" != "" ] ; then \
		GISRC=$(RUN_GISRC) \
		GISBASE=$(RUN_GISBASE) \
		PATH="$(BIN):$$PATH" \
		$(LD_LIBRARY_PATH_VAR)="$(BIN):$(ARCH_LIBDIR):$($(LD_LIBRARY_PATH_VAR))" \
		LC_ALL=C \
		$(HTMLSRC) --html-description < /dev/null | grep -v '</body>\|</html>' > $@ ; \
	fi

# html rules for cmd commands
htmlcmd:
	$(MAKE) $(HTMLDIR)/$(PGM).html HTMLSRC=$(BIN)/$(PGM)$(EXE)

# html rules for scripts
htmlscript:
	$(MAKE) $(HTMLDIR)/$(PGM).html HTMLSRC=$(SCRIPTDIR)/$(PGM)

# html rules for ETC commands
htmletc:
	$(MAKE) $(HTMLDIR)/$(PGM).html HTMLSRC=$(ETC)/$(PGM)$(EXE)

# html rules for intro pages in directories
htmldir:
	$(MAKE) $(HTMLDIR)/$(PGM).html

# html rules for multiple commands
htmlmulti:
	for prog in $(PROGRAMS) ; do $(MAKE) htmlcmd PGM=$$prog ; done

endif

.PHONY: htmlcmd htmletc htmlscript htmldir htmlmulti
