ifndef BUILDROOT_DIR
BUILDROOT_DIR := $(shell cd ../buildroot && pwd)
endif

CROSS_COMPILE := "$(BUILDROOT_DIR)/output/host/usr/bin/arm-linux-"
CC := $(CROSS_COMPILE)gcc

CFLAGS := -Wall
CFLAGS += -O2

TARGETS :=
TARGETS += activity

all: $(TARGETS)

clean:
	rm -f -- $(TARGETS) *.o *~
