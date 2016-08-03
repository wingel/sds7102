/*
 * OWON SDS7102 Front Panel Driver
 *
 * Copyright (C) 2016 Christer Weinigel <christer@weinigel.se>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation version 2.
 */

/* The FPGA actually records timestamps for each transition of a
 * switch.  I was planning to use the timestamps to perform filtering
 * of false transitions.  I ended up doing most of the filtering in
 * the FPGA, it scans the rotary switches more often than it scans the
 * key switches and then stretces the active pulses to hide bounces.
 * This handles most of the false transitions.  I'll probably remove
 * the timestamps from the FPGA later, but they are nice for making
 * pretty plots in gtkwave when trying to figure out what to do about
 * the noise.
 *
 * The rotary switches are still fairly noisy and a few false
 * transitions can come through.  It doesn't matter that much though,
 * it only happens when turning a rotary switch really fast and the
 * false transitions are hidden by all the transitions in the correct
 * direction.
 *
 * I did have some code in the driver to detect false transitions
 * before but the driver seems to behave better if I just ignore the
 * false transitions.
 */

#include <linux/module.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <linux/delay.h>
#include <linux/input-polldev.h>

#include "sds7102.h"
#include "sds7102-keys.h"

#define FP_NAME "sds7102-frontpanel"

#define FP_NR_KEYS	64
#define FP_POLL_INTERVAL 10

/* Frontpanel control register */
#define FP_CTRL		0x400
#define FP_INIT		(1<<8)

/* Frontpanel data register */
#define FP_DATA		0x440
#define FP_KEY_SHIFT	0
#define FP_KEY_MASK	0xff
#define FP_PRESSED	(1<<8)
#define FP_ACTIVE	(1<<9)
#define FP_TS_SHIFT	16
#define FP_TS_MASK	0xffff

/* A simple keymap which maps from scancodes to key codes or the coder
 * for a relative axis. */
struct fp_keymap {
	unsigned flags;
	int code;
	const char *name;
};

/* The flags say if it's a key or a rotary switch and if the rotary
 * switch is stepped or does continuous rotation. */
#define FLAG_BIT 1
#define FLAG_ROT 2
#define FLAG_STEP 4

/* Plain key switches */
#define MAKE_KEY(s) { 0, SDS_KEY_ ## s, #s }

/* Push function of rotary encoders, they are encoded the same as the keys */
#define MAKE_RP(s) { 0, SDS_KEY_ ## s, #s }

/* Small continuous rotary encoders */
#define MAKE_R1(s) { FLAG_ROT | 0, SDS_REL_ ## s, #s }
#define MAKE_R2(s) { FLAG_ROT | 1, SDS_REL_ ## s, #s }

/* Large stepped rotary encoders */
#define MAKE_S1(s) { FLAG_ROT | FLAG_STEP | 0, SDS_REL_ ## s, #s }
#define MAKE_S2(s) { FLAG_ROT | FLAG_STEP | 1, SDS_REL_ ## s, #s }

