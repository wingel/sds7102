#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <time.h>

#include <arpa/inet.h>

/* this table must match the table in _sds7102.py */
static const char *names[] = {
    /* bank0 */
    "B5",  "A5",
    "D6",  "C6",  "B8",

    /* bank2 */
    "M12", "M11", "T10", "N12",
    "P12", "N11", "P11", "N9",  "P9",
    "L10", "M10", "R9",  "T9",  "M9",
    "N8",  "P8",  "T8",  "P7",  "M7",
    "R7",  "T7",  "P6",  "T6",  "R5",
    "T5",  "N5",  "P5",  "L8",  "L7",
    "P4",  "T4",  "M6",  "N6",  "T3",

     /* bank3 */
    "M4",  "M3",  "M5",  "N4",  "R2",
    "R1",  "P2",  "P1",  "N3",  "N1",
    "M2",  "M1",  "L3",  "L1",  "K2",
    "K1",  "J3",  "J1",  "H2",  "H1",
    "G3",  "G1",  "F2",  "F1",  "K3",
    "J4",  "J6",  "H5",  "H4",  "H3",
    "L4",  "L5",  "E2",  "E1",  "K5",
    "K6",  "C3",  "C2",  "D3",  "D1",
    "C1",  "B1",  "G6",  "G5",  "B2",
    "A2",  "F4",  "F3",  "E4",  "E3",
    "F6",  "F5",  "B3",  "A3",

    "Ref",                      /* 10MHz reference clock */

    "Tr1", "Tr2",               /* Triggers */
    "Vd1", "Vd2", "Hd1", "Hd2", /* Vertical Sync, Horizonal Sync */
    "AC",                       /* AC Trigger */

    "Prb",                      /* Probe compensation output */
    "Ext",                      /* External trigger output */

    "SCL", "SDA",               /* AT88SC I2C SCL and SDA */

    "R11"                       /* CCLK */
};

#define COUNT (sizeof(names) / sizeof(*names) + 5)

int main()
{
    uint32_t buf[COUNT];
    uint32_t last[COUNT];
    int fd;
    int r;
    int i;
    struct timespec ts0, ts;

    for (i = 0; i < COUNT; i++)
	last[i] = 0;

    while (1)
    {
	clock_gettime(CLOCK_MONOTONIC, &ts0);

	fd = open("/dev/regs", O_RDWR);
	assert(fd >= 0);
	buf[0] = htonl((0 << 1) | 1);
	r = write(fd, buf, 4);
	printf("write -> %d\n", r);
	assert(r == 4);
	r = read(fd, buf, sizeof(buf));
	printf("read -> %d\n", r);
	assert(r == sizeof(buf));

	if (1)
	{
	    for (i = 0; i < COUNT; i++)
	    {
		buf[i] = ntohl(buf[i]);
		if (0)		/* gray decoder */
		{
		    uint32_t b = buf[i] >> 31;
		    buf[i] &= (1u<<31)-1;
		    buf[i] = buf[i] ^ (buf[i] >> 16);
		    buf[i] = buf[i] ^ (buf[i] >> 8);
		    buf[i] = buf[i] ^ (buf[i] >> 4);
		    buf[i] = buf[i] ^ (buf[i] >> 2);
		    buf[i] = buf[i] ^ (buf[i] >> 1);
		    buf[i] |= (b << 31);
		}
	    }
	}

	for (i = 0; i < COUNT; i++)
	{
	    uint32_t v = buf[i];

	    if (!(i % 5))
	    {
		if (i)
		    printf("\n");
		printf("%3u", i);
	    }
	    if (0)
		printf(" %08x", v);
	    else
	    {
		unsigned delta = (v - last[i]) & ((1u<<31)-1);

		if (i < sizeof(names) / sizeof(*names))
		    printf("  %-3s", names[i]);
		else
		    printf("  %-3s", "-");

		if (delta >= 1E9)
		    printf(" %5.1fG", delta / 1E9);
		else if (delta >= 1E6)
		    printf(" %5.1fM", delta / 1E6);
		else if (delta >= 1E3)
		    printf(" %5.1fk", delta / 1E3);
		else
		    printf("  %5d", delta);

		printf(" %c", v & (1u<<31) ? '^' : 'v');
	    }

	    last[i] = v;
	}
	printf("\n");
	fflush(stdout);

	usleep(300000);
	close(fd);

	do
	{
	    usleep(1000);
	    clock_gettime(CLOCK_MONOTONIC, &ts);
	}
	while (((ts.tv_sec - ts0.tv_sec) * 1000000000 +
		(ts.tv_nsec - ts0.tv_nsec)) < 1000000000);
    }
}

