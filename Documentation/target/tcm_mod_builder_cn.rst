=========================================
TCM v4 织网模块脚本生成器
=========================================

大家好，

本文档旨在作为使用 tcm_mod_builder.py 脚本生成全新的功能性的 TCM v4 织网 .ko 模块的迷你指南，一旦构建完成，即可立即加载以开始访问新的 TCM/ConfigFS 织网框架，只需使用以下命令：

```
modprobe $TCM_NEW_MOD
mkdir -p /sys/kernel/config/target/$TCM_NEW_MOD
```

此脚本将创建一个新的 drivers/target/$TCM_NEW_MOD/ 目录，并执行以下操作：

1. 为 drivers/target/target_core_fabric_configs.c 中的逻辑生成新的 API 调用函数 make_tpg()、drop_tpg()、make_wwn() 和 drop_wwn()。这些函数将被创建到 $TCM_NEW_MOD/$TCM_NEW_MOD_configfs.c 文件中。
2. 使用骨架结构体 target_core_fabric_ops API 模板生成加载和卸载 LKMs 和 TCM/ConfigFS 织网模块的基本基础设施。
3. 根据用户定义的新织网模块的 T10 Proto_Ident 自动生成与 TransportID、Initiator 和 Target WWPN 相关的 SPC-3 持久性预留处理程序，这些处理程序将自动生成在 $TCM_NEW_MOD/$TCM_NEW_MOD_fabric.c 文件中，使用 drivers/target/target_core_fabric_lib.c 中的逻辑。
4. 在 $TCM_NEW_MOD/$TCM_NEW_MOD_fabric.c 文件中生成所有其他数据 I/O 路径和织网相关属性逻辑的 NOP API 调用。

tcm_mod_builder.py 依赖于必需的参数 '-p $PROTO_IDENT' 和 '-m $FABRIC_MOD_name'，实际运行脚本看起来像这样：

```
target:/mnt/sdb/lio-core-2.6.git/Documentation/target# python tcm_mod_builder.py -p iSCSI -m tcm_nab5000
tcm_dir: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../
Set fabric_mod_name: tcm_nab5000
Set fabric_mod_dir: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000
Using proto_ident: iSCSI
Creating fabric_mod_dir: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000
Writing file: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000/tcm_nab5000_base.h
Using tcm_mod_scan_fabric_ops: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../include/target/target_core_fabric_ops.h
Writing file: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000/tcm_nab5000_fabric.c
Writing file: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000/tcm_nab5000_fabric.h
Writing file: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000/tcm_nab5000_configfs.c
Writing file: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000/Kbuild
Writing file: /mnt/sdb/lio-core-2.6.git/Documentation/target/../../drivers/target/tcm_nab5000/Kconfig
Would you like to add tcm_nab5000 to drivers/target/Kbuild..? [yes,no]: yes
Would you like to add tcm_nab5000 to drivers/target/Kconfig..? [yes,no]: yes
```

在 tcm_mod_builder.py 执行结束时，脚本会提示添加以下行到 drivers/target/Kbuild 文件中：

```
obj-$(CONFIG_TCM_NAB5000)       += tcm_nab5000/
```

同样地，在 drivers/target/Kconfig 文件中也需要添加：

```
source "drivers/target/tcm_nab5000/Kconfig"
```

#) 运行 'make menuconfig' 并选择新的 CONFIG_TCM_NAB5000 项：

```
<M> TCM_NAB5000 织网模块
```

#) 使用 'make modules' 构建，完成后你将得到如下文件：

