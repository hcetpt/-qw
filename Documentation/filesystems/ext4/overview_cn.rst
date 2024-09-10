SPDX 许可证标识符: GPL-2.0

高级设计
========

ext4 文件系统被划分为一系列的块组。为了减少由于碎片导致的性能问题，块分配器非常努力地将每个文件的块保持在同一个组内，从而减少寻道时间。块组的大小由 ``sb.s_blocks_per_group`` 指定，也可以通过 8 * ``block_size_in_bytes`` 计算得出。默认的块大小为 4KiB，因此每个组包含 32,768 个块，长度为 128MiB。块组的数量是设备大小除以块组的大小。ext4 中的所有字段都以小端字节序写入磁盘。但是，jbd2（日志）中的所有字段都以大端字节序写入磁盘。

.. include:: blocks.rst
.. include:: blockgroup.rst
.. include:: special_inodes.rst
.. include:: allocators.rst
.. include:: checksums.rst
.. include:: bigalloc.rst
.. include:: inlinedata.rst
.. include:: eainode.rst
.. include:: verity.rst
