/* A driver to program the Xilinx FPGA on the SDS7102 scope.
 *
 * Copyright (C) 2016 Christer Weinigel <christer@weinigel.se>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation version 2.
 */

/*
 * When the device is opened the FPGA is initialized by pulling PROG_B
 * low and then waiting for INIT_B to go hi.  Userspace then writes
 * the bitstream to the device using CCLK and DIN.  When the device is
 * closed it continues toggling CCLK until DONE goes high.
 *
 * From userspace this means that programming the FPGA is as easy as
 * "cat image.bin >/dev/fpga".
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/slab.h>
#include <linux/miscdevice.h>
#include <linux/delay.h>
#include <linux/errno.h>
#include <linux/gpio.h>
#include <linux/mutex.h>
#include <linux/uaccess.h>
#include <linux/sched.h>

#include <mach/gpio-samsung.h>
#include <plat/gpio-cfg.h>

#define DRIVER_NAME "sds7102-fpga"
#define DEVICE_NAME "fpga"

#define FPGA_PROG_B	S3C2410_GPK(7)
#define FPGA_INIT_B	S3C2410_GPK(13)
#define FPGA_DONE	S3C2410_GPK(5)
#define FPGA_CCLK	S3C2410_GPK(3)
#define FPGA_DIN	S3C2410_GPK(11)

static const struct {
	const char *name;
	unsigned pin;
} fpga_pins[] = {
	{ "FPGA PROG_B", FPGA_PROG_B, },
	{ "FPGA INIT_B", FPGA_INIT_B, },
	{ "FPGA DONE",	 FPGA_DONE, },
	{ "FPGA CCLK",	 FPGA_CCLK,   },
	{ "FPGA DIN",	 FPGA_DIN,    },
};

static struct miscdevice *fpga_mdev;
static DEFINE_MUTEX(fpga_mutex);
static unsigned fpga_open_count;
static char fpga_pin_requested[ARRAY_SIZE(fpga_pins)];

static int fpga_open(struct inode *inode, struct file *file)
{
	int r = 0;
	unsigned n;
	unsigned long timeout;

	pr_info("%s:\n", __func__);

	mutex_lock(&fpga_mutex);

	if (fpga_open_count) {
		mutex_unlock(&fpga_mutex);
		return -EBUSY;
	}
	fpga_open_count++;

	for (n = 0; n < ARRAY_SIZE(fpga_pins); n++) {
		r = gpio_request(fpga_pins[n].pin, fpga_pins[n].name);
		if (r) {
			pr_warning("%s: failed to allocate gpio %s (%u)\n",
				   __func__,
				   fpga_pins[n].name,
				   fpga_pins[n].pin);
		}
		else
			fpga_pin_requested[n] = 1;
	}

	s3c_gpio_setpull(FPGA_INIT_B, S3C_GPIO_PULL_UP);
	s3c_gpio_setpull(FPGA_DONE, S3C_GPIO_PULL_UP);
	s3c_gpio_setpull(FPGA_DIN, S3C_GPIO_PULL_UP);

	gpio_direction_output(FPGA_PROG_B, 0);
	gpio_direction_input(FPGA_INIT_B);
	gpio_direction_input(FPGA_DONE);
	gpio_direction_output(FPGA_CCLK, 0);
	gpio_direction_output(FPGA_DIN, 1);

	msleep(1);

	printk("INIT_B %u\n", gpio_get_value(FPGA_INIT_B));

	gpio_set_value(FPGA_PROG_B, 1);

	printk("INIT_B %u\n", gpio_get_value(FPGA_INIT_B));

	timeout = jiffies + HZ;
	while (!gpio_get_value(FPGA_INIT_B)) {
		if (time_after(jiffies, timeout)) {
			pr_err("%s: timeout waiting for INIT_B to go high\n",
			       __func__);
			r = -ETIMEDOUT;
			goto err;
		}
		msleep(1);
	}

	printk("INIT_B %u\n", gpio_get_value(FPGA_INIT_B));
	printk("DONE %u\n", gpio_get_value(FPGA_DONE));

	msleep(1);

	mutex_unlock(&fpga_mutex);
	return 0;

err:
	for (n = 0; n < ARRAY_SIZE(fpga_pins); n++) {
		if (fpga_pin_requested[n]) {
			gpio_free(fpga_pins[n].pin);
			fpga_pin_requested[n] = 0;
		}
	}
	fpga_open_count--;

	mutex_unlock(&fpga_mutex);
	return r;
}

static ssize_t fpga_write(struct file *file,
			  const char *buf, size_t len, loff_t *off)
{
	int r = 0;
	unsigned i;
	size_t n;
	uint8_t *tmp;
	uint8_t *p;

	tmp = kmalloc(len, GFP_KERNEL);
	if (!tmp)
		return -ENOMEM;

	if (copy_from_user(tmp, buf, len)) {
		kfree(tmp);
		return -EFAULT;
	}

	mutex_lock(&fpga_mutex);
	p = tmp;
	for (n = 0; n < len; n++) {
		uint8_t b = *p++;

		for (i = 0; i < 8; i++) {
			gpio_set_value(FPGA_CCLK, 0);
			if (b & 0x80)
				gpio_set_value(FPGA_DIN, 1);
			else
				gpio_set_value(FPGA_DIN, 0);
			gpio_set_value(FPGA_CCLK, 1);
			b <<= 1;
		}

		/* Since we're busy-waiting, schedule periodically to
		 * give other tasks some time to run. */
		if ((n & 1023) == 0)
			schedule();
	}
	mutex_unlock(&fpga_mutex);

	kfree(tmp);

	if (!r)
		r = len;

	return r;
}