```
target:/mnt/sdb/lio-core-2.6.git# ls -la drivers/target/tcm_nab5000/
total 1348
drwxr-xr-x 2 root root   4096 2010-10-05 03:23
drwxr-xr-x 9 root root   4096 2010-10-05 03:22 .
-rw-r--r-- 1 root root    282 2010-10-05 03:22 Kbuild
-rw-r--r-- 1 root root    171 2010-10-05 03:22 Kconfig
-rw-r--r-- 1 root root     49 2010-10-05 03:23 modules.order
-rw-r--r-- 1 root root    738 2010-10-05 03:22 tcm_nab5000_base.h
-rw-r--r-- 1 root root   9096 2010-10-05 03:22 tcm_nab5000_configfs.c
-rw-r--r-- 1 root root 191200 2010-10-05 03:23 tcm_nab5000_configfs.o
-rw-r--r-- 1 root root  40504 2010-10-05 03:23 .tcm_nab5000_configfs.o.cmd
-rw-r--r-- 1 root root   5414 2010-10-05 03:22 tcm_nab5000_fabric.c
-rw-r--r-- 1 root root   2016 2010-10-05 03:22 tcm_nab5000_fabric.h
-rw-r--r-- 1 root root 190932 2010-10-05 03:23 tcm_nab5000_fabric.o
-rw-r--r-- 1 root root  40713 2010-10-05 03:23 .tcm_nab5000_fabric.o.cmd
-rw-r--r-- 1 root root 401861 2010-10-05 03:23 tcm_nab5000.ko
-rw-r--r-- 1 root root    265 2010-10-05 03:23 .tcm_nab5000.ko.cmd
-rw-r--r-- 1 root root    459 2010-10-05 03:23 tcm_nab5000.mod.c
-rw-r--r-- 1 root root  23896 2010-10-05 03:23 tcm_nab5000.mod.o
-rw-r--r-- 1 root root  22655 2010-10-05 03:23 .tcm_nab5000.mod.o.cmd
-rw-r--r-- 1 root root 379022 2010-10-05 03:23 tcm_nab5000.o
-rw-r--r-- 1 root root    211 2010-10-05 03:23 .tcm_nab5000.o.cmd
```

#) 加载新模块，创建一个 lun_0 的 ConfigFS 组，并将新的 TCM Core IBLOCK 后端存储符号链接添加到端口：

```
target:/mnt/sdb/lio-core-2.6.git# insmod drivers/target/tcm_nab5000.ko
target:/mnt/sdb/lio-core-2.6.git# mkdir -p /sys/kernel/config/target/nab5000/iqn.foo/tpgt_1/lun/lun_0
target:/mnt/sdb/lio-core-2.6.git# cd /sys/kernel/config/target/nab5000/iqn.foo/tpgt_1/lun/lun_0/
target:/sys/kernel/config/target/nab5000/iqn.foo/tpgt_1/lun/lun_0# ln -s /sys/kernel/config/target/core/iblock_0/lvm_test0 nab5000_port

target:/sys/kernel/config/target/nab5000/iqn.foo/tpgt_1/lun/lun_0# cd -
target:/mnt/sdb/lio-core-2.6.git# tree /sys/kernel/config/target/nab5000/
/sys/kernel/config/target/nab5000/
|-- discovery_auth
|-- iqn.foo
|   `-- tpgt_1
|       |-- acls
|       |-- attrib
|       |-- lun
|       |   `-- lun_0
|       |       |-- alua_tg_pt_gp
|       |       |-- alua_tg_pt_offline
|       |       |-- alua_tg_pt_status
|       |       |-- alua_tg_pt_write_md
|       |       `-- nab5000_port -> ../../../../../../target/core/iblock_0/lvm_test0
|       |-- np
|       `-- param
`-- version

target:/mnt/sdb/lio-core-2.6.git# lsmod
Module                  Size  Used by
tcm_nab5000             3935  4
iscsi_target_mod      193211  0
target_core_stgt        8090  0
target_core_pscsi      11122  1
target_core_file        9172  2
target_core_iblock      9280  1
target_core_mod       228575  31
tcm_nab5000,iscsi_target_mod,target_core_stgt,target_core_pscsi,target_core_file,target_core_iblock
libfc                  73681  0
scsi_debug             56265  0
scsi_tgt                8666  1 target_core_stgt
configfs               20644  2 target_core_mod
```

-----------------------------------------------------------------------

未来待办事项
===============

1. 添加更多的 T10 proto_idents。
2. 让 tcm_mod_dump_fabric_ops() 更智能，并直接从 include/target/target_core_fabric_ops.h:struct target_core_fabric_ops 结构成员生成函数指针定义。

2010年10月5日

Nicholas A. Bellinger <nab@linux-iscsi.org>
