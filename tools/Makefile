all:
	#do nothing

$(DIBS_ROOT)/host/bin/kconfig:$(DIBS_ROOT)/tools/kconfig-frontends/Makefile
	cd $(DIBS_ROOT)/tools/kconfig-frontends; make install

$(DIBS_ROOT)/tools/kconfig-frontends/frontends/conf/kconfig-conf:$(DIBS_ROOT)/tools/kconfig-frontends/Makefile
	cd $(DIBS_ROOT)/tools/kconfig-frontends; make

$(DIBS_ROOT)/tools/kconfig-frontends/Makefile:$(DIBS_ROOT)/tools/kconfig-frontends/configure
	cd $(DIBS_ROOT)/tools/kconfig-frontends; ./configure --prefix=$(DIBS_ROOT)/host/

$(DIBS_ROOT)/tools/kconfig-frontends/configure:$(DIBS_ROOT)/tools/kconfig-frontends/configure.ac
	cd $(DIBS_ROOT)/tools/kconfig-frontends; autoreconf -vi

$(DIBS_ROOT)/tools/kconfig-frontends/configure.ac:
	cd $(DIBS_ROOT); git submodule update --init --recursive

clean:
	rm -rf $(DIBS_ROOT)/host
	git submodule foreach --recursive git clean -fx

.PHONY: clean all

