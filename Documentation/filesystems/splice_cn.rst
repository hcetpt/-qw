================
剪切和管道
================

剪切 API
========

剪切是一种在内核内部移动数据块的方法，无需持续地在内核和用户空间之间传输数据。
.. kernel-doc:: fs/splice.c

管道 API
========

管道接口都是用于内核内部（内置镜像）的。它们不供模块使用。
.. kernel-doc:: include/linux/pipe_fs_i.h
   :internal:

.. kernel-doc:: fs/pipe.c
