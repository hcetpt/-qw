将启动参数传递给内核
=====================

启动参数在内存中表示为TLV列表。请参阅
arch/xtensa/include/asm/bootparam.h以获取bp_tag结构和
标签值常量的定义。列表中的第一个条目必须具有类型BP_TAG_FIRST，最后一个条目必须具有类型BP_TAG_LAST。列表中第一条目的地址通过寄存器a2传递给内核。地址的类型取决于MMU类型：

- 对于没有MMU、具有区域保护或具有MPU的配置，
  地址必须是物理地址。
- 对于具有区域转换MMU或具有MMUv3且CONFIG_MMU=n的配置，
  地址必须是在当前映射中有效的地址。内核不会自行更改映射。
- 对于具有MMUv2的配置，
  地址必须是默认虚拟映射中的虚拟地址（0xd0000000..0xffffffff）。
- 对于具有MMUv3且CONFIG_MMU=y的配置，
  地址可以是虚拟地址也可以是物理地址。无论哪种情况，它都必须位于默认虚拟映射范围内。如果它位于默认KSEG映射所覆盖的物理地址范围内（XCHAL_KSEG_PADDR至XCHAL_KSEG_PADDR + XCHAL_KSEG_SIZE），则认为它是物理地址；否则，认为它是虚拟地址。
