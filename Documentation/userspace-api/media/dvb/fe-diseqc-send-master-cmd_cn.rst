SPDX 许可声明标识符：GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_DISEQC_SEND_MASTER_CMD:

*******************************
ioctl FE_DISEQC_SEND_MASTER_CMD
*******************************

名称
====

FE_DISEQC_SEND_MASTER_CMD - 发送 DiSEqC 命令

概要
====

.. c:macro:: FE_DISEQC_SEND_MASTER_CMD

``int ioctl(int fd, FE_DISEQC_SEND_MASTER_CMD, struct dvb_diseqc_master_cmd *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`dvb_diseqc_master_cmd` 的指针

描述
====

将由 :c:type:`dvb_diseqc_master_cmd` 指向的 DiSEqC 命令发送到天线子系统。
返回值
======

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为相应的错误码
通用错误码在“通用错误码”章节中描述。
