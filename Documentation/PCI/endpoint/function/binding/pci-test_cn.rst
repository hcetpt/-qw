SPDX 许可证标识符: GPL-2.0

==========================
PCI 测试端点功能
==========================

名称: 应为 "pci_epf_test" 以绑定到 pci_epf_test 驱动
可配置字段：

================   ===========================================================
vendorid           应为 0x104c
deviceid           对于 DRA74x 应为 0xb500，对于 DRA72x 应为 0xb501
revid              不关心
progif_code        不关心
subclass_code      不关心
baseclass_code     应为 0xff
cache_line_size    不关心
subsys_vendor_id   不关心
subsys_id          不关心
interrupt_pin      应为 1 - INTA, 2 - INTB, 3 - INTC, 4 - INTD
msi_interrupts     应为 1 到 32，取决于要测试的 MSI 中断数量
msix_interrupts    应为 1 到 2048，取决于要测试的 MSI-X 中断数量
================   ===========================================================
