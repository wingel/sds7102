/* A driver which talks to the FPGA on the SDS7102.  This is
 * actually a bidirectional SPI driver, but it's really stupid.  The
 * chip select is asserted when the device is opened and then the
 * userspace program writes one word with the address and read/write
 * bit.  After that it does a read or a write to read or write data.
 *
 * This should really be replaced by the spi-gpio driver in the Linux
 * kernel, but in that case that driver has to be modified to support
 * bidirectional SPI with a shared GPIO pin for MOSI/MISO.
 *
 * This driver also has the advantage that it only allocates the GPIO
 * pins when the device is open.  This means that both this driver and
 * the FPGA programming driver can be loaded at the same time.
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

#include <asm/io.h>

#include <mach/gpio-samsung.h>
#include <plat/gpio-cfg.h>

#define DRIVER_NAME "regs"
#define DEVICE_NAME "regs"

#define FPGA_PROG_B	S3C2410_GPK(7)
#define FPGA_INIT_B	S3C2410_GPK(13)
#define FPGA_DONE	S3C2410_GPK(5)
#define FPGA_CCLK	S3C2410_GPK(3)
#define FPGA_DIN	S3C2410_GPK(11)

static const struct {
	const char *name;
	unsigned pin;
} regs_pins[] = {
	{ "REGS INIT_B",	 FPGA_INIT_B, },
	{ "REGS CCLK",	 FPGA_CCLK,   },
	{ "REGS DIN",	 FPGA_DIN,    },
};

static struct miscdevice *regs_mdev;
static DEFINE_MUTEX(regs_mutex);
static unsigned regs_open_count;
static char regs_pin_requested[ARRAY_SIZE(regs_pins)];

/* FROBNICATE v. To manipulate or adjust, to tweak.
 *
 * Derived from FROBNITZ (q.v.). Usually abbreviated to FROB. Thus one
 * has the saying "to frob a frob". See TWEAK and TWIDDLE.
 *
 * Usage: FROB, TWIDDLE, and TWEAK sometimes connote points along a
 * continuum. FROB connotes aimless manipulation; TWIDDLE connotes
 * gross manipulation, often a coarse search for a proper setting;
 * TWEAK connotes fine-tuning. If someone is turning a knob on an
 * oscilloscope, then if he's carefully adjusting it he is probably
 * tweaking it; if he is just turning it but looking at the screen he
 * is probably twiddling it; but if he's just doing it because turning
 * a knob is fun, he's frobbing it. */

#define FROB 1

#if FROB
#define FROB_COUNT 16
#define FROB_OFFSET 64
#define FROB_STRIDE (4 + 1024 + 32 * 1024)
// #define FROB_STRIDE 4
#define FROB_ADDR(i) (FROB_OFFSET + (i) * FROB_STRIDE)

static uint32_t frob_data[FROB_COUNT];

static const uint32_t ddr_addr = 0x38000000;
static char *ddr_mem;

/* Try to generate test patterns on the SoC bus by writing and reading
 * some address that go to the FPGA.  */
static void soc_frob(void)
{
	local_irq_disable();

	if (1) {
		int i;
		for (i = 0; i < 32; i++)
			writel((1<<i), ddr_mem + i * 4);
	}

	if (1)
	       udelay(1);

	if (1) {
		int i;
		for (i = 0; i < FROB_COUNT; i++)
			frob_data[i] = readl(ddr_mem + FROB_ADDR(i));
	}

	local_irq_enable();
}
#endif

static int regs_open(struct inode *inode, struct file *file)
{
	int r = 0;
	unsigned n;

	mutex_lock(&regs_mutex);

	if (regs_open_count) {
		mutex_unlock(&regs_mutex);
		return -EBUSY;
	}
	regs_open_count++;

#if FROB
	ddr_mem = ioremap(ddr_addr, 32 * 1024 * 1024);
#endif

	for (n = 0; n < ARRAY_SIZE(regs_pins); n++) {
		r = gpio_request(regs_pins[n].pin, regs_pins[n].name);
		if (r) {
			if (0)
			pr_warning("%s: failed to allocate gpio %s (%u)\n",
				   __func__,
				   regs_pins[n].name,
				   regs_pins[n].pin);
		}
		else
			regs_pin_requested[n] = 1;
	}

	s3c_gpio_setpull(FPGA_INIT_B, S3C_GPIO_PULL_UP);

	gpio_direction_input(FPGA_INIT_B);
	gpio_direction_output(FPGA_CCLK, 0);
	gpio_direction_output(FPGA_DIN, 0);

	msleep(1);

	gpio_direction_output(FPGA_DIN, 1);

	mutex_unlock(&regs_mutex);
	return 0;
}

