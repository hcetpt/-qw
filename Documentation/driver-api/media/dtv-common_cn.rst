SPDX 许可证标识符: GPL-2.0

数字电视通用功能
---------------------------

DVB 设备
~~~~~~~~~~~

这些函数负责处理 DVB 设备节点。
.. kernel-doc:: include/media/dvbdev.h

数字电视环形缓冲区
~~~~~~~~~~~~~~~~~~~~~~

这些例程实现了用于处理数字电视数据并从/向用户空间复制的环形缓冲区。
.. note::

  1) 出于性能考虑，读取和写入例程不检查缓冲区大小和/或剩余/可用字节数。这必须在调用这些例程之前完成。例如：

   .. code-block:: c

        /* 写入 @buflen: 字节 */
        free = dvb_ringbuffer_free(rbuf);
        if (free >= buflen)
                count = dvb_ringbuffer_write(rbuf, buffer, buflen);
        else
                /* 做些其他事情 */

        /* 读取最少 1000，最多 @bufsize: 字节 */
        avail = dvb_ringbuffer_avail(rbuf);
        if (avail >= 1000)
                count = dvb_ringbuffer_read(rbuf, buffer, min(avail, bufsize));
        else
                /* 做些其他事情 */

  2) 如果恰好有一个读者和一个写者，则无需锁定读取或写入操作。
     两个或多个读者必须互相锁定
     清空缓冲区被视为读取操作
     重置缓冲区被视为读取和写入操作
     两个或多个写者必须互相锁定
.. kernel-doc:: include/media/dvb_ringbuffer.h

数字电视 VB2 处理器
~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/media/dvb_vb2.h
