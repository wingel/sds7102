#ifndef _REG_H
#define _REG_H

#include <stdint.h>

void read_regs(uint32_t addr, uint32_t *buf, unsigned count);
void write_regs(uint32_t addr, const uint32_t *buf, unsigned count);
uint32_t read_reg(uint32_t addr);
void write_reg(uint32_t addr, uint32_t v);

#endif /* _REG_H */
