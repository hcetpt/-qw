SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _cec-func-open:

**********
cec_open()
**********

名称
====

cec_open - 打开一个 CEC 设备

概要
========

.. code-block:: c

    #include <fcntl.h>

.. c:function:: int open(const char *device_name, int flags)

参数
=========

``device_name``
    要打开的设备
``flags``
    打开标志。访问模式必须为 ``O_RDWR``
当给出 ``O_NONBLOCK`` 标志时，
    :ref:`CEC_RECEIVE <CEC_RECEIVE>` 和 :ref:`CEC_DQEVENT <CEC_DQEVENT>` 的 ioctl
    在没有消息或事件可用时将返回 ``EAGAIN`` 错误码，并且 ioctl
    :ref:`CEC_TRANSMIT <CEC_TRANSMIT>`、
    :ref:`CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>` 和
    :ref:`CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>`
    都将返回 0
其他标志无效

描述
===========

为了打开一个 CEC 设备，应用程序需要调用 :c:func:`open()` 并传入所需的设备名。该函数没有副作用；设备配置保持不变。
当设备以只读模式打开时，尝试修改其配置将导致错误，并且 ``errno`` 将被设置为 EBADF。

返回值
============

:c:func:`open()` 在成功时返回新的文件描述符。在发生错误时返回 -1，并且根据情况设置 ``errno``。可能的错误代码包括：

``EACCES``
    请求的文件访问权限不允许
``EMFILE``
    进程已经打开了最大数量的文件
``ENFILE``
    系统上打开文件的总数已达到上限
``ENOMEM``
    内核内存不足
``ENODEV``
设备未找到或已被移除
