/*
 * This file contains parts from:
 *
 *  linux/arch/arm/mm/proc-arm926.S: MMU functions for ARM926EJ-S
 *
 *  Copyright (C) 1999-2001 ARM Limited
 *  Copyright (C) 2000 Deep Blue Solutions Ltd.
 *  hacked for non-paged-MM by Hyok S. Choi, 2003.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * These are the low level assembler for performing cache and TLB
 * functions on the arm926.
 *
 *  CONFIG_CPU_ARM926_CPU_IDLE -> nohlt
 */

#include <linux/linkage.h>
#include <linux/init.h>
#include <asm/assembler.h>
#include <asm/hwcap.h>
#include <asm/pgtable-hwdef.h>
#include <asm/pgtable.h>
#include <asm/page.h>
#include <asm/ptrace.h>

#define CACHE_DLINESIZE	32

/*
 *	dma_inv_range(start, end)
 *
 *	Invalidate (discard) the specified virtual address range.
 *	May not write back any entries.  If 'start' or 'end'
 *	are not cache line aligned, those lines must be written
 *	back.
 *
 *	- start	- virtual start address
 *	- end	- virtual end address
 *
 * (same as v4wb)
 */
arm926_dma_inv_range:
#ifndef CONFIG_CPU_DCACHE_WRITETHROUGH
	tst	r0, #CACHE_DLINESIZE - 1
	mcrne	p15, 0, r0, c7, c10, 1		@ clean D entry
	tst	r1, #CACHE_DLINESIZE - 1
	mcrne	p15, 0, r1, c7, c10, 1		@ clean D entry
#endif
	bic	r0, r0, #CACHE_DLINESIZE - 1
1:	mcr	p15, 0, r0, c7, c6, 1		@ invalidate D entry
	add	r0, r0, #CACHE_DLINESIZE
	cmp	r0, r1
	blo	1b
	mcr	p15, 0, r0, c7, c10, 4		@ drain WB
	ret	lr

/*
 *	dma_clean_range(start, end)
 *
 *	Clean the specified virtual address range.
 *
 *	- start	- virtual start address
 *	- end	- virtual end address
 *
 * (same as v4wb)
 */
arm926_dma_clean_range:
#ifndef CONFIG_CPU_DCACHE_WRITETHROUGH
	bic	r0, r0, #CACHE_DLINESIZE - 1
1:	mcr	p15, 0, r0, c7, c10, 1		@ clean D entry
	add	r0, r0, #CACHE_DLINESIZE
	cmp	r0, r1
	blo	1b
#endif
	mcr	p15, 0, r0, c7, c10, 4		@ drain WB
	ret	lr

/*
 *	dma_flush_range(start, end)
 *
 *	Clean and invalidate the specified virtual address range.
 *
 *	- start	- virtual start address
 *	- end	- virtual end address
 */
ENTRY(arm926_dma_flush_range)
	bic	r0, r0, #CACHE_DLINESIZE - 1
1:
#ifndef CONFIG_CPU_DCACHE_WRITETHROUGH
	mcr	p15, 0, r0, c7, c14, 1		@ clean+invalidate D entry
#else
	mcr	p15, 0, r0, c7, c6, 1		@ invalidate D entry
#endif
	add	r0, r0, #CACHE_DLINESIZE
	cmp	r0, r1
	blo	1b
	mcr	p15, 0, r0, c7, c10, 4		@ drain WB
	ret	lr

/*
 *	dma_map_area(start, size, dir)
 *	- start	- kernel virtual start address
 *	- size	- size of region
 *	- dir	- DMA direction
 */
ENTRY(arm926_dma_map_area)
	add	r1, r1, r0
	cmp	r2, #DMA_TO_DEVICE
	beq	arm926_dma_clean_range
	bcs	arm926_dma_inv_range
	b	arm926_dma_flush_range
ENDPROC(arm926_dma_map_area)

