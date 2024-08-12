HW 消费者
===========
一个IIO（Industrial I/O）设备可以直接在硬件层面与另一个设备相连。在这种情况下，IIO提供者和IIO消费者之间的缓冲区由硬件处理。工业I/O HW消费者提供了一种方式来连接这些IIO设备，而无需软件缓冲数据。该实现可以在 :file:`drivers/iio/buffer/hw-consumer.c` 中找到。

* struct iio_hw_consumer — 硬件消费者结构体
* :c:func:`iio_hw_consumer_alloc` — 分配IIO硬件消费者
* :c:func:`iio_hw_consumer_free` — 释放IIO硬件消费者
* :c:func:`iio_hw_consumer_enable` — 启用IIO硬件消费者
* :c:func:`iio_hw_consumer_disable` — 禁用IIO硬件消费者

HW消费者设置
=================

作为标准的IIO设备，其实现基于IIO提供者/消费者模型。
典型的IIO HW消费者设置如下所示：

```c
static struct iio_hw_consumer *hwc;

static const struct iio_info adc_info = {
	.read_raw = adc_read_raw,
};

static int adc_read_raw(struct iio_dev *indio_dev,
			struct iio_chan_spec const *chan, int *val,
			int *val2, long mask)
{
	int ret;
	
	ret = iio_hw_consumer_enable(hwc);

	/* 获取数据 */

	ret = iio_hw_consumer_disable(hwc);
}

static int adc_probe(struct platform_device *pdev)
{
	hwc = devm_iio_hw_consumer_alloc(&iio->dev);
}
```

更多细节
============
.. kernel-doc:: drivers/iio/buffer/industrialio-hw-consumer.c
   :export:
