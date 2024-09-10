SPDX许可证标识符: GPL-2.0

===============
配额子系统
===============

配额子系统允许系统管理员为用户和/或组设置使用的空间和使用的索引节点（索引节点是与每个文件或目录相关联的文件系统结构）的数量限制。对于使用的空间和使用的索引节点数量，实际上有两个限制。第一个称为软限制（softlimit），第二个称为硬限制（hardlimit）。用户永远不能超过任何资源的硬限制（除非他拥有CAP_SYS_RESOURCE权限）。用户被允许超过软限制，但只能在有限的时间内。这段时间被称为“宽限期”或“宽限时间”。当宽限期结束后，用户无法分配更多的空间/索引节点，直到他释放足够的空间/索引节点以低于软限制。
配额限制（以及宽限期的数量）独立地为每个文件系统设定。
关于配额设计的更多详细信息，请参阅quota-tools包中的文档（https://sourceforge.net/projects/linuxquota）。

配额Netlink接口
=======================
当用户超过软限制、用尽宽限期或达到硬限制时，传统的做法是配额子系统向导致超出配额的过程的控制终端打印一条消息。这种方法的缺点在于，当用户使用图形桌面时，通常看不到这条消息。
因此，设计了配额Netlink接口来将上述事件的信息传递到用户空间。在那里，这些信息可以被应用程序捕获并相应处理。
该接口使用通用Netlink框架（有关此层的更多信息，请参见https://lwn.net/Articles/208755/ 和 http://www.infradead.org/~tgr/libnl/）。配额通用Netlink接口的名称为“VFS_DQUOT”。下面定义的常量位于<linux/quota.h>中。由于配额Netlink协议不支持命名空间，因此只在初始网络命名空间中发送配额Netlink消息。
目前，该接口仅支持一种消息类型：QUOTA_NL_C_WARNING。
此命令用于发送有关上述事件的通知。每条消息有六个属性（括号内为参数类型）：

        QUOTA_NL_A_QTYPE (u32)
        - 超出的配额类型（USRQUOTA 或 GRPQUOTA 中的一个）
        QUOTA_NL_A_EXCESS_ID (u64)
        - 超出限制的用户的UID/组的GID（取决于配额类型）
QUOTA_NL_A_CAUSED_ID (u64)
        - 导致事件发生的用户的UID
        QUOTA_NL_A_WARNING (u32)
        - 超出哪种类型的限制：
        
            QUOTA_NL_IHARDWARN
                索引节点硬限制
            QUOTA_NL_ISOFTLONGWARN
                超过索引节点软限制的时间长于给定的宽限期
            QUOTA_NL_ISOFTWARN
                索引节点软限制
            QUOTA_NL_BHARDWARN
                空间（块）硬限制
            QUOTA_NL_BSOFTLONGWARN
                超过空间（块）软限制的时间长于给定的宽限期
            QUOTA_NL_BSOFTWARN
                空间（块）软限制

        - 还定义了四种警告用于当用户停止超出某些限制的情况：

            QUOTA_NL_IHARDBELOW
                索引节点硬限制
            QUOTA_NL_ISOFTBELOW
                索引节点软限制
            QUOTA_NL_BHARDBELOW
                空间（块）硬限制
            QUOTA_NL_BSOFTBELOW
                空间（块）软限制

        QUOTA_NL_A_DEV_MAJOR (u32)
        - 受影响文件系统的设备主号
        QUOTA_NL_A_DEV_MINOR (u32)
        - 受影响文件系统的设备次号
