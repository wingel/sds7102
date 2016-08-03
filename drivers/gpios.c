/* Test driver which detects GPIO activity.
 *
 * Copyright (C) 2016 Christer Weinigel <christer@weinigel.se>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation version 2.
 *
 * A Linux device driver that watches for GPIO changes on the SDS7102
 * scope.  Just do a "insmod gpios.ko" and it will print a log message
 * to the console every time one of the watched GPIOs change. */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/sched.h>
#include <linux/delay.h>
#include <linux/io.h>

struct rmv
{
	const char *name;
	uint32_t addr;
	uint32_t mask;
	uint32_t value;
};

/* List of GPIO registers to modify. It sets up a bunch of GPIOs as
 * inputs with pull ups or pull downs. */
struct rmv mods[] = {
	{ "GPACON", 0x56000000, ~0x00000000, 0x00000000 },
	{ "GPBCON", 0x56000010, ~0x000c03c0, 0x00000000 },
	{ "GPBUDP", 0x56000018, ~0xffffffff, 0x55555555 },
	{ "GPBSEL", 0x5600001c, ~0x00000000, 0x00000000 },
	{ "GPCCON", 0x56000020, ~0x0000fc03, 0x00000000 },
	{ "GPCUDP", 0x56000028, ~0xffffffff, 0x55555555 },
	{ "GPECON", 0x56000040, ~0xf03fffff, 0x00000000 },
	{ "GPEUDP", 0x56000048, ~0xffffffff, 0x55555555 },
	{ "GPESEL", 0x5600004c, ~0x00000000, 0x00000000 },
	{ "GPFCON", 0x56000050, ~0xfffffff3, 0x00000000 },
	{ "GPFUDP", 0x56000058, ~0xffffffff, 0x55555545 },
	{ "GPGCON", 0x56000060, ~0x0000303f, 0x00000000 },
	{ "GPGUDP", 0x56000068, ~0xffffffff, 0x55555555 },
	{ "GPHCON", 0x56000070, ~0xfffffff0, 0x00000000 },
	{ "GPHUDP", 0x56000078, ~0xffffffff, 0x55555555 },
	{ "GPKCON", 0x560000e0, ~0x00000000, 0x00000000 },
	{ "GPKUDP", 0x560000e8, ~0xffffffff, 0x55555555 },
	{ "GPLCON", 0x560000f0, ~0x00000000, 0x00000000 },
	{ "GPLUDP", 0x560000f8, ~0xffffffff, 0x55555555 },
	{ "GPMCON", 0x56000100, ~0x00000000, 0x00000000 },
	{ "GPMUDP", 0x56000108, ~0x00000000, 0x00000000 },
	{ "GPMSEL", 0x5600010c, ~0x00000000, 0x00000000 },
};

/* List of GPIO registers to watch for changes. */
struct rmv checks[] = {
	{ "GPADAT", 0x56000004, ~0x00008003 },
	{ "GPBDAT", 0x56000014, ~0x00000000 },
	{ "GPCDAT", 0x56000024, ~0x0000fffe },
	{ "GPDDAT", 0x56000034, ~0x0000ffff },
	{ "GPEDAT", 0x56000044, ~0x0000380a },
	{ "GPFDAT", 0x56000054, ~0x00000002 },
	{ "GPGDAT", 0x56000064, ~0x00000000 },
	{ "GPHDAT", 0x56000074, ~0x00001a03 },
	{ "GPKDAT", 0x560000e4, ~0x000028a8 },
	{ "GPLDAT", 0x560000f4, ~0x00002000 },
	{ "GPMDAT", 0x56000104, ~0x00000000 },
};

struct task_struct *task;

static int thread_function(void *data)
{
	char *m = ioremap(0x48000000, 0x18000000);
	int i;

	for (i = 0; i < ARRAY_SIZE(mods); i++) {
		struct rmv *mod = &mods[i];
		uint32_t value;
		uint32_t newvalue;

		value = readl(m + (mod->addr - 0x48000000));
		newvalue = (value & mod->mask) | mod->value;

		printk("%s 0x%08x -> 0x%08x\n",
		       mod->name, value, newvalue);

		writel(newvalue, m + (mod->addr - 0x48000000));

		if (0)
			msleep(1000);
	}

	while (!kthread_should_stop()) {
		for (i = 0; i < ARRAY_SIZE(checks); i++) {
			struct rmv *check = &checks[i];
			uint32_t value;
			uint32_t diff;

			value = readl(m + (check->addr - 0x48000000));

			diff = (check->value ^ value) & check->mask;
			if (diff) {
				printk("%s 0x%08x -> 0x%08x diff 0x%08x\n",
				       check->name, check->value, value, diff);
				check->value = value;
			}
		}
		msleep(1);
	}

	iounmap(m);

	return 0;
}

static int __init gpios_init(void)
{
	task = kthread_run(&thread_function, NULL, "gpios");

	if (!task)
		return -ENOMEM;

	return 0;
}

static void __exit gpios_cleanup(void)
{
	kthread_stop(task);
}

module_init(gpios_init);
module_exit(gpios_cleanup);

MODULE_AUTHOR("Christer Weinigel <christer@weinigel.se>");
MODULE_DESCRIPTION("GPIO tester for SDS7102");
MODULE_LICENSE("GPL");
