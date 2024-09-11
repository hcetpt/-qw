.. _magicnumbers:

Linux 魔数
===================

此文件是正在使用的魔数的注册表。当你向一个结构体中添加一个魔数时，你也应该将它添加到此文件中，因为最好让各种结构体所用的魔数是唯一的。
使用魔数来保护内核数据结构是一个**非常好的主意**。这允许你在运行时检查（a）一个结构体是否被篡改了，或（b）你是否传递了一个错误的结构体给某个函数。特别是在通过 `void *` 指针传递结构体指针时，这一点特别有用。例如，tty 代码经常这样做以在驱动程序和线路纪律特定的结构体之间传递数据。
使用魔数的方法是在结构体的开头声明它们，如下所示：

```c
    struct tty_ldisc {
        int magic;
        ...
    };
```

请在将来对内核进行增强时遵循这一规范！这已经为我节省了无数的调试时间，尤其是在数组溢出导致后续结构体被覆盖的情况下。通过遵循这一规范，这些情况可以被迅速且安全地检测出来。

变更日志：

* Theodore Ts'o
  1994年3月31日

  魔数表已更新至 Linux 2.1.55。
  
* Michael Chastain
  <mailto:mec@shout.net>
  1997年9月22日

  现在应已更新至 Linux 2.1.112。因为我们正处于功能冻结期，在 2.2.x 版本之前不太可能有变动。条目按数字字段排序。

* Krzysztof G. Baranowski
  <mailto:kgb@knm.org.pl>
  1998年7月29日

  更新魔数表至 Linux 2.5.45。刚好在功能冻结期之后，但在 2.6.x 版本之前仍有可能会有新的魔数进入内核。

* Petr Baudis
  <pasky@ucw.cz>
  2002年11月3日

  更新魔数表至 Linux 2.5.74。

* Fabian Frederick
  <ffrederick@users.sourceforge.net>
  2003年7月9日

  更新魔数表至 Linux 2.5.74。

===================== ================ ======================== ==========================================
魔数名称              编号              结构体                  文件
===================== ================ ======================== ==========================================
PG_MAGIC              'P'              pg_{read,write}_hdr      ``include/linux/pg.h``
APM_BIOS_MAGIC        0x4101           apm_user                 ``arch/x86/kernel/apm_32.c``
FASYNC_MAGIC          0x4601           fasync_struct            ``include/linux/fs.h``
SLIP_MAGIC            0x5302           slip                     ``drivers/net/slip.h``
BAYCOM_MAGIC          0x19730510       baycom_state             ``drivers/net/baycom_epp.c``
HDLCDRV_MAGIC         0x5ac6e778       hdlcdrv_state            ``include/linux/hdlcdrv.h``
KV_MAGIC              0x5f4b565f       kernel_vars_s            ``arch/mips/include/asm/sn/klkernvars.h``
CODA_MAGIC            0xC0DAC0DA       coda_file_info           ``fs/coda/coda_fs_i.h``
YAM_MAGIC             0xF10A7654       yam_port                 ``drivers/net/hamradio/yam.c``
CCB_MAGIC             0xf2691ad2       ccb                      ``drivers/scsi/ncr53c8xx.c``
QUEUE_MAGIC_FREE      0xf7e1c9a3       queue_entry              ``drivers/scsi/arm/queue.c``
QUEUE_MAGIC_USED      0xf7e1cc33       queue_entry              ``drivers/scsi/arm/queue.c``
NMI_MAGIC             0x48414d4d455201 nmi_s                    ``arch/mips/include/asm/sn/nmi.h``
===================== ================ ======================== ==========================================
