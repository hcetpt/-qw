===============================
工业IIO配置文件系统支持
===============================

1. 概览
===========

配置文件系统（Configfs）是一种基于文件系统的内核对象管理器。IIO使用了一些可以通过配置文件系统轻松配置的对象（例如：设备、触发器）。
有关配置文件系统如何工作的更多信息，请参阅Documentation/filesystems/configfs.rst。
2. 使用方法
========

为了在IIO中使用配置文件系统支持，我们需要通过CONFIG_IIO_CONFIGFS配置选项在编译时选择它。
然后，挂载配置文件系统（通常在/config目录下）：

```
$ mkdir /config
$ mount -t configfs none /config
```

此时，所有默认的IIO组将被创建，并可以在/config/iio下访问。接下来的章节将描述可用的IIO配置对象。
3. 软件触发器
====================

一个默认的配置文件系统组是“触发器”组。当挂载配置文件系统时，该组会自动变得可访问，并且可以在/config/iio/triggers下找到。
IIO软件触发器实现提供了创建多种触发器类型的支持。一个新的触发器类型通常是作为一个单独的内核模块来实现的，遵循include/linux/iio/sw_trigger.h中的接口：

```
/*
 * drivers/iio/trigger/iio-trig-sample.c
 * 实现新的触发器类型的示例内核模块
 */
#include <linux/iio/sw_trigger.h>

static struct iio_sw_trigger *iio_trig_sample_probe(const char *name)
{
    /*
     * 这里分配并注册了一个IIO触发器以及进行其他特定于触发器类型的初始化
     */
}

static int iio_trig_sample_remove(struct iio_sw_trigger *swt)
{
    /*
     * 这里撤销了iio_trig_sample_probe中的操作
     */
}

static const struct iio_sw_trigger_ops iio_trig_sample_ops = {
    .probe = iio_trig_sample_probe,
    .remove = iio_trig_sample_remove,
};

static struct iio_sw_trigger_type iio_trig_sample = {
    .name = "trig-sample",
    .owner = THIS_MODULE,
    .ops = &iio_trig_sample_ops,
};

module_iio_sw_trigger_driver(iio_trig_sample);
```

每个触发器类型在其目录下都有一个自己的目录/config/iio/triggers。加载iio-trig-sample模块将创建名为“trig-sample”的触发器类型目录/config/iio/triggers/trig-sample。

我们支持以下中断源（触发器类型）：

- hrtimer，使用高分辨率定时器作为中断源

3.1 Hrtimer触发器的创建和销毁
---------------------------------------------

加载iio-trig-hrtimer模块将注册Hrtimer触发器类型，允许用户在/config/iio/triggers/hrtimer下创建Hrtimer触发器。
例如：
```
$ mkdir /config/iio/triggers/hrtimer/instance1
$ rmdir /config/iio/triggers/hrtimer/instance1
```

每个触发器可以有一个或多个特定于触发器类型的属性。
3.2 “hrtimer”触发器类型的属性
--------------------------------------

“hrtimer”触发器类型没有任何从/config目录可配置的属性。
这确实引入了sampling_frequency属性来触发目录
该属性以赫兹（Hz）为单位设置轮询频率，并具有毫赫兹（mHz）的精度。
