下面是内核32位引导协议中`struct boot_params`结构体的附加字段，这些字段应由引导加载程序或内核的16位实模式设置代码填充。主要引用和设置位于：

  `arch/x86/include/uapi/asm/bootparam.h`

====== ===== ========================= ==================================================
偏移量/大小 协议 名称                    含义
====== ===== ========================= ==================================================
000/040 ALL screen_info               文本模式或帧缓冲信息（`struct screen_info`）
040/014 ALL apm_bios_info            APM BIOS信息（`struct apm_bios_info`）
058/008 ALL tboot_addr               tboot共享页的物理地址
060/010 ALL ist_info                 Intel SpeedStep (IST) BIOS支持信息（`struct ist_info`）
070/008 ALL acpi_rsdp_addr           ACPI RSDP表的物理地址
080/010 ALL hd0_info                 hd0磁盘参数，已废弃！
090/010 ALL hd1_info                 hd1磁盘参数，已废弃！
0A0/010 ALL sys_desc_table           系统描述表（`struct sys_desc_table`），已废弃！
0B0/010 ALL olpc_ofw_header          OLPC的OpenFirmware CIF及相关信息
0C0/004 ALL ext_ramdisk_image        ramdisk_image高32位
0C4/004 ALL ext_ramdisk_size         ramdisk_size高32位
0C8/004 ALL ext_cmd_line_ptr         cmd_line_ptr高32位
13C/004 ALL cc_blob_address          Confidential Computing blob的物理地址
140/080 ALL edid_info                视频模式设置（`struct edid_info`）
1C0/020 ALL efi_info                 EFI 32信息（`struct efi_info`）
1E0/004 ALL alt_mem_k                替代内存检查，以KB为单位
1E4/004 ALL scratch                  内核设置代码的临时字段
1E8/001 ALL e820_entries             e820_table（下面）中的条目数量
1E9/001 ALL eddbuf_entries           eddbuf（下面）中的条目数量
1EA/001 ALL edd_mbr_sig_buf_entries  edd_mbr_sig_buffer中的条目数量（下面）
1EB/001 ALL kbd_status               Numlock被启用
1EC/001 ALL secure_boot              固件中启用了安全启动
1EF/001 ALL sentinel                 用于检测有问题的引导加载程序
290/040 ALL edd_mbr_sig_buffer       EDD MBR签名
2D0/A00 ALL e820_table               E820内存映射表（`struct e820_entry`数组）
D00/1EC ALL eddbuf                   EDD数据（`struct edd_info`数组）
====== ===== ========================= ==================================================
