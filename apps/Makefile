ifndef BUILDROOT_DIR
BUILDROOT_DIR := $(shell cd ../buildroot && pwd)
endif

CROSS_COMPILE := "$(BUILDROOT_DIR)/output/host/usr/bin/arm-linux-"
CC := $(CROSS_COMPILE)gcc

CFLAGS := -Wall
CFLAGS += -O2

TARGETS :=
TARGETS += activity
TARGETS += sds-server

all: $(TARGETS)

sds-server: sds-server.o reg.o

sds-server.o: sds-server.c reg.h

reg.o: reg.c reg.h

clean:
	rm -f -- $(TARGETS) *.o *~
