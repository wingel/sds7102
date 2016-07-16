#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <time.h>
#include <string.h>

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
    fprintf(stderr, "r %d\n", r);
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
