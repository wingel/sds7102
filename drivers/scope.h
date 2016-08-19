#ifndef _SCOPE_H
#define _SCOPE_H

#include <linux/ioctl.h>

#define SCOPE_IOC_MAGIC 's'

#define IOCTL_SCOPE_RENDER _IOWR(SCOPE_IOC_MAGIC, 0, struct scope_render)

struct scope_render
{
	uint32_t addr;
	uint32_t scale;
	uint32_t count;
	void *buf;
};

#endif /* _SDS7102_SCOPE_H */
