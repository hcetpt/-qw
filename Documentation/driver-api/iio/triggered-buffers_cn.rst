触发式缓冲区
=============

现在我们已经了解了缓冲区和触发器是什么，让我们来看看它们是如何协同工作的。
IIO 触发式缓冲区设置
=====================

* :c:func:`iio_triggered_buffer_setup` — 设置触发式缓冲区及轮询函数
* :c:func:`iio_triggered_buffer_cleanup` — 释放由 :c:func:`iio_triggered_buffer_setup` 分配的资源
* struct iio_buffer_setup_ops — 与缓冲区设置相关的回调函数

一个典型的触发式缓冲区设置如下所示::

    const struct iio_buffer_setup_ops sensor_buffer_setup_ops = {
      .preenable    = sensor_buffer_preenable,
      .postenable   = sensor_buffer_postenable,
      .postdisable  = sensor_buffer_postdisable,
      .predisable   = sensor_buffer_predisable,
    };

    irqreturn_t sensor_iio_pollfunc(int irq, void *p)
    {
        pf->timestamp = iio_get_time_ns((struct indio_dev *)p);
        return IRQ_WAKE_THREAD;
    }

    irqreturn_t sensor_trigger_handler(int irq, void *p)
    {
        u16 buf[8];
        int i = 0;

        /* 为每个激活的通道读取数据 */
        for_each_set_bit(bit, active_scan_mask, masklength)
            buf[i++] = sensor_get_data(bit)

        iio_push_to_buffers_with_timestamp(indio_dev, buf, timestamp);

        iio_trigger_notify_done(trigger);
        return IRQ_HANDLED;
    }

    /* 在probe函数中通常设置触发式缓冲区 */
    iio_triggered_buffer_setup(indio_dev, sensor_iio_polfunc,
                               sensor_trigger_handler,
                               sensor_buffer_setup_ops);

这里需要注意的关键点是：

* :c:type:`iio_buffer_setup_ops`，这些缓冲区设置函数将在预定义的缓冲区配置序列中的特定时刻被调用（例如，在启用之前，禁用之后）。如果没有指定，则IIO核心使用默认的 iio_triggered_buffer_setup_ops
* **sensor_iio_pollfunc**，将用作轮询函数的上半部分的函数。应该尽可能少地进行处理，因为它在中断上下文中运行。最常见的操作是记录当前的时间戳，并且为此可以使用IIO核心定义的 :c:func:`iio_pollfunc_store_time` 函数
* **sensor_trigger_handler**，将用作轮询函数下半部分的函数。这在内核线程上下文中运行，所有的处理都在这里发生。它通常从设备读取数据并将其与在上半部分记录的时间戳一起存储在内部缓冲区中
更多细节
=========
.. kernel-doc:: drivers/iio/buffer/industrialio-triggered-buffer.c
