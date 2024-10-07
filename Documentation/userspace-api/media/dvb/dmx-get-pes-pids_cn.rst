SPDX 许可声明标识符：GFDL-1.1-no-invariants-or-later
C 命名空间: DTV.dmx

.. _DMX_GET_PES_PIDS:

================
DMX_GET_PES_PIDS
================

名称
----

DMX_GET_PES_PIDS

简介
--------

.. c:macro:: DMX_GET_PES_PIDS

``int ioctl(fd, DMX_GET_PES_PIDS, __u16 pids[5])``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符。
``pids``
    用于存储 5 个节目 ID 的数组。

描述
-----------

此 ioctl（输入/输出控制）命令允许查询 DVB 设备以返回给定服务上音频、视频、图文电视、字幕和 PCR 程序所使用的第一个 PID。它们按如下方式存储：

=======================	========	=======================================
PID 元素	位置	内容
=======================	========	=======================================
pids[DMX_PES_AUDIO]	0		第一个音频 PID
pids[DMX_PES_VIDEO]	1		第一个视频 PID
pids[DMX_PES_TELETEXT]	2		第一个图文电视 PID
pids[DMX_PES_SUBTITLE]	3		第一个字幕 PID
pids[DMX_PES_PCR]	4		第一个节目时钟参考 (PCR) PID
=======================	========	=======================================

.. note::

    值为 0xffff 表示该 PID 未被内核填充。

返回值
------------

成功时返回 0；
出错时返回 -1，并设置 ``errno`` 变量以指示错误原因。
通用错误代码在“通用错误代码”章节中描述。
