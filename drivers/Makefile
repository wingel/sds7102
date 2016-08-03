ifndef KBUILD_CFLAGS

ifndef BUILDROOT_DIR
BUILDROOT_DIR := $(shell cd ../buildroot && pwd)
endif

ifndef CROSS_COMPILE
CROSS_COMPILE := "$(BUILDROOT_DIR)/output/host/usr/bin/arm-linux-"
endif

ifndef LINUX_DIR
LINUX_DIR := $(shell cd ../linux && pwd)
endif

ARCH := arm

all: modules

modules:
	$(MAKE) -C $(LINUX_DIR) ARCH=$(ARCH) CROSS_COMPILE="$(CROSS_COMPILE)" \
	    M="`pwd`" modules

clean:
	rm -f -- *.ko *.o *~ *.mod.c .??*.cmd \#* .\#* Module* modules.order
	rm -rf -- .tmp_versions

else

obj-m += fpga.o
obj-m += gpios.o
obj-m += regs.o
obj-m += test-soc.o
obj-m += sds7102-frontpanel.o

endif
