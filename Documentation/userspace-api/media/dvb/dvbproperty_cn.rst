SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _前端属性:

**************
属性类型
**************

调谐到数字电视物理频道并开始解码需要更改一组参数，以控制调谐器、解调器、线性低噪声放大器（LNA）并通过卫星设备控制（SEC）设置天线子系统（在卫星系统中）。实际参数针对每种特定的数字电视标准，随着数字电视规范的发展可能会发生变化。在过去（直到DVB API版本3 - DVBv3），所使用的方法是将DVB-S、DVB-C、DVB-T和ATSC传输系统的调谐所需参数组合在一个联合体中。问题是，随着第二代标准的出现，这种联合体的大小不足以容纳新标准所需的结构。此外，对其进行扩展会破坏用户空间。

因此，基于联合体/结构体的方法被废弃，取而代之的是基于属性集的方法。在这种方法中，使用:ref:`FE_GET_PROPERTY 和 FE_SET_PROPERTY <FE_GET_PROPERTY>` 来设置前端并读取其状态。实际的操作由一系列dtv_property cmd/data对决定。通过单一的ioctl调用，可以获取或设置多达64个属性。本节描述了新的推荐方式来设置前端，支持所有数字电视传输系统。

.. note::

   1. 在Linux DVB API版本3中，设置前端是通过结构体 :c:type:`dvb_frontend_parameters` 完成的。
   2. 不要在支持更新标准的硬件上使用DVB API版本3调用。该API不支持或仅有限支持新标准和/或新硬件。
   3. 如今，大多数前端支持多种传输系统。只有通过DVB API版本5调用才能在前端支持的多种传输系统之间切换。
4. DVB API版本5也被称为*S2API*，因为首次添加到其中的新标准是DVB-S2。

**示例**：为了将硬件调谐到651kHz的DVB-C频道，该频道采用256-QAM调制、FEC 3/4和符号率为5.217 Mbauds，需要将这些属性发送给`FE_SET_PROPERTY` ioctl：

  `DTV_DELIVERY_SYSTEM` = SYS_DVBC_ANNEX_A

  `DTV_FREQUENCY` = 651000000

  `DTV_MODULATION` = QAM_256

  `DTV_INVERSION` = INVERSION_AUTO

  `DTV_SYMBOL_RATE` = 5217000

  `DTV_INNER_FEC` = FEC_3_4

  `DTV_TUNE`

实现上述功能的代码如`dtv-prop-example`所示：
```c
#include <stdio.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/dvb/frontend.h>

static struct dtv_property props[] = {
    { .cmd = DTV_DELIVERY_SYSTEM, .u.data = SYS_DVBC_ANNEX_A },
    { .cmd = DTV_FREQUENCY,       .u.data = 651000000 },
    { .cmd = DTV_MODULATION,      .u.data = QAM_256 },
    { .cmd = DTV_INVERSION,       .u.data = INVERSION_AUTO },
    { .cmd = DTV_SYMBOL_RATE,     .u.data = 5217000 },
    { .cmd = DTV_INNER_FEC,       .u.data = FEC_3_4 },
    { .cmd = DTV_TUNE }
};

static struct dtv_properties dtv_prop = {
    .num = 6, .props = props
};

int main(void)
{
    int fd = open("/dev/dvb/adapter0/frontend0", O_RDWR);

    if (!fd) {
        perror("open");
        return -1;
    }
    if (ioctl(fd, FE_SET_PROPERTY, &dtv_prop) == -1) {
        perror("ioctl");
        return -1;
    }
    printf("Frontend set\n");
    return 0;
}
```

**注意**：虽然可以直接像上面的例子那样调用内核代码，但强烈建议使用`libdvbv5 <https://linuxtv.org/docs/libdvbv5/index.html>`__，因为它提供了处理支持的数字电视标准的抽象，并提供了用于常见操作（如节目扫描和读写频道描述文件）的方法。

.. toctree::
    :maxdepth: 1

    fe_property_parameters
    frontend-stat-properties
    frontend-property-terrestrial-systems
    frontend-property-cable-systems
    frontend-property-satellite-systems
    frontend-header
```
