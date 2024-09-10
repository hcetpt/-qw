缓冲区头部
============

Linux 使用缓冲区头部来维护关于各个文件系统块的状态。缓冲区头部已被弃用，新的文件系统应使用 iomap。
函数
---------

.. kernel-doc:: include/linux/buffer_head.h
.. kernel-doc:: fs/buffer.c
   :export: 

（注：`.. kernel-doc::` 是一种用于生成文档的指令，并非实际的代码或文本内容，因此保留原样未作翻译。）
