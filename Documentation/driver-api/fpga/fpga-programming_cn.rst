### FPGA编程的内核API
==================================

#### 概览
------------

FPGA编程的内核API结合了来自FPGA管理器、桥接器和区域的API。用于触发FPGA编程的实际函数是`fpga_region_program_fpga()`。`fpga_region_program_fpga()`使用由FPGA管理器和桥接器提供的功能。它会执行以下操作：

* 锁定区域的互斥锁
* 锁定该区域FPGA管理器的互斥锁
* 如果指定了方法，则构建一个FPGA桥接器列表
* 禁用桥接器
* 使用通过`fpga_region->info`传递的信息对FPGA进行编程
* 重新启用桥接器
* 释放锁

结构体`fpga_image_info`指定了要编程的FPGA图像。它可以通过`fpga_image_info_alloc()`分配，并通过`fpga_image_info_free()`释放。

#### 如何使用区域编程FPGA
-------------------------------------

当FPGA区域驱动程序被探测时，它会获得指向FPGA管理器驱动程序的指针，因此它知道要使用哪个管理器。该区域要么有一个在编程期间要控制的桥接器列表，要么有一个可以生成该列表的函数指针。下面是下一步操作的示例代码：

```c
#include <linux/fpga/fpga-mgr.h>
#include <linux/fpga/fpga-region.h>

struct fpga_image_info *info;
int ret;

/* 首先，分配一个包含有关要编程的FPGA图像信息的结构体 */
info = fpga_image_info_alloc(dev);
if (!info)
    return -ENOMEM;

/* 设置所需的标志，例如： */
info->flags = FPGA_MGR_PARTIAL_RECONFIG;

/* 指定FPGA图像的位置。这是伪代码；你将使用以下三种情况之一 */
if (image is in a scatter gather table) {

    info->sgt = [your scatter gather table];

} else if (image is in a buffer) {

    info->buf = [your image buffer];
    info->count = [image buffer size];

} else if (image is in a firmware file) {

    info->firmware_name = devm_kstrdup(dev, firmware_name, GFP_KERNEL);

}

/* 将信息添加到区域并进行编程 */
region->info = info;
ret = fpga_region_program_fpga(region);

/* 如果不再需要，释放图像信息 */
region->info = NULL;
fpga_image_info_free(info);

if (ret)
    return ret;

/* 现在枚举出现在FPGA中的任何硬件。 */
```

#### FPGA编程API
---------------------------

* `fpga_region_program_fpga()` — 编程FPGA
* `fpga_image_info()` — 指定要编程的FPGA图像
* `fpga_image_info_alloc()` — 分配FPGA图像信息结构体
* `fpga_image_info_free()` — 释放FPGA图像信息结构体

#### FPGA管理器标志

参见：
- `drivers/fpga/fpga-region.c` 中的 `fpga_region_program_fpga`
- `include/linux/fpga/fpga-mgr.h` 中的 FPGA管理器标志
- `include/linux/fpga/fpga-mgr.h` 中的 `fpga_image_info`
- `drivers/fpga/fpga-mgr.c` 中的 `fpga_image_info_alloc`
- `drivers/fpga/fpga-mgr.c` 中的 `fpga_image_info_free`
