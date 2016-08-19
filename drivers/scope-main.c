/* A driver for the scope functionality of the SDS7102 scope.
 *
 * Copyright (C) 2016 Christer Weinigel <christer@weinigel.se>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation version 2.
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
#include <linux/dma-mapping.h>

#include <asm/cacheflush.h>

#include <mach/gpio-samsung.h>
#include <plat/gpio-cfg.h>

#include <asm/glue-cache.h>

#define dma_map_area		__glue(_CACHE,_dma_map_area)
#define dma_unmap_area 		__glue(_CACHE,_dma_unmap_area)
extern void dma_map_area(const void *, size_t, int);
extern void dma_unmap_area(const void *, size_t, int);

#include "sds7102.h"
#include "scope.h"

#define DRIVER_NAME "sds7102-scope"
#define DEVICE_NAME "scope"

static DEFINE_MUTEX(scope_mutex);
static unsigned scope_open_count;

#define TIMEOUT 10000

struct scope_state
{
	struct miscdevice *mdev;
	u32 __iomem *regs;
	u32 __iomem *render_buf;
};

static struct scope_state *static_scope;

static int scope_open(struct inode *inode, struct file *file)
{
	mutex_lock(&scope_mutex);

	if (scope_open_count) {
		mutex_unlock(&scope_mutex);
		return -EBUSY;
	}
	scope_open_count++;

	mutex_unlock(&scope_mutex);

	return 0;
}

static int scope_release(struct inode *inode, struct file *file)
{
	mutex_lock(&scope_mutex);

	scope_open_count--;

	mutex_unlock(&scope_mutex);

	return 0;
}

static int scope_render_column(struct scope_state *scope,
			       uint32_t *buf,
			       unsigned addr, unsigned count)
{
	u32 v;
	unsigned r;
	unsigned i;

	iowrite32(FP_REG_RENDER_CLEAR, scope->regs + FP_REG_RENDER);
	mb();

	for (r = TIMEOUT; r > 0; r--) {
		v = ioread32(scope->regs + FP_REG_RENDER);
		if (!(v & FP_REG_RENDER_CLEAR))
			break;
	}
	if (!r) {
		pr_err(DRIVER_NAME ": render clear timeout (0x%x)\n", v);
		return -ETIMEDOUT;
	}
	// printk("clear %u\n", TIMEOUT - r);

	iowrite32(addr, scope->regs + FP_REG_DDR_RD_ADDR);
	mb();
	iowrite32(count, scope->regs + FP_REG_DDR_RD_COUNT);
	mb();

	/* Invalidate cache */
	dma_map_area(scope->render_buf, RENDER_BUF_SIZE, DMA_FROM_DEVICE);

	for (r = TIMEOUT; r > 0; r--) {
		v = ioread32(scope->regs + FP_REG_RENDER);
		if ((v & FP_REG_RENDER_IDLE))
			break;
	}
	if (!r) {
		pr_err(DRIVER_NAME ": render timeout (0x%x)\n", v);
		return -ETIMEDOUT;
	}
	// printk("render %u\n", TIMEOUT - r);

	/* Read samples */
	for (i = 0; i < 256; i++)
		buf[i] = ioread32(scope->render_buf + i);

	return 0;
}

static int scope_render(struct scope_render __user *arg)
{
	struct scope_state *scope = static_scope;
	struct scope_render render;
	void *buf;
	uint32_t *p;
	unsigned size;
	int r;

	if (copy_from_user(&render, arg, sizeof(render)))
		return -EFAULT;

	if (!render.count)
		return 0;

	if (render.count > 1024)
		return -EINVAL;

	size = render.count * 256 * sizeof(u32);

	buf = kmalloc(size, GFP_KERNEL);
	if (!buf)
		return -ENOMEM;

	r = 0;

	p = buf;
	while (render.count--) {
		r = scope_render_column(scope, p,
					render.addr, render.scale + 1);
		if (r)
			break;

		p += 256;
		render.addr += render.scale;
	}

	if (!r) {
		if (copy_to_user(render.buf, buf, size))
			r = -EFAULT;
	}

	kfree(buf);

	return r;
}

static long scope_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	switch (cmd) {
	case IOCTL_SCOPE_RENDER:
		return scope_render((void __user *)arg);

	default:
		return -ENOTTY;
	}
}

static const struct file_operations scope_fileops = {
	.owner		= THIS_MODULE,
	.open		= scope_open,
	.release	= scope_release,
	.unlocked_ioctl	= scope_ioctl,
	.llseek		= no_llseek,
};

static int __init scope_init(void)
{
	struct scope_state *scope;
	int r;

	scope = kzalloc(sizeof(*scope), GFP_KERNEL);
	if (!scope) {
		pr_err(DRIVER_NAME ": scope memory allocation failed\n");
		r = -ENOMEM;
		goto err;
	}

	scope->mdev = kzalloc(sizeof(*scope->mdev), GFP_KERNEL);
	if (!scope->mdev) {
		pr_err(DRIVER_NAME ": misc device allocation failed\n");
		r = -ENOMEM;
		goto err;
	}

	scope->regs = ioremap(SDS7102_REG_BASE, SDS7102_REG_SIZE);
	if (!scope->regs) {
		pr_err(DRIVER_NAME ": regs ioremap failed\n");
		r = -ENOMEM;
	}

	scope->render_buf = ioremap_cache(RENDER_BUF_BASE, RENDER_BUF_SIZE);
	if (!scope->render_buf) {
		pr_err(DRIVER_NAME ": render_buf ioremap failed\n");
		r = -ENOMEM;
	}

	static_scope = scope;

	scope->mdev->minor = MISC_DYNAMIC_MINOR;
	scope->mdev->name = "scope";
	scope->mdev->fops = &scope_fileops;
	r = misc_register(scope->mdev);
	if (r) {
		pr_err(DRIVER_NAME ": misc_register failed\n");
		goto err;
	}

	pr_info(DRIVER_NAME ": registered\n");

	return 0;

err:
	if (scope) {
		if (scope->render_buf)
			iounmap(scope->render_buf);
		if (scope->regs)
			iounmap(scope->regs);
		if (scope->mdev)
			kfree(scope->mdev);
		kfree(scope);
	}

	return r;
}

static void __exit scope_cleanup(void)
{
	struct scope_state *scope = static_scope;

	misc_deregister(scope->mdev);
	iounmap(scope->render_buf);
	iounmap(scope->regs);
}

module_init(scope_init);
module_exit(scope_cleanup);

MODULE_AUTHOR("Christer Weinigel <christer@weinigel.se>");
MODULE_DESCRIPTION("SDS7102 scope driver");
MODULE_LICENSE("GPL v2");