static int fpga_release(struct inode *inode, struct file *file)
{
	unsigned n;
	unsigned long timeout;
	int r = 0;

	mutex_lock(&fpga_mutex);

	printk("INIT_B %u\n", gpio_get_value(FPGA_INIT_B));
	printk("DONE %u\n", gpio_get_value(FPGA_DONE));

	gpio_direction_input(FPGA_DIN);

	timeout = jiffies + HZ;
	while (!gpio_get_value(FPGA_DONE)) {
		gpio_set_value(FPGA_CCLK, 0);
		gpio_set_value(FPGA_CCLK, 1);

		if (time_after(jiffies, timeout)) {
			pr_err("%s: timeout waiting for DONE to go high\n",
			       __func__);
			r = -ETIMEDOUT;
			break;
		}
	}

	gpio_set_value(FPGA_CCLK, 0);

	gpio_direction_input(FPGA_INIT_B);
	gpio_direction_input(FPGA_DONE);
	gpio_direction_input(FPGA_CCLK);
	gpio_direction_input(FPGA_DIN);

	for (n = 0; n < ARRAY_SIZE(fpga_pins); n++) {
		if (fpga_pin_requested[n]) {
			gpio_free(fpga_pins[n].pin);
			fpga_pin_requested[n] = 0;
		}
	}

	fpga_open_count--;

	mutex_unlock(&fpga_mutex);

	return r;
}

static const struct file_operations fpga_fileops = {
	.owner 		= THIS_MODULE,
	.open 		= fpga_open,
	.release 	= fpga_release,
	.write 		= fpga_write,
	.llseek 	= no_llseek,
};

static int __init fpga_init(void)
{
	int r;

	fpga_mdev = kzalloc(sizeof(*fpga_mdev), GFP_KERNEL);
	if (!fpga_mdev) {
		pr_err(DRIVER_NAME ": misc device allocation failed\n");
		return -ENOMEM;
	}

	fpga_mdev->minor = MISC_DYNAMIC_MINOR;
	fpga_mdev->name = "fpga";
	fpga_mdev->fops = &fpga_fileops;
	r = misc_register(fpga_mdev);
	if (!r)
		printk(DEVICE_NAME " device registered\n");

	return r;
}

static void __exit fpga_cleanup(void)
{
	misc_deregister(fpga_mdev);
}

module_init(fpga_init);
module_exit(fpga_cleanup);

MODULE_AUTHOR("Christer Weinigel <christer@weinigel.se>");
MODULE_DESCRIPTION("SDS7102 FPGA slave serial configuration driver");
MODULE_LICENSE("GPL v2");
