### SPDX 许可证标识符: GPL-2.0

#### NVMEM 子系统

##### Srinivas Kandagatla <srinivas.kandagatla@linaro.org>

本文档解释了 NVMEM 框架及其提供的 API，以及如何使用它。

1. **简介**
   - *NVMEM* 是非易失性内存层的简称。它用于从如 EEPROM、eFuses 等非易失性内存中检索特定于系统芯片（SoC）或设备的数据配置。
   - 在此框架出现之前，像 EEPROM 这样的 NVMEM 驱动程序都存储在 `drivers/misc` 中，它们几乎都需要重复编写相同的代码来注册 sysfs 文件、允许内核中的用户访问其所驱动设备的内容等。
   - 这也给其他内核用户带来了问题，因为所使用的解决方案从一个驱动程序到另一个驱动程序大不相同，导致了一个较大的抽象泄露。
   - 该框架旨在解决这些问题。它还引入了设备树表示法，使消费者设备能够从 NVMEM 中获取所需数据（例如 MAC 地址、SoC/修订版本 ID、部件编号等）。

   - **NVMEM 提供者**
     - NVMEM 提供者是指实现初始化、读取和写入非易失性内存方法的实体。

2. **注册/注销 NVMEM 提供者**
   - NVMEM 提供者可以通过向 `nvmem_register()` 函数提供相关的 NVMEM 配置来注册到 NVMEM 核心。如果成功，核心将返回一个有效的 `nvmem_device` 指针。
   - 使用 `nvmem_unregister()` 来注销已注册的提供者。
   
   例如，一个简单的 NVRAM 情况：
   ```c
   static int brcm_nvram_probe(struct platform_device *pdev)
   {
       struct nvmem_config config = {
           .name = "brcm-nvram",
           .reg_read = brcm_nvram_read,
       };
       ...
       config.dev = &pdev->dev;
       config.priv = priv;
       config.size = resource_size(res);

       devm_nvmem_register(&config);
   }
   ```
   - 板级文件的使用者可以定义并使用 `nvmem_cell_table` 结构体来注册 NVMEM 单元格：
   ```c
   static struct nvmem_cell_info foo_nvmem_cells[] = {
       {
           .name = "macaddr",
           .offset = 0x7f00,
           .bytes = ETH_ALEN,
       }
   };

   static struct nvmem_cell_table foo_nvmem_cell_table = {
       .nvmem_name = "i2c-eeprom",
       .cells = foo_nvmem_cells,
       .ncells = ARRAY_SIZE(foo_nvmem_cells),
   };

   nvmem_add_cell_table(&foo_nvmem_cell_table);
   ```

   - 此外，还可以创建 NVMEM 单元格查找表，并从机器代码中注册它们，如下所示：
   ```c
   static struct nvmem_cell_lookup foo_nvmem_lookup = {
       .nvmem_name = "i2c-eeprom",
       .cell_name = "macaddr",
       .dev_id = "foo_mac.0",
       .con_id = "mac-address",
   };

   nvmem_add_cell_lookups(&foo_nvmem_lookup, 1);
   ```

   - **NVMEM 消费者**
     - NVMEM 消费者是利用 NVMEM 提供者从 NVMEM 读取和写入数据的实体。
### 基于NVMEM单元的消费者API
=================================

NVMEM单元是NVMEM中的数据条目/字段。
NVMEM框架提供了3个API来读取/写入NVMEM单元：

  - `struct nvmem_cell *nvmem_cell_get(struct device *dev, const char *name);`
  - `struct nvmem_cell *devm_nvmem_cell_get(struct device *dev, const char *name);`

  - `void nvmem_cell_put(struct nvmem_cell *cell);`
  - `void devm_nvmem_cell_put(struct device *dev, struct nvmem_cell *cell);`

  - `void *nvmem_cell_read(struct nvmem_cell *cell, ssize_t *len);`
  - `int nvmem_cell_write(struct nvmem_cell *cell, void *buf, ssize_t len);`

`*nvmem_cell_get()` API会根据给定的ID获取对NVMEM单元的引用，然后可以使用`nvmem_cell_read/write()`读取或写入该单元。一旦完成对该单元的使用，消费者应该调用`*nvmem_cell_put()`释放该单元的所有分配内存。

### 基于直接NVMEM设备的消费者API
==========================================

在某些情况下，需要直接读取/写入NVMEM。为了方便此类消费者，NVMEM框架提供了以下API：

  - `struct nvmem_device *nvmem_device_get(struct device *dev, const char *name);`
  - `struct nvmem_device *devm_nvmem_device_get(struct device *dev, const char *name);`
  - `struct nvmem_device *nvmem_device_find(void *data, int (*match)(struct device *dev, const void *data));`
  - `void nvmem_device_put(struct nvmem_device *nvmem);`
  - `int nvmem_device_read(struct nvmem_device *nvmem, unsigned int offset, size_t bytes, void *buf);`
  - `int nvmem_device_write(struct nvmem_device *nvmem, unsigned int offset, size_t bytes, void *buf);`
  - `int nvmem_device_cell_read(struct nvmem_device *nvmem, struct nvmem_cell_info *info, void *buf);`
  - `int nvmem_device_cell_write(struct nvmem_device *nvmem, struct nvmem_cell_info *info, void *buf);`

在消费者可以直接读取/写入NVMEM之前，它应通过其中一个`*nvmem_device_get()` API获取NVMEM控制器。这些API与基于单元的API的区别在于这些API始终将nvmem_device作为参数。

### 释放NVMEM的引用
=====================================

当消费者不再需要NVMEM时，必须释放其通过上述部分中提到的API获得的NVMEM引用。
NVMEM框架提供了2个API来释放NVMEM的引用：

  - `void nvmem_cell_put(struct nvmem_cell *cell);`
  - `void devm_nvmem_cell_put(struct device *dev, struct nvmem_cell *cell);`
  - `void nvmem_device_put(struct nvmem_device *nvmem);`
  - `void devm_nvmem_device_put(struct device *dev, struct nvmem_device *nvmem);`

这两个API都用于释放NVMEM的引用，并且`devm_nvmem_cell_put`和`devm_nvmem_device_put`会销毁与此NVMEM相关的devres。

### 用户空间
+++++++++

### 用户空间二进制接口
==============================

用户空间可以从以下位置读取/写入原始NVMEM文件：

  `/sys/bus/nvmem/devices/*/nvmem`

例如：

  `hexdump /sys/bus/nvmem/devices/qfprom0/nvmem`

  ```
  0000000 0000 0000 0000 0000 0000 0000 0000 0000
  *
  00000a0 db10 2240 0000 e000 0c00 0c00 0000 0c00
  0000000 0000 0000 0000 0000 0000 0000 0000 0000
  ..
  *
  0001000
  ```

### DeviceTree绑定
=====================

请参阅Documentation/devicetree/bindings/nvmem/nvmem.txt

### NVMEM布局
=================

NVMEM布局是创建单元的另一种机制。使用DeviceTree绑定，可以使用偏移量和长度指定简单的单元。有时，单元没有静态偏移量，但内容仍然定义明确，例如标签-长度-值。在这种情况下，需要先解析NVMEM设备的内容，然后相应地添加单元。布局使您可以读取NVMEM设备的内容，并让您动态地添加单元。
布局的另一个用途是对单元格进行后期处理。通过使用布局，可以为单元格关联一个自定义的后期处理钩子。甚至有可能将此钩子添加到非布局自身创建的单元格中。

9. 内部内核API
=============

.. kernel-doc:: drivers/nvmem/core.c
   :export:
