#include "reg.h"

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <time.h>
#include <string.h>

#include <arpa/inet.h>

#define FN "/dev/regs"

void read_regs(uint32_t addr, uint32_t *buf, unsigned count)
{
    int fd;
    int r;
    uint32_t t;
    unsigned i;

    for (i = 0; i < 1000; i++)
    {
	fd = open(FN, O_RDWR);
	if (fd != -1)
	    break;
	usleep(100000);
    }
    assert(fd >= 0);
    t = htonl((addr << 1) | 1);
    r = write(fd, &t, 4);
    assert(r == 4);
    r = read(fd, buf, count * 4);
    assert(r == count * 4);
    close(fd);

    for (i = 0; i < count; i++)
	buf[i] = ntohl(buf[i]);
}

void write_regs(uint32_t addr, const uint32_t *buf, unsigned count)
{
    int fd;
    int r;
    uint32_t t;
    unsigned i;
    uint32_t tmp_buf[count];

    for (i = 0; i < count; i++)
	tmp_buf[i] = htonl(buf[i]);

    for (i = 0; i < 1000; i++)
    {
	fd = open(FN, O_RDWR);
	if (fd != -1)
	    break;
	usleep(100000);
    }
    assert(fd >= 0);
    t = htonl((addr << 1) | 0);
    r = write(fd, &t, 4);
    assert(r == 4);
    r = write(fd, tmp_buf, count * 4);
    assert(r == count * 4);
    close(fd);
}

uint32_t read_reg(uint32_t addr)
{
    uint32_t v;
    read_regs(addr, &v, 1);
    return v;
}

void write_reg(uint32_t addr, uint32_t v)
{
    write_regs(addr, &v, 1);
}