static ssize_t regs_write(struct file *file,
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

	mutex_lock(&regs_mutex);
	gpio_direction_output(FPGA_INIT_B, 1);
	p = tmp;
	for (n = 0; n < len; n++) {
		uint8_t b = *p++;

		for (i = 0; i < 8; i++) {
			if (b & 0x80)
				gpio_set_value(FPGA_INIT_B, 1);
			else
				gpio_set_value(FPGA_INIT_B, 0);
			gpio_set_value(FPGA_CCLK, 1);
			// udelay(10);
			gpio_set_value(FPGA_CCLK, 0);
			b <<= 1;
		}
#if FROB
		/* Generate test patterns after every byte that's
		 * written, with a bit of luck the SoC bus tracer will
		 * catch these. */
		soc_frob();
#endif
	}
	mutex_unlock(&regs_mutex);

	kfree(tmp);

	if (!r)
		r = len;

	return r;
}

static ssize_t regs_read(struct file *file,
			     char *buf, size_t len, loff_t *off)
{
	int r = 0;
	unsigned i;
	size_t n;
	uint8_t *tmp;
	uint8_t *p;

	tmp = kmalloc(len, GFP_KERNEL);
	if (!tmp)
		return -ENOMEM;

	mutex_lock(&regs_mutex);
	gpio_direction_input(FPGA_INIT_B);
	p = tmp;
	for (n = 0; n < len; n++) {
		uint8_t b = 0;

		for (i = 0; i < 8; i++) {
			b <<= 1;
			gpio_set_value(FPGA_CCLK, 1);
			// udelay(10);
			if (gpio_get_value(FPGA_INIT_B))
				b |= 1;
			gpio_set_value(FPGA_CCLK, 0);
			// udelay(10);
		}
		*p++ = b;
	}
	mutex_unlock(&regs_mutex);

	if (copy_to_user(buf, tmp, len))
		r = -EFAULT;

	kfree(tmp);

	if (!r)
		r = len;

	return r;
}

static int regs_release(struct inode *inode, struct file *file)
{
	unsigned n;
	int r = 0;

	if (1) {
		int i;
		for (i = 0; i < FROB_COUNT; i++) {
			unsigned v = (((FROB_ADDR(i) >> 1) & 0xffff) |
				      (((FROB_ADDR(i) >> 1) + 1) << 16));
			const char *e = "";

			if (frob_data[i] != v)
				e = " <<<< ERROR";

			printk("0x%08x -> 0x%08x (0x%08x)%s\n",
			       FROB_ADDR(i), frob_data[i], v, e);
		}
	}

	gpio_direction_input(FPGA_INIT_B);
	gpio_direction_input(FPGA_CCLK);
	gpio_direction_input(FPGA_DIN);

	for (n = 0; n < ARRAY_SIZE(regs_pins); n++) {
		if (regs_pin_requested[n]) {
			gpio_free(regs_pins[n].pin);
			regs_pin_requested[n] = 0;
		}
	}

#if FROB
	iounmap(ddr_mem);
#endif

	regs_open_count--;

	return r;
}

static const struct file_operations regs_fileops = {
    .owner = THIS_MODULE,
    .open = regs_open,
    .release = regs_release,
    .read = regs_read,
    .write = regs_write,
    .llseek = no_llseek,
};

static int __init regs_init(void)
{
	int r;

	regs_mdev = kzalloc(sizeof(*regs_mdev), GFP_KERNEL);
	if (!regs_mdev) {
		pr_err("Misc device allocation failed\n");
		return -ENOMEM;
	}

	regs_mdev->minor = MISC_DYNAMIC_MINOR;
	regs_mdev->name = "regs";
	regs_mdev->fops = &regs_fileops;
	r = misc_register(regs_mdev);
	if (!r) {
		printk("regs device registered\n");
	}

	return r;
}

static void __exit regs_cleanup(void)
{
	misc_deregister(regs_mdev);
}

module_init(regs_init);
module_exit(regs_cleanup);

MODULE_AUTHOR("Christer Weinigel <christer@weinigel.se>");
MODULE_DESCRIPTION("FPGA register driver for SDS7102");
MODULE_LICENSE("GPL");
