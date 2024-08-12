======================
达拉斯1线总线 (Dallas' 1-Wire Bus)
======================

:作者: David Fries

内核中的W1 API
=============================

`include/linux/w1.h`
~~~~~~~~~~~~~~~~~~

W1 内核API函数
.. kernel-doc:: include/linux/w1.h
   :internal:

`drivers/w1/w1.c`
~~~~~~~~~~~~~~~

W1 核心函数
.. kernel-doc:: drivers/w1/w1.c
   :internal:

`drivers/w1/w1_family.c`
~~~~~~~~~~~~~~~~~~~~~~~

允许注册设备家族的操作
.. kernel-doc:: drivers/w1/w1_family.c
   :export:

`drivers/w1/w1_internal.h`
~~~~~~~~~~~~~~~~~~~~~~~~

为主机设备进行W1内部初始化
.. kernel-doc:: drivers/w1/w1_internal.h
   :internal:

`drivers/w1/w1_int.c`
~~~~~~~~~~~~~~~~~~~~

为主机设备进行W1内部初始化
.. kernel-doc:: drivers/w1/w1_int.c
   :export:

`drivers/w1/w1_netlink.h`
~~~~~~~~~~~~~~~~~~~~~~~~

W1外部Netlink API结构和命令
.. kernel-doc:: drivers/w1/w1_netlink.h
   :internal:

`drivers/w1/w1_io.c`
~~~~~~~~~~~~~~~~~~~

W1 输入/输出
.. kernel-doc:: drivers/w1/w1_io.c
   :export:

.. kernel-doc:: drivers/w1/w1_io.c
   :internal:
