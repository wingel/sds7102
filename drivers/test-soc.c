/* A Linux device driver that test the SoC interface */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/sched.h>
#include <linux/delay.h>
#include <linux/io.h>
#include <linux/random.h>

static const unsigned ddr_base = 0x38000000;
static const unsigned ddr_size = 32 * 1024 * 1024;

struct task_struct *test_soc_task;

static uint32_t seed;

static uint32_t rnd(void)
{
	return seed = seed * 1664525 + 10139042233;
}

static unsigned test_ro(void)
{
	char *m;
	unsigned i;
	unsigned errors = 0;

	m = ioremap(ddr_base, ddr_size);

	for (i = 0; i < (1<<16); i++) {
		uint32_t o = i; // rnd() & 0xffff;
		uint32_t v;
		uint32_t e;
		char *p = m + (64 * 1024 + o) * 4;

		e = ((o ^ (o >> 1)) << 16) | o;
		v = readl(p);

		if (v != e) {
			errors++;
			printk(KERN_INFO "RO mismatch at 0x%08x, expected 0x%08x, got 0x%08x\n",
			       ddr_base + p - m, (unsigned)e, (unsigned)v);

			if (kthread_should_stop())
				break;

			msleep(1);
		}
	}

	iounmap(m);

	return errors;
}

static inline uint32_t pattern(uint32_t i)
{
	switch (0) {
	case 1: return ~(1<<(i&31));
	}
	return rnd();
}

static unsigned test_rw(void)
{
	char *m;
	unsigned i;
	unsigned errors = 0;
	unsigned saved_seed;

	seed = saved_seed = get_random_int();

	m = ioremap_cache(ddr_base, ddr_size);

	for (i = 0; i < 4 * 1024; i++) {
		uint32_t o = i;
		char *p = m + (32 * 1024 + o) * 4;
		uint32_t e = pattern(i);
		writel(e, p);
	}

	iounmap(m);

	seed = saved_seed;

	m = ioremap(ddr_base, ddr_size);

	for (i = 0; i < 4 * 1024; i++) {
		uint32_t o = i;
		char *p = m + (32 * 1024 + o) * 4;
		uint32_t e = pattern(i);
		uint32_t v;

		v = readl(p);

		if (v != e) {
			uint32_t v2 = readl(p);

			errors++;
			printk(KERN_INFO "RW mismatch at 0x%08x, expected 0x%08x, got 0x%08x (0x%08x%s)\n",
			       ddr_base + p - m, (unsigned)e, (unsigned)v,
			       (unsigned)v2, v == v2 ? " SAME" : "");

			if (kthread_should_stop())
				break;

			msleep(1);
		}
	}

	iounmap(m);

	return errors;
}

static void dump(void)
{
	char *m;
	unsigned i;

	m = ioremap(ddr_base, ddr_size);

	for (i = 0; i < 32; i++) {
		char *p = m + (32 * 1024 + i) * 4;
		uint32_t v = readl(p);

		printk(KERN_INFO "0x%08x: 0x%08x\n",
		       ddr_base + p - m, (unsigned)v);
	}

	iounmap(m);
}

static int test_soc_thread_function(void *data)
{
	struct sched_param param;
	unsigned long timeout;
	unsigned count;
	unsigned errors;

	param.sched_priority = 0;
	// sched_setscheduler(current, SCHED_IDLE, &param);

	count = 0;
	errors = 0;
	timeout = jiffies + HZ;

	while (1) {
		errors += test_ro();
		errors += test_rw();

		schedule();

		if (kthread_should_stop())
			break;

		count++;

		if (time_after(jiffies, timeout)) {
			printk(KERN_INFO "%s: %u loops, %u errors\n", __func__, count, errors);
			timeout = jiffies + 10 * HZ;
		}
	}

	dump();

	return 0;
}

static int __init test_soc_init(void)
{
	test_soc_task = kthread_run(&test_soc_thread_function, NULL,
				    "test-soc");

	if (!test_soc_task)
		return -ENOMEM;

	return 0;
}

static void __exit test_soc_cleanup(void)
{
	kthread_stop(test_soc_task);
}

module_init(test_soc_init);
module_exit(test_soc_cleanup);

MODULE_AUTHOR("Christer Weinigel <christer@weinigel.se>");
MODULE_DESCRIPTION("SoC bus tester for SDS7102");
MODULE_LICENSE("GPL");
