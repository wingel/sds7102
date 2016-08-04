#ifndef _SDS7102_H
#define _SDS7102_H

#define SDS7102_REG_BASE 0x38000000
#define SDS7102_REG_SIZE 4096

/* Frontpanel */

#define FP_NR_KEYS	64

#define FP_REG_BASE	(SDS7102_REG_BASE + 0x400)
#define FP_REG_SIZE	0x20

/* Frontpanel control register */
#define FP_CTRL		0x00
#define FP_INIT		(1<<8)

/* Frontpanel data register */
#define FP_DATA		0x10
#define FP_KEY_SHIFT	0
#define FP_KEY_MASK	0xff
#define FP_PRESSED	(1<<8)
#define FP_ACTIVE	(1<<9)
#define FP_TS_SHIFT	16
#define FP_TS_MASK	0xffff

/* MISC registers */

#define MISC_REG_BASE	(SDS7102_REG_BASE + 0x420)
#define MISC_REG_SIZE	0x10

#define MISC_LED	0x00
#define MISC_LED_GREEN	(1<<0)
#define MISC_LED_WHITE	(1<<1)

/* 4kByte block RAM */
#define BLOCK_RAM_BASE	(SDS7102_REG_BASE + 0x20000)
#define BLOCK_RAM_SIZE  4096

/* Read-only region which returns a predictable pattern based on the
 * address */
#define ALGO_MEM_BASE	(SDS7102_REG_BASE + 0x40000)
#define ALGO_MEM_SIZE	(4<<16)

#endif /* _SDS7102_H */
