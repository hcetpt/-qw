==========================
ELF 注释 PowerPC 命名空间
==========================

内核二进制文件中的 ELF 注释的 PowerPC 命名空间用于存储
可以被引导加载程序或用户空间利用的能力和信息。
类型与描述符
---------------------

在 "PowerPC" 命名空间中使用的类型定义在 [#f1]_ 中：
1) PPC_ELFNOTE_CAPABILITIES

定义内核支持或需要的能力。此类型使用位图作为“描述符”字段。每个比特位的含义如下：

- Ultravisor 能力位（仅适用于 PowerNV）
.. code-block:: c

	#define PPCCAP_ULTRAVISOR_BIT (1 << 0)

表示 powerpc 内核二进制文件知道如何在一个启用了 Ultravisor 的系统中运行。
在一个启用了 Ultravisor 的系统中，某些机器资源现在由 Ultravisor 控制。
如果内核不具备 Ultravisor 能力，但在带有 Ultravisor 的机器上运行，内核可能会尝试访问 Ultravisor 资源时崩溃。
例如，在早期启动阶段设置分区表入口 0 时可能会崩溃。
在一个启用了 Ultravisor 的系统中，如果不存在 PowerPC Ultravisor 能力或 Ultravisor 能力位未设置，引导加载程序可以警告用户或阻止内核运行。

参考资料
----------

.. [#f1] arch/powerpc/include/asm/elfnote.h