static const struct fp_keymap fp_keymap[FP_NR_KEYS] = {
	[ 0] = MAKE_R1(TRIG),		/* Trig level rotation 1 */
	[ 1] = MAKE_R1(HORIZ_POS),	/* Horizontal position rotation 1 */
	[ 2] = MAKE_R1(CH2_POS), 	/* Ch2 vertical position rotation 1 */
	[ 3] = MAKE_R1(CH1_POS), 	/* Ch1 vertical position rotation 1 */
	[ 4] = MAKE_S1(CH2_SCALE), 	/* Ch1 Volts/Div rotation 1 */
	[ 5] = MAKE_R1(MULTI),		/* Multipurpose rotation 1 */
	[ 6] = MAKE_S1(HORIZ_SCALE),	/* Sec/Div rotation 1 */
	[ 7] = MAKE_S1(CH1_SCALE),	/* Ch1 Volts/Div rotation 1 */
	[ 8] = MAKE_R2(TRIG),		/* Trig level rotation 2 */
	[ 9] = MAKE_R2(HORIZ_POS),	/* Horizontal position rotation 2 */
	[10] = MAKE_R2(CH2_POS), 	/* Ch2 vertical position rotation 2 */
	[11] = MAKE_R2(CH1_POS), 	/* Ch1 vertical position rotation 2 */
	[12] = MAKE_S2(CH2_SCALE), 	/* Ch1 Volts/Div rotation 2 */
	[13] = MAKE_R2(MULTI),		/* Multipurpose rotation 2 */
	[14] = MAKE_S2(HORIZ_SCALE),	/* Sec/Div rotation 2 */
	[15] = MAKE_S2(CH1_SCALE),	/* Ch1 Volts/Div rotation 2 */
	[16] = MAKE_RP(TRIG),		/* Trig level press */
	[17] = MAKE_RP(HORIZ_POS),	/* Horizontal position press */
	[18] = MAKE_RP(CH2_POS), 	/* Ch2 vertical position press */
	[19] = MAKE_RP(CH1_POS), 	/* Ch1 vertical position press */
	[20] = MAKE_RP(CH2_SCALE), 	/* Ch1 Volts/Div press */
	[21] = MAKE_RP(MULTI),		/* Multipurpose press */
	[22] = MAKE_RP(HORIZ_SCALE),	/* Sec/Div press */
	[23] = MAKE_RP(CH1_SCALE),	/* Ch1 Volts/Div press */
	[24] = MAKE_KEY(TRIG_50),	/* Trigger 50% */
	[25] = MAKE_KEY(MATH_MENU),	/* Math menu */
	[26] = MAKE_KEY(COPY),		/* Copy */
	[29] = MAKE_KEY(H1),		/* H1 */
	[31] = MAKE_KEY(F5),		/* F5 */
	[32] = MAKE_KEY(SINGLE),	/* Single */
	[33] = MAKE_KEY(AUTOSCALE),	/* Autoscale */
	[34] = MAKE_KEY(CURSOR),	/* Cursor */
	[35] = MAKE_KEY(UTILITY),	/* Utility */
	[36] = MAKE_KEY(F2),		/* F2 */
	[37] = MAKE_KEY(H5),		/* H5 */
	[39] = MAKE_KEY(F1),		/* F1 */
	[40] = MAKE_KEY(TRIG_MENU),	/* Trigger Menu */
	[41] = MAKE_KEY(HELP),		/* Help */
	[42] = MAKE_KEY(DISPLAY),	/* Display */
	[43] = MAKE_KEY(SAVE),		/* Save */
	[45] = MAKE_KEY(H4),		/* H4 */
	[47] = MAKE_KEY(F3),		/* F3 */
	[48] = MAKE_KEY(RUN_STOP),	/* Run/Stop */
	[49] = MAKE_KEY(AUTOSET),	/* Autoset */
	[50] = MAKE_KEY(ACQUIRE),	/* Acquire */
	[51] = MAKE_KEY(MEASURE),	/* Measure */
	[53] = MAKE_KEY(H3),		/* H3 */
	[55] = MAKE_KEY(F4),		/* F4 */
	[56] = MAKE_KEY(TRIG_FORCE),	/* Trigger Force */
	[57] = MAKE_KEY(HORIZ_MENU),	/* Horiz Menu */
	[58] = MAKE_KEY(CH2_MENU),	/* Ch2 Menu */
	[59] = MAKE_KEY(CH1_MENU),	/* Ch1 Menu */
	[61] = MAKE_KEY(H2),		/* H2 */
	[63] = MAKE_KEY(MENU_OFF),	/* Menu Off */
};

/* State machine for small rotary encoders.  Report all valid transitions. */
static const int8_t rot_state_machine[4][4] = {
	{  0,  1, -1,  0 },
	{ -1,  0,  0,  1 },
	{  1,  0,  0, -1 },
	{  0, -1,  1,  0 },
};

/* State machine for stepped rotary encoders.  They generate four transitions
 * per step, only report a change for one of the four transitions. */
static const int8_t step_state_machine[4][4] = {
	{  0,  1, -1,  0 },
	{  0,  0,  0,  0 },
	{  0,  0,  0,  0 },
	{  0,  0,  0,  0 },
};

struct fp_dev {
	void __iomem *reg;

	struct input_polled_dev *poll_dev;

	/* Timestamps */
	uint16_t short_ts;
	uint32_t long_ts;

	/* Information for the relative axes */
	uint8_t rel_state[REL_MAX];
	int rel_acc[REL_MAX];
};

