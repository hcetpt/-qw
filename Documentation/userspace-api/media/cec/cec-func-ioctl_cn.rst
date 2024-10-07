SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _cec-func-ioctl:

***********
cec ioctl()
***********

名称
====

cec-ioctl - 控制一个 CEC 设备

概要
========

.. code-block:: c

    #include <sys/ioctl.h>

``int ioctl(int fd, int request, void *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``request``
    在 cec.h 头文件中定义的 CEC ioctl 请求代码，例如 :ref:`CEC_ADAP_G_CAPS <CEC_ADAP_G_CAPS>`
``argp``
    指向请求特定结构的指针
描述
===========

:c:func:`ioctl()` 函数用于操作 CEC 设备参数。参数 ``fd`` 必须是一个已打开的文件描述符。
ioctl 的 ``request`` 代码指定了要调用的 CEC 函数。该代码编码了参数是输入、输出还是读写参数，以及参数 ``argp`` 的字节大小。
定义 CEC ioctl 请求及其参数的宏和结构位于 cec.h 头文件中。所有 CEC ioctl 请求、其相应的函数及参数在 :ref:`cec-user-func` 中指定。
返回值
============

成功时返回 0，出错时返回 -1 并设置 ``errno`` 变量为适当的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
特定于请求的错误码列在各个请求的描述中。
当一个带有输出或读写参数的 ioctl 调用失败时，该参数保持不变。
