.. 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_DISEQC_SEND_BURST:

**************************
ioctl FE_DISEQC_SEND_BURST
**************************

名称
====

FE_DISEQC_SEND_BURST - 发送用于2x1迷你DiSEqC卫星选择的22KHz音调脉冲

概要
====

.. c:宏:: FE_DISEQC_SEND_BURST

``int ioctl(int fd, FE_DISEQC_SEND_BURST, enum fe_sec_mini_cmd tone)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``tone``
    在 :c:type:`fe_sec_mini_cmd` 中定义的一个整数枚举值

描述
====

此 ioctl 用于设置生成用于2x1切换器的迷你 DiSEqC 卫星选择的22kHz音调脉冲。此调用需要读写权限。
它支持 `Digital Satellite Equipment Control (DiSEqC) - Simple "ToneBurst" Detection Circuit specification. <http://www.eutelsat.com/files/contributed/satellites/pdf/Diseqc/associated%20docs/simple_tone_burst_detec.pdf>`__ 中指定的内容。

返回值
======

成功时返回0
错误时返回-1，并且设置适当的 ``errno`` 变量
通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
