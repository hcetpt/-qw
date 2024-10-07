.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_DISEQC_RECV_SLAVE_REPLY:

********************************
ioctl FE_DISEQC_RECV_SLAVE_REPLY
********************************

名称
====

FE_DISEQC_RECV_SLAVE_REPLY - 接收来自DiSEqC 2.0命令的回复

概要
========

.. c:宏:: FE_DISEQC_RECV_SLAVE_REPLY

``int ioctl(int fd, FE_DISEQC_RECV_SLAVE_REPLY, struct dvb_diseqc_slave_reply *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`dvb_diseqc_slave_reply` 结构体的指针

描述
===========

接收来自DiSEqC 2.0命令的回复
接收到的消息存储在由 ``argp`` 指向的缓冲区中

返回值
============

成功时返回0
错误时返回-1，并且设置 ``errno`` 变量为适当的值
通用错误代码在“通用错误代码”章节中有描述（:ref:`Generic Error Codes <gen-errors>`）。
