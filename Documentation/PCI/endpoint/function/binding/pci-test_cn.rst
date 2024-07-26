SPDX 许可证标识符: GPL-2.0

==========================
PCI 测试终端功能
==========================

名称：应为 "pci_epf_test" 以便与 pci_epf_test 驱动绑定
可配置字段：

================   ===========================================================
vendorid	   应该是 0x104c
deviceid	   对于 DRA74x 应该是 0xb500，对于 DRA72x 应该是 0xb501
revid		   不关心
progif_code	   不关心
subclass_code	   不关心
baseclass_code	   应该是 0xff
cache_line_size	   不关心
subsys_vendor_id   不关心
subsys_id	   不关心
interrupt_pin	   应该是 1 - INTA、2 - INTB、3 - INTC、4 - INTD
msi_interrupts	   应该是 1 到 32，具体取决于要测试的 MSI 中断数量
msix_interrupts	   应该是 1 到 2048，具体取决于要测试的 MSI-X 中断数量
================   ===========================================================
