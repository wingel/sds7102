#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <time.h>
#include <string.h>

#include <sys/mman.h>

#include "reg.h"

#define ARRAY_SIZE(a) (sizeof(a) / sizeof(*a))

static void set_gpio(unsigned pin, const char *value)
{
    int fd;
    char s[128];
    int r;
    int i;

    snprintf(s, sizeof(s), "/sys/class/gpio/gpio%u/direction", pin);
    fd = open(s, O_RDWR);
    if (fd == -1)
    {
	sprintf(s, "%u", pin);
	fd = open("/sys/class/gpio/export", O_WRONLY);
	assert(fd != -1);
	r = write(fd, s, strlen(s));
	assert(r != -1);
	close(fd);

	snprintf(s, sizeof(s), "/sys/class/gpio/gpio%u/direction", pin);
    }
    for (i = 0; i < 1000; i++)
    {
	fd = open(s, O_RDWR);
	if (fd != -1)
	    break;
	usleep(100000);
    }
    assert(fd != -1);
    r = write(fd, value, strlen(value));
    // fprintf(stderr, "r %d\n", r);
    if (r == -1)
	perror("r");
    assert(r == strlen(value));
    close(fd);
}

static char *tok(char **ps)
{
    char *s = *ps;
    char *p;

    while (*s && isspace(*s))
	s++;

    p = s;

    while (*s && !isspace(*s))
	s++;

    if (*s)
	*s++ = '\0';

    *ps = s;

    return p;
}