static void fp_update(struct fp_dev *fp_dev, unsigned scancode, bool pressed)
{
	struct input_dev *input = fp_dev->poll_dev->input;
	const struct fp_keymap *p;

	p = &fp_keymap[scancode];
	if (p->flags & FLAG_ROT) {
		unsigned bit = p->flags & FLAG_BIT;
		unsigned v0 = fp_dev->rel_state[p->code];
		unsigned v = v0;
		int dir;

		if (pressed)
			v &= ~(1 << bit);
		else
			v |= (1 << bit);

		if (p->flags & FLAG_STEP)
			dir = step_state_machine[v0][v];
		else
			dir = rot_state_machine[v0][v];

		fp_dev->rel_acc[p->code] += dir;

		fp_dev->rel_state[p->code] = v;
	} else {
		input_report_key(input, p->code, pressed);
		input_sync(input);
	}
}

static void fp_poll(struct input_polled_dev *dev)
{
	struct fp_dev *fp_dev = dev->private;
	struct input_dev *input = dev->input;
	uint32_t v;
	unsigned i;
	unsigned scancode;
	bool pressed;
	bool active;
	uint16_t ts;

	/* Limit the number of times we read the data register, just
	 * in case something goes wrong. */
	for (i = 0; i < 100; i++) {
		v = readl(fp_dev->reg + FP_DATA);

		scancode = v & FP_KEY_MASK;
		pressed = v & FP_PRESSED;
		active = v & FP_ACTIVE;
		ts = (v >> FP_TS_SHIFT) & FP_TS_MASK;

		fp_dev->long_ts += (uint16_t)(ts - fp_dev->short_ts);
		fp_dev->short_ts = ts;

		if (!active)
			break;

		if (scancode >= FP_NR_KEYS) {
			printk(KERN_DEBUG FP_NAME ": invalid scancode %u\n",
			       scancode);
			continue;
		}

		fp_update(fp_dev, scancode, pressed);
	}

	for (i = 0; i < REL_MAX; i++) {
		if (fp_dev->rel_acc[i]) {
			input_report_rel(input, i, fp_dev->rel_acc[i]);
			input_sync(input);
			fp_dev->rel_acc[i] = 0;
		}
	}
}

static struct fp_dev *fp_dev;

static int __init sds7102_frontpanel_init(void)
{
	struct input_dev *input;
	int r = -ENOMEM;
	unsigned i;

	fp_dev = kzalloc(sizeof(struct fp_dev), GFP_KERNEL);
	if (!fp_dev)
		goto out;

	fp_dev->reg = ioremap(SDS7102_REG_BASE, SDS7102_REG_SIZE);
	if (!fp_dev->reg)
		goto out;

	fp_dev->poll_dev = input_allocate_polled_device();
	if (!fp_dev->poll_dev)
		goto out;

	fp_dev->poll_dev->private = fp_dev;
	fp_dev->poll_dev->poll = fp_poll;
	fp_dev->poll_dev->poll_interval = FP_POLL_INTERVAL;

	input = fp_dev->poll_dev->input;
	input->name = "SDS7102 Front Panel";
	input->id.bustype = BUS_HOST;

	__set_bit(EV_KEY, input->evbit);
	__set_bit(EV_REL, input->evbit);

	for (i = 0; i < ARRAY_SIZE(fp_keymap); i++) {
		const struct fp_keymap *p = &fp_keymap[i];
		if (p->flags & FLAG_ROT)
			__set_bit(p->code, input->relbit);
		else
			__set_bit(p->code, input->keybit);
	}

	// input_set_capability(input, EV_MSC, MSC_SCAN);

	writel(FP_INIT, fp_dev->reg + FP_CTRL);
	writel(0, fp_dev->reg + FP_CTRL);

	r = input_register_polled_device(fp_dev->poll_dev);
	if (r)
		goto out;

	return 0;

out:
	if (fp_dev)
	{
		if (fp_dev->poll_dev)
			input_free_polled_device(fp_dev->poll_dev);
		if (fp_dev->reg)
			iounmap(fp_dev->reg);
		kfree(fp_dev);
	}

	return r;
}

static void __exit sds7102_frontpanel_cleanup(void)
{
	input_unregister_polled_device(fp_dev->poll_dev);
	input_free_polled_device(fp_dev->poll_dev);
	iounmap(fp_dev->reg);
	kfree(fp_dev);
}

module_init(sds7102_frontpanel_init);
module_exit(sds7102_frontpanel_cleanup);

MODULE_AUTHOR("Christer Weinigel <christer@weinigel.se>");
MODULE_DESCRIPTION("OWON SDS7102 Front Panel Driver");
MODULE_LICENSE("GPL v2");
