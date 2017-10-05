dibs_root = $(dir $(abspath $(lastword $(MAKEFILE_LIST))/..))

$(dibs_root)host/bin/kconfig:$(dibs_root)tools/kconfig-frontends/Makefile
	cd $(dibs_root)tools/kconfig-frontends; make install

$(dibs_root)tools/kconfig-frontends/frontends/conf/kconfig-conf:$(dibs_root)tools/kconfig-frontends/Makefile
	cd $(dibs_root)tools/kconfig-frontends; make

$(dibs_root)tools/kconfig-frontends/Makefile:$(dibs_root)tools/kconfig-frontends/configure
	cd $(dibs_root)tools/kconfig-frontends; ./configure --prefix=$(dibs_root)host/

$(dibs_root)tools/kconfig-frontends/configure:$(dibs_root)tools/kconfig-frontends/configure.ac
	cd $(dibs_root)tools/kconfig-frontends; autoreconf -vi

$(dibs_root)tools/kconfig-frontends/configure.ac:
	cd $(dibs_root); git submodule update --init --recursive

clean:
	rm -rf $(dibs_root)host
	git submodule foreach --recursive git clean -fx

.PHONY: clean setup