int main(int argc, char *argv[])
{
    char s[65536];
    char *p;
    char *start;
    char *end;
    uint32_t buf[65536];
    volatile uint32_t *soc;
    int fd;

    fd = open("/dev/mem", O_RDWR);
    assert(fd != -1);
    soc = mmap(NULL, 64*1024*1024, PROT_READ | PROT_WRITE, MAP_SHARED, fd,
               0x38000000);
    assert(soc != MAP_FAILED);

    while (fgets(s, sizeof(s), stdin) != NULL)
    {
	p = s;
	start = tok(&p);

	if (!*start)
	    ;
	else if (!strcasecmp(start, "write_fpga"))
	{
	    uint32_t addr;
	    unsigned n;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: write_fpga needs an address\n");
		goto err;
	    }

	    addr = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid address \"%s\"\n", start);
		goto err;
	    }

	    for (n = 0; n < ARRAY_SIZE(buf); n++)
	    {
		start = tok(&p);
		if (!*start)
		    break;

		buf[n] = strtoul(start, &end, 0);
		if (*end)
		{
		    printf("error: invalid value \"%s\"\n", start);
		    goto err;
		}

	    }

	    if (!n)
	    {
		printf("write_fpga needs at least one value\n\n");
		goto err;
	    }

	    write_regs(addr, buf, n);
	}
	else if (!strcasecmp(start, "read_fpga"))
	{
	    uint32_t addr;
	    unsigned count;
	    unsigned i;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: read_fpga needs an address\n");
		goto err;
	    }

	    addr = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid address \"%s\"\n", start);
		goto err;
	    }

	    start = tok(&p);
	    if (!*start)
		count =1;
	    else
	    {
		count = strtoul(start, &end, 0);
		if (*end || count > ARRAY_SIZE(buf))
		{
		    printf("error: invalid count \"%s\"\n", start);
		    goto err;
		}
	    }

	    read_regs(addr, buf, count);

	    for (i = 0; i < count; i++)
		printf("0x%08x\n", buf[i]);
	}
	else if (!strcasecmp(start, "write_soc"))
	{
	    uint32_t addr;
	    unsigned n;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: write_soc needs an address\n");
		goto err;
	    }

	    addr = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid address \"%s\"\n", start);
		goto err;
	    }

	    for (n = 0; n < ARRAY_SIZE(buf); n++)
	    {
		start = tok(&p);
		if (!*start)
		    break;

		soc[addr+n] = strtoul(start, &end, 0);
		if (*end)
		{
		    printf("error: invalid value \"%s\"\n", start);
		    goto err;
		}

	    }

	    if (!n)
	    {
		printf("write_soc needs at least one value\n\n");
		goto err;
	    }
	}
	else if (!strcasecmp(start, "read_soc"))
	{
	    uint32_t addr;
	    unsigned count;
	    unsigned i;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: read_soc needs an address\n");
		goto err;
	    }

	    addr = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid address \"%s\"\n", start);
		goto err;
	    }

	    start = tok(&p);
	    if (!*start)
		count =1;
	    else
	    {
		count = strtoul(start, &end, 0);
		if (*end || count > ARRAY_SIZE(buf))
		{
		    printf("error: invalid count \"%s\"\n", start);
		    goto err;
		}
	    }

	    for (i = 0; i < count; i++)
		printf("0x%08x\n", (unsigned)soc[addr+i]);
	}
	else if (!strcasecmp(start, "write_ddr"))
	{
	    uint32_t addr;
	    unsigned i, n;
            volatile uint32_t v;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: write_ddr needs an address\n");
		goto err;
	    }

	    addr = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid address \"%s\"\n", start);
		goto err;
	    }

            while (1)
            {
                uint32_t buf[64];

                v = soc[0x201];
                if (!((v >> 4) & 1))
                {
                    printf("write fifo not empty, status 0x%08x\n", (unsigned)v);
                    goto err;
                }

                for (n = 0; n < 64; n++)
                {
                    start = tok(&p);
                    if (!*start)
                        break;

                    buf[n] = strtoul(start, &end, 0);

                    if (*end)
                    {
                        printf("error: invalid value \"%s\"\n", start);
                        goto err;
                    }
                }

                if (!n)
                    break;

                /* There seems to be a write buffer in the CPU which
                 * merges writes to the same adress.  There is a CP15
                 * call which can be used to flush this buffer but
                 * userspace code is not allowed to call it.  Use a
                 * usleep to wait for the writes to reach the FPGA.
                 * This stuff ought to be moved to the kernel so that
                 * we can do proper flushes instead. */
                for (i = 0; i < n; i++)
                {
                    soc[0x210] = buf[i]; /* fill FIFO */
                    usleep(10000);       /* need this to defeat the write buffer */
                }

                for (i = 10000; i; i--)
                {
                    v = soc[0x201];
                    if (((v >> 8) & 0x7f) == n)
                        break;
                }
                if (!i)
                {
                    printf("write fifo timeout, status 0x%08x\n", (unsigned)v);
                    fprintf(stderr, "counts 0x%08x\n", (unsigned)soc[0x202]);
                    goto err;
                }

                soc[0x200] = addr | ((n-1)<<24) | (0<<30); /* write */

                for (i = 10000; i; i--)
                {
                    v = soc[0x201];
                    if (((v >> 4) & 1))
                        break;
                }
                if (!i)
                {
                    printf("write timeout, status 0x%08x\n", (unsigned)v);
                    goto err;
                }

                if (((v >> 7) & 1))
                {
                    printf("write underrun, status 0x%08x\n", (unsigned)v);
                    goto err;
                }

                addr += n;
	    }
	}
	else if (!strcasecmp(start, "read_ddr"))
	{
	    uint32_t addr;
	    unsigned count;
	    unsigned n, i;
            uint32_t v;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: read_ddr needs an address\n");
		goto err;
	    }

	    addr = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid address \"%s\"\n", start);
		goto err;
	    }

	    start = tok(&p);
	    if (!*start)
		count =1;
	    else
	    {
		count = strtoul(start, &end, 0);
		if (*end || count > ARRAY_SIZE(buf))
		{
		    printf("error: invalid count \"%s\"\n", start);
		    goto err;
		}
	    }

            while (count)
            {
                n = count;
                if (n > 32)
                    n = 32;

                v = soc[0x201];
                if (!((v >> 15) & 1))
                {
                    printf("read fifo not empty, status 0x%08x\n", (unsigned)v);
                    goto err;
                }

                v = addr | ((n-1)<<24) | (1<<30); /* read */
                fprintf(stderr, "0x200 <- 0x%08x\n", (unsigned)v);
                soc[0x200] = v;

                for (i = 10000; i; i--)
                {
                    v = soc[0x201];

                    if (((v >> 19) & 0x7f) == n)
                        break;
                }
                if (!i)
                {
                    printf("read timeout, status 0x%08x\n", (unsigned)v);
                    goto err;
                }

                /* empty FIFO */
                for (i = 0; i < n; i++)
                {
                    volatile uint32_t t = soc[0x211];
                    printf("0x%08x\n", (unsigned)t);
                }

                addr += n;
                count -= n;
            }

            v = soc[0x201];
            if (!((v >> 15) & 1))
            {
                printf("read fifo not empty after, status 0x%08x\n", (unsigned)v);
                goto err;
            }
	}
	else if (!strcasecmp(start, "set_gpio"))
	{
	    unsigned pin;
	    unsigned value;

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: set_gpio needs a pin number\n");
		goto err;
	    }

	    pin = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid pin number \"%s\"\n", start);
		goto err;
	    }

	    start = tok(&p);
	    if (!*start)
	    {
		printf("error: set_gpio needs a pin value\n");
		goto err;
	    }

	    value = strtoul(start, &end, 0);
	    if (*end)
	    {
		printf("error: invalid pin value \"%s\"\n", start);
		goto err;
	    }

	    set_gpio(pin, value ? "high" : "low");
	}
	else
	{
	    printf("invalid command \"%s\"\n", start);
	}

    err:
	fflush(stdout);
    }

    exit(0);
}
