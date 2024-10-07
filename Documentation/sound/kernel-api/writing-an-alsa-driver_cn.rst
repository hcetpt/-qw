编写ALSA驱动程序
======================

:作者: Takashi Iwai <tiwai@suse.de>

前言
=======

本文档描述了如何编写`ALSA（高级Linux声音架构）<http://www.alsa-project.org/>`__驱动程序。本文档主要关注PCI声卡。对于其他设备类型，API可能有所不同。然而，至少ALSA内核API是一致的，因此对于编写这些驱动程序仍然有一定的帮助。本文档的目标读者是有足够的C语言技能并且具备基本Linux内核编程知识的人。本文档不解释Linux内核编码的一般主题，也不涵盖低级驱动程序实现细节。它仅描述了使用ALSA编写PCI声卡驱动的标准方法。
文件树结构
===================

概述
-------

ALSA驱动程序的文件树结构如下所示::

            sound
                    /core
                            /oss
                            /seq
                                    /oss
                    /include
                    /drivers
                            /mpu401
                            /opl3
                    /i2c
                    /synth
                            /emux
                    /pci
                            /(cards)
                    /isa
                            /(cards)
                    /arm
                    /ppc
                    /sparc
                    /usb
                    /pcmcia /(cards)
                    /soc
                    /oss

core目录
--------------

此目录包含作为ALSA驱动程序核心的中间层。在此目录中存储了原生的ALSA模块。子目录包含不同的模块，并且依赖于内核配置。
core/oss
~~~~~~~~

OSS PCM和混音器仿真模块的代码存储在此目录中。由于ALSA rawmidi代码相当小，所以OSS rawmidi仿真包含在其中。序列器代码存储在``core/seq/oss``目录中（见下文<core/seq/oss_>`__）
core/seq
~~~~~~~~

此目录及其子目录用于ALSA序列器。此目录包含序列器核心和主要的序列器模块，如snd-seq-midi、snd-seq-virmidi等。当内核配置中的``CONFIG_SND_SEQUENCER``被设置时，它们才会被编译。
core/seq/oss
~~~~~~~~~~~~

此目录包含OSS序列器仿真代码。
include目录
-----------------

这是ALSA驱动程序公共头文件的存放位置，这些文件会被导出到用户空间，或者由不同目录中的多个文件包含。基本上，私有头文件不应放置在此目录中，但由于历史原因，你仍可能会在这里找到一些文件 :)

drivers目录
-----------------

此目录包含不同架构之间共享的不同驱动程序代码。因此，它们不应该是特定于架构的。例如，虚拟PCM驱动程序和串行MIDI驱动程序可以在该目录中找到。在子目录中，有独立于总线和CPU架构的组件代码。
drivers/mpu401
~~~~~~~~~~~~~~

MPU401和MPU401-UART模块存储在此处。
drivers/opl3 和 opl4
~~~~~~~~~~~~~~~~~~~~~

OPL3和OPL4 FM合成器的相关内容可以在此处找到。
i2c 目录
-------------

此目录包含 ALSA 的 I2C 组件。
尽管 Linux 上有一个标准的 I2C 层，但 ALSA 对某些声卡有自己的 I2C 代码，因为声卡只需要一个简单的操作，而标准的 I2C API 对此目的来说过于复杂。

synth 目录
--------------

此目录包含合成器中间层模块。
到目前为止，只有 Emu8000/Emu10k1 合成器驱动位于 `synth/emux` 子目录下。

pci 目录
-------------

此目录及其子目录包含 PCI 声卡的顶级模块和特定于 PCI 总线的代码。
由单个文件编译的驱动程序直接存储在 pci 目录中，而包含多个源文件的驱动程序则存储在各自的子目录中（例如 emu10k1、ice1712）。

isa 目录
-------------

此目录及其子目录包含 ISA 声卡的顶级模块。

arm、ppc 和 sparc 目录
-------------------------------

它们用于特定于这些架构的顶级声卡模块。

usb 目录
-------------

此目录包含 USB 音频驱动程序。
USB MIDI 驱动程序集成在 USB 音频驱动程序中。
### PCMCIA 目录

PCMCIA 驱动，特别是 PCCard 驱动将放在这里。CardBus 驱动将会放在 pci 目录中，因为它们的 API 与标准 PCI 卡相同。

### SoC 目录

此目录包含 ASoC（ALSA 系统级芯片）层的代码，包括 ASoC 核心、编解码器和机器驱动。

### OSS 目录

此目录包含 OSS/Lite 代码。截至撰写时，除了 m68k 上的 dmasound 外，其他所有代码都已移除。

### PCI 驱动的基本流程
#### 概述

PCI 声卡的基本流程如下：

- 定义 PCI ID 表（参见 `PCI Entries`_ 部分）
- 创建 `probe` 回调函数
- 创建 `remove` 回调函数
- 创建一个 `struct pci_driver` 结构体，其中包含上述三个指针
- 创建一个 `init` 函数，用于调用 `pci_register_driver()` 注册上述定义的 pci_driver 表
- 创建一个 `exit` 函数，用于调用 `pci_unregister_driver()` 函数
完整代码示例
-----------------

下面展示了代码示例。某些部分目前尚未实现，但将在后续章节中填充。注释行中的数字指的是 `snd_mychip_probe()` 函数中解释的细节：

```c
#include <linux/init.h>
#include <linux/pci.h>
#include <linux/slab.h>
#include <sound/core.h>
#include <sound/initval.h>

/* 模块参数（见“模块参数”） */
/* SNDRV_CARDS：此模块支持的最大卡数 */
static int index[SNDRV_CARDS] = SNDRV_DEFAULT_IDX;
static char *id[SNDRV_CARDS] = SNDRV_DEFAULT_STR;
static bool enable[SNDRV_CARDS] = SNDRV_DEFAULT_ENABLE_PNP;

/* 定义特定于芯片的记录 */
struct mychip {
    struct snd_card *card;
    /* 其余实现将在“PCI资源管理”部分中展示 */
};

/* 特定于芯片的析构函数
 * （见“PCI资源管理”）
 */
static int snd_mychip_free(struct mychip *chip)
{
    .... /* 将在后续部分实现... */
}

/* 组件析构函数
 * （见“卡片和组件的管理”）
 */
static int snd_mychip_dev_free(struct snd_device *device)
{
    return snd_mychip_free(device->device_data);
}

/* 特定于芯片的构造函数
 * （见“卡片和组件的管理”）
 */
static int snd_mychip_create(struct snd_card *card,
                             struct pci_dev *pci,
                             struct mychip **rchip)
{
    struct mychip *chip;
    int err;
    static const struct snd_device_ops ops = {
        .dev_free = snd_mychip_dev_free,
    };

    *rchip = NULL;

    /* 检查PCI可用性
     * （见“PCI资源管理”）
     */
    ...

    /* 分配一个特定于芯片的数据，并用零填充 */
    chip = kzalloc(sizeof(*chip), GFP_KERNEL);
    if (chip == NULL)
        return -ENOMEM;

    chip->card = card;

    /* 剩余初始化在此处进行；将在后续部分实现
     * 见“PCI资源管理”
     */
    ...

    err = snd_device_new(card, SNDRV_DEV_LOWLEVEL, chip, &ops);
    if (err < 0) {
        snd_mychip_free(chip);
        return err;
    }

    *rchip = chip;
    return 0;
}

/* 构造函数——见“驱动程序构造函数”小节 */
static int snd_mychip_probe(struct pci_dev *pci,
                            const struct pci_device_id *pci_id)
{
    static int dev;
    struct snd_card *card;
    struct mychip *chip;
    int err;

    /* (1) */
    if (dev >= SNDRV_CARDS)
        return -ENODEV;
    if (!enable[dev]) {
        dev++;
        return -ENOENT;
    }

    /* (2) */
    err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                       0, &card);
    if (err < 0)
        return err;

    /* (3) */
    err = snd_mychip_create(card, pci, &chip);
    if (err < 0)
        goto error;

    /* (4) */
    strcpy(card->driver, "My Chip");
    strcpy(card->shortname, "My Own Chip 123");
    sprintf(card->longname, "%s at 0x%lx irq %i",
            card->shortname, chip->port, chip->irq);

    /* (5) */
    .... /* 在后续部分实现 */

    /* (6) */
    err = snd_card_register(card);
    if (err < 0)
        goto error;

    /* (7) */
    pci_set_drvdata(pci, card);
    dev++;
    return 0;

error:
    snd_card_free(card);
    return err;
}

/* 析构函数——见“析构函数”小节 */
static void snd_mychip_remove(struct pci_dev *pci)
{
    snd_card_free(pci_get_drvdata(pci));
}
```

驱动程序构造函数
------------------

PCI驱动程序的实际构造函数是`probe`回调。由于任何PCI设备都可能是热插拔设备，因此不能在`probe`回调和其他从`probe`回调调用的组件构造函数中使用`__init`前缀。在`probe`回调中，通常采用以下模式：
1) 检查并递增设备索引
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```c
static int dev;
...
if (dev >= SNDRV_CARDS)
    return -ENODEV;
if (!enable[dev]) {
    dev++;
    return -ENOENT;
}
```

其中`enable[dev]`是模块选项。每次调用`probe`回调时，检查设备是否可用。如果不可用，则简单地递增设备索引并返回。dev也会在步骤7（设置PCI驱动程序数据并返回零）之后递增。
2) 创建一个卡片实例
~~~~~~~~~~~~~~~~~~~~~~~~~

```c
struct snd_card *card;
int err;
...
```
```c
err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE, 0, &card);
```

详细内容将在《声卡与组件管理》一节中解释。

3) 创建主组件
~~~~~~~~~~~~~~

在这一部分，分配 PCI 资源：

```c
struct mychip *chip;
...
err = snd_mychip_create(card, pci, &chip);
if (err < 0)
    goto error;
```

当出现问题时，probe 函数需要处理错误。在此示例中，我们在函数末尾放置了一个单一的错误处理路径：

```c
error:
    snd_card_free(card);
    return err;
```

由于每个组件都可以正确地释放，通常情况下单个 `snd_card_free()` 调用就足够了。

4) 设置驱动程序 ID 和名称字符串
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```c
strcpy(card->driver, "My Chip");
strcpy(card->shortname, "My Own Chip 123");
sprintf(card->longname, "%s at 0x%lx irq %i", card->shortname, chip->port, chip->irq);
```

`driver` 字段包含芯片的最小 ID 字符串。这是由 alsa-lib 的配置器使用的，因此保持简单但唯一。即使是同一个驱动程序也可以有不同的驱动 ID 来区分每种芯片类型的功能。

`shortname` 字段是一个显示为更详细名称的字符串。`longname` 字段包含在 `/proc/asound/cards` 中显示的信息。

5) 创建其他组件，如混音器、MIDI 等
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在这里定义基本组件，例如 `PCM` 接口、混音器（如 `AC97`）、MIDI（如 `MPU-401`）及其他接口。
```
另外，如果你想定义一个 `proc 文件 <Proc Interface_>`__，也可以在这里定义。
6) 注册卡片实例
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  err = snd_card_register(card);
  if (err < 0)
          goto error;

这将在 `卡片和组件的管理`_ 部分进行解释。
7) 设置 PCI 驱动数据并返回零
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  pci_set_drvdata(pci, card);
  dev++;
  return 0;

在上面的代码中，存储了卡片记录。这个指针也在移除回调和电源管理回调中使用。

析构函数
---------

析构函数（即移除回调）仅释放卡片实例。然后 ALSA 中间层会自动释放所有已附加的组件。通常只需调用 :c:func:`snd_card_free()`：

::

  static void snd_mychip_remove(struct pci_dev *pci)
  {
          snd_card_free(pci_get_drvdata(pci));
  }

上述代码假设卡片指针已经设置为 PCI 驱动的数据。
头文件
------------

对于上述示例，至少需要以下头文件：

::

  #include <linux/init.h>
  #include <linux/pci.h>
  #include <linux/slab.h>
  #include <sound/core.h>
  #include <sound/initval.h>

其中最后一个头文件只有在源文件中定义模块选项时才需要。如果代码被拆分成多个文件，则没有模块选项的文件不需要包含它。
除了这些头文件外，你还需要 ``<linux/interrupt.h>`` 用于中断处理，以及 ``<linux/io.h>`` 用于 I/O 访问。如果你使用了 :c:func:`mdelay()` 或 :c:func:`udelay()` 函数，还需要包含 ``<linux/delay.h>``。
ALSA 接口如 PCM 和控制 API 在其他 `<sound/xxx.h>` 头文件中定义。这些头文件必须在 `<sound/core.h>` 之后包含。

### 卡和组件管理

#### 卡实例

对于每块声卡，必须分配一个“卡”记录。
卡记录是声卡的中心。它管理声卡上的所有设备（组件）列表，例如 PCM、混音器、MIDI、合成器等。此外，卡记录还持有卡的 ID 和名称字符串，管理 proc 文件的根目录，并控制电源管理和热插拔断开。卡记录中的组件列表用于在销毁时正确释放资源。

如前所述，要创建一个卡实例，需要调用 `:c:func:'snd_card_new()'` 函数：

```c
struct snd_card *card;
int err;
err = snd_card_new(&pci->dev, index, id, module, extra_size, &card);
```

该函数接受六个参数：父设备指针、卡索引号、ID 字符串、模块指针（通常是 `THIS_MODULE`）、额外数据空间大小以及返回卡实例的指针。`extra_size` 参数用于为 `card->private_data` 分配芯片特定的数据。请注意，这些数据是由 `:c:func:'snd_card_new()'` 函数分配的。

第一个参数 `struct device` 指针指定了父设备。对于 PCI 设备，通常传递 `&pci->dev`。

#### 组件

创建卡后，可以将组件（设备）附加到卡实例上。在 ALSA 驱动程序中，一个组件表示为 `struct snd_device` 对象。组件可以是一个 PCM 实例、一个控制接口、一个原始 MIDI 接口等。每个这样的实例都有一个组件条目。

可以通过 `:c:func:'snd_device_new()'` 函数创建组件：

```c
snd_device_new(card, SNDRV_DEV_XXX, chip, &ops);
```

这需要卡指针、设备级别（`SNDRV_DEV_XXX`）、数据指针以及回调指针（`&ops`）。设备级别定义了组件类型以及注册和注销顺序。对于大多数组件，设备级别已经定义。对于用户自定义组件，可以使用 `SNDRV_DEV_LOWLEVEL`。

该函数本身不会分配数据空间。数据必须手动预先分配，并将其指针作为参数传递。这个指针（如上例中的 `chip`）作为实例的标识符。

每个预定义的 ALSA 组件（如 AC97 和 PCM）在其构造函数内部调用 `:c:func:'snd_device_new()'`。每个组件的析构函数定义在回调指针中。因此，对于此类组件，无需关心调用析构函数。
如果你希望创建自己的组件，需要将析构函数设置为 `ops` 中的 `dev_free` 回调函数，以便通过 `snd_card_free()` 自动释放。下一个示例将展示芯片特定数据的实现。

### 芯片特定数据

芯片特定信息（例如 I/O 端口地址、资源指针或中断号）存储在芯片特定记录中：

```c
struct mychip {
    ...
};
```

一般来说，有以下两种分配芯片记录的方法：

1. 通过 `snd_card_new()` 分配
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   如上所述，你可以将额外数据长度传递给 `snd_card_new()` 的第 5 个参数，例如：

   ```c
   err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                      sizeof(struct mychip), &card);
   ```

   `struct mychip` 是芯片记录的类型。返回的已分配记录可以通过以下方式访问：

   ```c
   struct mychip *chip = card->private_data;
   ```

   使用这种方法，你不需要两次分配。记录会与卡实例一起释放。

2. 分配额外设备
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   在通过 `snd_card_new()` 分配一个卡实例（第 4 个参数为 `0`）之后，调用 `kzalloc()`：

   ```c
   struct snd_card *card;
   struct mychip *chip;
   err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                      0, &card);
   ...
   chip = kzalloc(sizeof(*chip), GFP_KERNEL);
   ```

   芯片记录至少应该包含一个字段来保存卡指针：

   ```c
   struct mychip {
       struct snd_card *card;
       ...
   };
   ```

   然后，在返回的芯片实例中设置卡指针：

   ```c
   chip->card = card;
   ```

   接下来初始化字段，并使用指定的 `ops` 将此芯片记录注册为低级设备：

   ```c
   static const struct snd_device_ops ops = {
       .dev_free = snd_mychip_dev_free,
   };
   ...
   ```
```c
// 创建设备实例
snd_device_new(card, SNDRV_DEV_LOWLEVEL, chip, &ops);

// 设备析构函数
:c:func:`snd_mychip_dev_free()` 是设备的析构函数，它会调用实际的析构函数：

  static int snd_mychip_dev_free(struct snd_device *device)
  {
          return snd_mychip_free(device->device_data);
  }

其中 :c:func:`snd_mychip_free()` 是实际的析构函数。

这种方法的一个缺点是代码量明显增加。然而，优点在于你可以在注册和断开声卡时通过设置 `snd_device_ops` 触发自己的回调。关于注册和断开声卡，请参见下面的小节。

注册和释放
------------------------

在所有组件分配完毕后，通过调用 :c:func:`snd_card_register()` 来注册声卡实例。此时可以访问设备文件。也就是说，在调用 :c:func:`snd_card_register()` 之前，外部无法访问这些组件。如果此调用失败，则在释放声卡后退出探测函数。

为了释放声卡实例，你可以简单地调用 :c:func:`snd_card_free()`。如前所述，此调用会自动释放所有组件。

对于支持热插拔的设备，你可以使用 :c:func:`snd_card_free_when_closed()`。这会在所有设备关闭后再延迟销毁。

PCI资源管理
=======================

完整代码示例
-----------------

在本节中，我们将完成特定于芯片的构造函数、析构函数和PCI条目。首先展示示例代码：

```c
struct mychip {
        struct snd_card *card;
        struct pci_dev *pci;

        unsigned long port;
        int irq;
};

static int snd_mychip_free(struct mychip *chip)
{
        /* 禁用硬件（如果有的话） */
        .... /* （在此文档中未实现） */

        /* 释放中断 */
        if (chip->irq >= 0)
                free_irq(chip->irq, chip);
        /* 释放I/O端口和内存 */
        pci_release_regions(chip->pci);
        /* 禁用PCI条目 */
        pci_disable_device(chip->pci);
        /* 释放数据 */
        kfree(chip);
        return 0;
}

/* 特定于芯片的构造函数 */
static int snd_mychip_create(struct snd_card *card,
                             struct pci_dev *pci,
                             struct mychip **rchip)
{
        struct mychip *chip;
        int err;
        static const struct snd_device_ops ops = {
                .dev_free = snd_mychip_dev_free,
        };

        *rchip = NULL;

        /* 初始化PCI条目 */
        err = pci_enable_device(pci);
        if (err < 0)
                return err;
        /* 检查PCI可用性（28位DMA） */
        if (pci_set_dma_mask(pci, DMA_BIT_MASK(28)) < 0 ||
            pci_set_consistent_dma_mask(pci, DMA_BIT_MASK(28)) < 0) {
                printk(KERN_ERR "设置28位DMA掩码出错\n");
                pci_disable_device(pci);
                return -ENXIO;
        }

        chip = kzalloc(sizeof(*chip), GFP_KERNEL);
        if (chip == NULL) {
                pci_disable_device(pci);
                return -ENOMEM;
        }

        /* 初始化相关结构 */
        chip->card = card;
        chip->pci = pci;
        chip->irq = -1;

        /* (1) 分配PCI资源 */
        err = pci_request_regions(pci, "My Chip");
        if (err < 0) {
                kfree(chip);
                pci_disable_device(pci);
                return err;
        }
        chip->port = pci_resource_start(pci, 0);
        if (request_irq(pci->irq, snd_mychip_interrupt,
                        IRQF_SHARED, KBUILD_MODNAME, chip)) {
                printk(KERN_ERR "无法获取中断 %d\n", pci->irq);
                snd_mychip_free(chip);
                return -EBUSY;
        }
        chip->irq = pci->irq;
        card->sync_irq = chip->irq;

        /* (2) 初始化硬件 */
        .... /* （在此文档中未实现） */

        err = snd_device_new(card, SNDRV_DEV_LOWLEVEL, chip, &ops);
        if (err < 0) {
                snd_mychip_free(chip);
                return err;
        }

        *rchip = chip;
        return 0;
}

/* PCI ID表 */
static struct pci_device_id snd_mychip_ids[] = {
        { PCI_VENDOR_ID_FOO, PCI_DEVICE_ID_BAR,
          PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0, },
        ...
        { 0, }
};
MODULE_DEVICE_TABLE(pci, snd_mychip_ids);

/* PCI驱动定义 */
static struct pci_driver driver = {
        .name = KBUILD_MODNAME,
        .id_table = snd_mychip_ids,
        .probe = snd_mychip_probe,
        .remove = snd_mychip_remove,
};

/* 模块初始化 */
static int __init alsa_card_mychip_init(void)
{
        return pci_register_driver(&driver);
}

/* 模块清理 */
static void __exit alsa_card_mychip_exit(void)
{
        pci_unregister_driver(&driver);
}

module_init(alsa_card_mychip_init)
module_exit(alsa_card_mychip_exit)

EXPORT_NO_SYMBOLS; /* 仅适用于旧内核 */

一些注意事项
--------------

PCI资源的分配是在 `probe` 函数中完成的，通常为此目的编写一个额外的 :c:func:`xxx_create()` 函数。
对于PCI设备，你需要在分配资源之前先调用 :c:func:`pci_enable_device()` 函数。此外，你需要设置适当的PCI DMA掩码来限制访问的I/O范围。在某些情况下，你可能还需要调用 :c:func:`pci_set_master()` 函数。
```
假设一个28位掩码，需要添加的代码如下：

```c
err = pci_enable_device(pci);
if (err < 0)
        return err;
if (pci_set_dma_mask(pci, DMA_BIT_MASK(28)) < 0 ||
    pci_set_consistent_dma_mask(pci, DMA_BIT_MASK(28)) < 0) {
        printk(KERN_ERR "设置28位掩码DMA时出错\n");
        pci_disable_device(pci);
        return -ENXIO;
}
```

资源分配
-------------------

I/O端口和中断的分配是通过标准内核函数完成的。这些资源必须在析构函数中释放（见下文）。
现在假设PCI设备有一个8字节的I/O端口和一个中断。那么`struct mychip`将具有以下字段：

```c
struct mychip {
        struct snd_card *card;

        unsigned long port;
        int irq;
};
```

对于一个I/O端口（以及内存区域），你需要有用于标准资源管理的资源指针。对于一个中断，你只需要保留中断号（整数）。但是在实际分配之前，需要将这个号码初始化为-1，因为中断号0是有效的。端口地址及其资源指针可以通过`kzalloc()`自动初始化为null，因此你不需要关心重置它们。

I/O端口的分配如下所示：

```c
err = pci_request_regions(pci, "My Chip");
if (err < 0) { 
        kfree(chip);
        pci_disable_device(pci);
        return err;
}
chip->port = pci_resource_start(pci, 0);
```

这将保留给定PCI设备的8字节I/O端口区域。
返回值`chip->port`是通过`kmalloc()`由`request_region()`分配的。该指针必须通过`kfree()`释放，但这存在一个问题。这个问题将在后面解释。

中断源的分配如下所示：

```c
if (request_irq(pci->irq, snd_mychip_interrupt,
                IRQF_SHARED, KBUILD_MODNAME, chip)) {
        printk(KERN_ERR "无法获取中断%d\n", pci->irq);
        snd_mychip_free(chip);
        return -EBUSY;
}
chip->irq = pci->irq;
```

其中`snd_mychip_interrupt()`是在`PCM Interrupt Handler`部分定义的中断处理程序。注意`chip->irq`应该仅在`request_irq()`成功时才被定义。

在PCI总线上，中断可以共享。因此，`IRQF_SHARED`作为`request_irq()`的中断标志使用。

`request_irq()`的最后一个参数是指传递给中断处理程序的数据指针。通常情况下，特定于芯片的记录被用于此目的，但你也可以使用任何你喜欢的内容。

这里不详细说明中断处理程序，但至少可以解释其外观。中断处理程序通常如下所示：

```c
static irqreturn_t snd_mychip_interrupt(int irq, void *dev_id)
{
        struct mychip *chip = dev_id;
        ...
        return IRQ_HANDLED;
}
```

请求中断后，你可以将其传递给`card->sync_irq`字段：

```c
card->irq = chip->irq;
```

这允许PCM核心在适当的时候自动调用`synchronize_irq()`，例如在`hw_free`之前。

有关详细信息，请参阅后面的`sync_stop回调`部分。
现在让我们为上面的资源编写相应的析构函数。
析构函数的作用很简单：禁用硬件（如果已经激活）并释放资源。到目前为止，我们还没有硬件部分，因此禁用代码在这里不编写。
为了释放资源，“检查并释放”的方法更安全。
对于中断，可以这样做：

  如果 (chip->irq >= 0)
          free_irq(chip->irq, chip);

由于中断号可以从0开始，你应该将 `chip->irq` 初始化为一个负数（例如-1），以便能够像上面那样检查中断号的有效性。
当你通过 `pci_request_region()` 或 `pci_request_regions()` 请求I/O端口或内存区域时，应该使用对应的函数 `pci_release_region()` 或 `pci_release_regions()` 来释放这些资源，如下所示：

  pci_release_regions(chip->pci);

如果你手动通过 `request_region()` 或 `request_mem_region()` 请求资源，你可以通过 `release_resource()` 函数来释放它。假设你将从 `request_region()` 返回的资源指针保存在 `chip->res_port` 中，那么释放过程如下：

  release_and_free_resource(chip->res_port);

别忘了在最后调用 `pci_disable_device()`。
最后，释放芯片特定的数据结构：

  kfree(chip);

我们没有实现上述的硬件禁用部分。如果你需要这样做，请注意析构函数可能在芯片初始化完成之前就被调用。最好有一个标志位来跳过硬件禁用，如果硬件尚未初始化的话。
当使用带有 `SNDRV_DEV_LOWLEVEL` 的 `snd_device_new()` 分配芯片数据时，其析构函数会在最后被调用。也就是说，可以确保所有其他组件如 PCM 和控制已经被释放。你不需要显式地停止 PCM 等组件，只需调用低级硬件停止即可。
管理内存映射区域几乎与管理I/O端口相同。你需要两个字段，如下所示：

  struct mychip {
          ...
unsigned long iobase_phys;
          void __iomem *iobase_virt;
  };

分配过程如下：

  err = pci_request_regions(pci, "My Chip");
  if (err < 0) {
          kfree(chip);
          return err;
  }
  chip->iobase_phys = pci_resource_start(pci, 0);
  chip->iobase_virt = ioremap(chip->iobase_phys,
                                      pci_resource_len(pci, 0));

相应的析构函数如下：

  static int snd_mychip_free(struct mychip *chip)
  {
          ...
if (chip->iobase_virt)
                  iounmap(chip->iobase_virt);
          ...
  }
```c
pci_release_regions(chip->pci);
...
}

当然，使用:c:func:`pci_iomap()`的现代方法也会使事情变得简单一些::

  err = pci_request_regions(pci, "My Chip");
  if (err < 0) {
          kfree(chip);
          return err;
  }
  chip->iobase_virt = pci_iomap(pci, 0, 0);

这需要在析构函数中与:c:func:`pci_iounmap()`配对
PCI 条目
-----------

到目前为止，一切顺利。让我们完成剩余的 PCI 相关工作。首先，我们需要为这个芯片组准备一个 `struct pci_device_id` 表。这是一个包含 PCI 厂商/设备 ID 号及其一些掩码的表。例如::

  static struct pci_device_id snd_mychip_ids[] = {
          { PCI_VENDOR_ID_FOO, PCI_DEVICE_ID_BAR,
            PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0, },
          ...
{ 0, }
  };
  MODULE_DEVICE_TABLE(pci, snd_mychip_ids);

`struct pci_device_id` 的前两个字段是厂商和设备 ID。如果你没有理由过滤匹配设备，可以将剩余字段留空。`struct pci_device_id` 的最后一个字段包含此条目的私有数据。你可以在这里指定任何值，例如，定义支持的设备 ID 的特定操作。在 intel8x0 驱动程序中可以看到这样的例子。
这个列表的最后一个条目是终止符。你必须指定这个全零条目。
然后，准备 `struct pci_driver` 记录::

  static struct pci_driver driver = {
          .name = KBUILD_MODNAME,
          .id_table = snd_mychip_ids,
          .probe = snd_mychip_probe,
          .remove = snd_mychip_remove,
  };

`probe` 和 `remove` 函数已经在前面的部分中定义过了。`name` 字段是此设备的名称字符串。请注意，该字符串中不得包含斜杠（“/”）。
最后，模块入口点::

  static int __init alsa_card_mychip_init(void)
  {
          return pci_register_driver(&driver);
  }

  static void __exit alsa_card_mychip_exit(void)
  {
          pci_unregister_driver(&driver);
  }

  module_init(alsa_card_mychip_init)
  module_exit(alsa_card_mychip_exit)

请注意，这些模块入口点带有 `__init` 和 `__exit` 前缀。
就是这样！

PCM 接口
==========

概述
-------

ALSA 的 PCM 中间层非常强大，每个驱动程序只需实现访问其硬件的低级函数即可。
要访问 PCM 层，你需要首先包含 `<sound/pcm.h>`。此外，如果访问与 `hw_param` 相关的某些函数，可能还需要包含 `<sound/pcm_params.h>`。
```
每个卡设备最多可以有四个PCM实例。一个PCM实例对应一个PCM设备文件。实例数量的限制仅来自于Linux设备号可用的位数。一旦使用64位设备号，我们将有更多的PCM实例可用。

一个PCM实例包括PCM播放和捕获流，每个PCM流又由一个或多个PCM子流组成。一些声卡支持多种播放功能。例如，emu10k1具有32个立体声音频子流的PCM播放功能。在这种情况下，每次打开时，通常会自动选择一个空闲的子流并将其打开。同时，当只有一个子流存在且已被打开时，后续的打开操作将根据文件打开模式要么阻塞要么返回`EAGAIN`错误。但是，在编写驱动程序时，您无需关心这些细节。PCM中间层会处理这些工作。

完整的代码示例
-----------------

下面的示例代码不包含任何硬件访问例程，只展示了如何构建PCM接口的基本框架：

```c
#include <sound/pcm.h>
...

/* 硬件定义 */
static struct snd_pcm_hardware snd_mychip_playback_hw = {
        .info = (SNDRV_PCM_INFO_MMAP |
                 SNDRV_PCM_INFO_INTERLEAVED |
                 SNDRV_PCM_INFO_BLOCK_TRANSFER |
                 SNDRV_PCM_INFO_MMAP_VALID),
        .formats = SNDRV_PCM_FMTBIT_S16_LE,
        .rates = SNDRV_PCM_RATE_8000_48000,
        .rate_min = 8000,
        .rate_max = 48000,
        .channels_min = 2,
        .channels_max = 2,
        .buffer_bytes_max = 32768,
        .period_bytes_min = 4096,
        .period_bytes_max = 32768,
        .periods_min = 1,
        .periods_max = 1024,
};

/* 硬件定义 */
static struct snd_pcm_hardware snd_mychip_capture_hw = {
        .info = (SNDRV_PCM_INFO_MMAP |
                 SNDRV_PCM_INFO_INTERLEAVED |
                 SNDRV_PCM_INFO_BLOCK_TRANSFER |
                 SNDRV_PCM_INFO_MMAP_VALID),
        .formats = SNDRV_PCM_FMTBIT_S16_LE,
        .rates = SNDRV_PCM_RATE_8000_48000,
        .rate_min = 8000,
        .rate_max = 48000,
        .channels_min = 2,
        .channels_max = 2,
        .buffer_bytes_max = 32768,
        .period_bytes_min = 4096,
        .period_bytes_max = 32768,
        .periods_min = 1,
        .periods_max = 1024,
};

/* 打开回调 */
static int snd_mychip_playback_open(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        struct snd_pcm_runtime *runtime = substream->runtime;

        runtime->hw = snd_mychip_playback_hw;
        /* 这里将完成更多的硬件初始化 */
        ...
        return 0;
}

/* 关闭回调 */
static int snd_mychip_playback_close(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        /* 这里将包含特定于硬件的代码 */
        ...
        return 0;
}

/* 打开回调 */
static int snd_mychip_capture_open(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        struct snd_pcm_runtime *runtime = substream->runtime;

        runtime->hw = snd_mychip_capture_hw;
        /* 这里将完成更多的硬件初始化 */
        ...
        return 0;
}

/* 关闭回调 */
static int snd_mychip_capture_close(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        /* 这里将包含特定于硬件的代码 */
        ...
        return 0;
}

/* hw_params 回调 */
static int snd_mychip_pcm_hw_params(struct snd_pcm_substream *substream,
                                    struct snd_pcm_hw_params *hw_params)
{
        /* 这里将包含特定于硬件的代码 */
        ...
        return 0;
}

/* hw_free 回调 */
static int snd_mychip_pcm_hw_free(struct snd_pcm_substream *substream)
{
        /* 这里将包含特定于硬件的代码 */
        ...
        return 0;
}
```
```c
返回 0;
}

/* 准备回调函数 */
static int snd_mychip_pcm_prepare(struct snd_pcm_substream *substream)
{
    struct mychip *chip = snd_pcm_substream_chip(substream);
    struct snd_pcm_runtime *runtime = substream->runtime;

    /* 使用当前配置设置硬件，例如... */
    mychip_set_sample_format(chip, runtime->format);
    mychip_set_sample_rate(chip, runtime->rate);
    mychip_set_channels(chip, runtime->channels);
    mychip_set_dma_setup(chip, runtime->dma_addr,
                         chip->buffer_size,
                         chip->period_size);
    return 0;
}

/* 触发回调函数 */
static int snd_mychip_pcm_trigger(struct snd_pcm_substream *substream,
                                  int cmd)
{
    switch (cmd) {
    case SNDRV_PCM_TRIGGER_START:
        /* 启动 PCM 引擎的操作 */
        ...
        break;
    case SNDRV_PCM_TRIGGER_STOP:
        /* 停止 PCM 引擎的操作 */
        ...
        break;
    default:
        return -EINVAL;
    }
}

/* 指针回调函数 */
static snd_pcm_uframes_t
snd_mychip_pcm_pointer(struct snd_pcm_substream *substream)
{
    struct mychip *chip = snd_pcm_substream_chip(substream);
    unsigned int current_ptr;

    /* 获取当前硬件指针 */
    current_ptr = mychip_get_hw_pointer(chip);
    return current_ptr;
}

/* 操作符 */
static struct snd_pcm_ops snd_mychip_playback_ops = {
    .open =        snd_mychip_playback_open,
    .close =       snd_mychip_playback_close,
    .hw_params =   snd_mychip_pcm_hw_params,
    .hw_free =     snd_mychip_pcm_hw_free,
    .prepare =     snd_mychip_pcm_prepare,
    .trigger =     snd_mychip_pcm_trigger,
    .pointer =     snd_mychip_pcm_pointer,
};

/* 操作符 */
static struct snd_pcm_ops snd_mychip_capture_ops = {
    .open =        snd_mychip_capture_open,
    .close =       snd_mychip_capture_close,
    .hw_params =   snd_mychip_pcm_hw_params,
    .hw_free =     snd_mychip_pcm_hw_free,
    .prepare =     snd_mychip_pcm_prepare,
    .trigger =     snd_mychip_pcm_trigger,
    .pointer =     snd_mychip_pcm_pointer,
};

/*
 * 录音部分定义省略...
*/

/* 创建一个 PCM 设备 */
static int snd_mychip_new_pcm(struct mychip *chip)
{
    struct snd_pcm *pcm;
    int err;

    err = snd_pcm_new(chip->card, "My Chip", 0, 1, 1, &pcm);
    if (err < 0)
        return err;
    pcm->private_data = chip;
    strcpy(pcm->name, "My Chip");
    chip->pcm = pcm;
    /* 设置操作符 */
    snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK,
                    &snd_mychip_playback_ops);
    snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE,
                    &snd_mychip_capture_ops);
    /* 预分配缓冲区 */
    /* 注意：这可能会失败 */
    snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV,
                                   &chip->pci->dev,
                                   64 * 1024, 64 * 1024);
    return 0;
}

PCM 构造函数
-------------

一个 PCM 实例由 :c:func:`snd_pcm_new()` 函数分配。最好为 PCM 创建一个构造函数，例如：

```c
static int snd_mychip_new_pcm(struct mychip *chip)
{
    struct snd_pcm *pcm;
    int err;

    err = snd_pcm_new(chip->card, "My Chip", 0, 1, 1, &pcm);
    if (err < 0)
        return err;
    pcm->private_data = chip;
    strcpy(pcm->name, "My Chip");
    chip->pcm = pcm;
    ..
    return 0;
}
```

:c:func:`snd_pcm_new()` 函数接受六个参数。第一个参数是指定给此 PCM 的声卡指针，第二个参数是标识字符串。
第三个参数（`index`，上面的 0）是新 PCM 的索引。它从零开始。如果你创建了多个 PCM 实例，则需要在此参数中指定不同的数字。例如，对于第二个 PCM 设备，`index = 1`。
第四个和第五个参数分别是回放和录音子流的数量。这里都使用 1。如果没有可用的回放或录音子流，则将 0 传递给相应的参数。
如果一个芯片支持多个回放或录音，则可以指定更多的数字，但在打开/关闭等回调中必须正确处理它们。当你需要知道你正在引用哪个子流时，可以通过如下方式从传递给每个回调的 `struct snd_pcm_substream` 数据中获取它：

```c
struct snd_pcm_substream *substream;
int index = substream->number;
```

创建 PCM 后，需要为每个 PCM 流设置操作符：

```c
snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK,
                &snd_mychip_playback_ops);
snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE,
                &snd_mychip_capture_ops);
```

操作符通常定义如下：

```c
static struct snd_pcm_ops snd_mychip_playback_ops = {
    .open =        snd_mychip_pcm_open,
    .close =       snd_mychip_pcm_close,
    .hw_params =   snd_mychip_pcm_hw_params,
    .hw_free =     snd_mychip_pcm_hw_free,
    .prepare =     snd_mychip_pcm_prepare,
    .trigger =     snd_mychip_pcm_trigger,
    .pointer =     snd_mychip_pcm_pointer,
};
```

所有回调函数都在“操作符”小节中描述。
```
设置操作符之后，您可能需要预分配缓冲区并设置托管分配模式。为此，只需调用以下函数：

```c
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV,
                               &chip->pci->dev,
                               64*1024, 64*1024);
```

这将默认分配一个最多为64KB的缓冲区。缓冲区管理的具体细节将在后面的章节《缓冲区和内存管理》中描述。此外，您可以在`pcm->info_flags`中设置一些额外信息。可用的值定义在`<sound/asound.h>`中的`SNDRV_PCM_INFO_XXX`，这些用于硬件定义（稍后描述）。如果您的声卡仅支持半双工，则可以这样指定：

```c
pcm->info_flags = SNDRV_PCM_INFO_HALF_DUPLEX;
```

... 析构函数？
-------------------

对于PCM实例的析构函数并不总是必需的。由于PCM设备会由中间层代码自动释放，因此您无需显式调用析构函数。如果内部创建了特殊记录并且需要释放它们，则需要设置析构函数到`pcm->private_free`：

```c
static void mychip_pcm_free(struct snd_pcm *pcm)
{
    struct mychip *chip = snd_pcm_chip(pcm);
    /* 释放您自己的数据 */
    kfree(chip->my_private_pcm_data);
    /* 进行其他处理 */
    ...
}

static int snd_mychip_new_pcm(struct mychip *chip)
{
    struct snd_pcm *pcm;
    ...
    /* 分配您自己的数据 */
    chip->my_private_pcm_data = kmalloc(...);
    /* 设置析构函数 */
    pcm->private_data = chip;
    pcm->private_free = mychip_pcm_free;
    ...
}
```

运行时指针 - PCM信息的宝箱
----------------------------------------------

当PCM子流被打开时，会分配一个PCM运行时实例，并将其分配给子流。此指针可以通过`substream->runtime`访问。此运行时指针包含控制PCM所需的大部分信息：hw_params和sw_params配置的副本、缓冲区指针、mmap记录、自旋锁等。运行时实例的定义可以在`<sound/pcm.h>`中找到。以下是该文件的相关部分：

```c
struct _snd_pcm_runtime {
    /* -- 状态 -- */
    struct snd_pcm_substream *trigger_master;
    snd_timestamp_t trigger_tstamp;     /* 触发时间戳 */
    int overrange;
    snd_pcm_uframes_t avail_max;
    snd_pcm_uframes_t hw_ptr_base;      /* 缓冲区重启时的位置 */
    snd_pcm_uframes_t hw_ptr_interrupt; /* 中断时的位置 */

    /* -- 硬件参数 -- */
    snd_pcm_access_t access;            /* 访问模式 */
    snd_pcm_format_t format;            /* SNDRV_PCM_FORMAT_* */
    snd_pcm_subformat_t subformat;      /* 子格式 */
    unsigned int rate;                  /* 频率（赫兹） */
    unsigned int channels;              /* 通道数 */
    snd_pcm_uframes_t period_size;      /* 周期大小 */
    unsigned int periods;               /* 周期数 */
    snd_pcm_uframes_t buffer_size;      /* 缓冲区大小 */
    unsigned int tick_time;             /* 打点时间 */
    snd_pcm_uframes_t min_align;        /* 格式对齐最小值 */
    size_t byte_align;
    unsigned int frame_bits;
    unsigned int sample_bits;
    unsigned int info;
    unsigned int rate_num;
    unsigned int rate_den;

    /* -- 软件参数 -- */
    struct timespec tstamp_mode;        /* mmap时间戳更新 */
    unsigned int period_step;
    unsigned int sleep_min;             /* 最小打点睡眠时间 */
    snd_pcm_uframes_t start_threshold;
    /*
     * 下面两个阈值可减轻播放缓冲区欠载；当hw_avail低于阈值时，触发相应动作：
     */
    snd_pcm_uframes_t stop_threshold;   /* - 停止播放 */
    snd_pcm_uframes_t silence_threshold;/* - 用静音填充缓冲区 */
    snd_pcm_uframes_t silence_size;     /* 静音填充的最大尺寸；当>=边界时，立即用静音填充播放区域 */
    snd_pcm_uframes_t boundary;         /* 指针绕回点 */

    /* 自动静音器的内部数据 */
    snd_pcm_uframes_t silence_start;    /* 静音区域的起始指针 */
    snd_pcm_uframes_t silence_filled;   /* 已用静音填充的大小 */

    snd_pcm_sync_id_t sync;             /* 硬件同步ID */

    /* -- 内存映射 -- */
    volatile struct snd_pcm_mmap_status *status;
    volatile struct snd_pcm_mmap_control *control;
    atomic_t mmap_count;

    /* -- 锁定/调度 -- */
    spinlock_t lock;
    wait_queue_head_t sleep;
    struct timer_list tick_timer;
    struct fasync_struct *fasync;

    /* -- 私有部分 -- */
    void *private_data;
    void (*private_free)(struct snd_pcm_runtime *runtime);

    /* -- 硬件描述 -- */
    struct snd_pcm_hardware hw;
    struct snd_pcm_hw_constraints hw_constraints;

    /* -- 定时器 -- */
    unsigned int timer_resolution;      /* 定时器分辨率 */

    /* -- DMA -- */
    unsigned char *dma_area;            /* DMA区域 */
    dma_addr_t dma_addr;                /* 物理总线地址（主CPU无法访问） */
    size_t dma_bytes;                   /* DMA区域大小 */

    struct snd_dma_buffer *dma_buffer_p; /* 分配的缓冲区 */

#if defined(CONFIG_SND_PCM_OSS) || defined(CONFIG_SND_PCM_OSS_MODULE)
    /* -- OSS相关 -- */
    struct snd_pcm_oss_runtime oss;
#endif
};
```

对于每个声卡驱动的操作符（回调），大多数这些记录应该是只读的。只有PCM中间层会更改/更新它们。例外是硬件描述（hw）、DMA缓冲区信息和私有数据。此外，如果您使用标准的托管缓冲区分配模式，则无需自己设置DMA缓冲区信息。

在下面的部分中，将解释重要的记录。
硬件描述
~~~~~~~~~~~~~~~~~~~~

硬件描述符（struct snd_pcm_hardware）包含了基本硬件配置的定义。最重要的是，您需要在`PCM打开回调`中定义这个描述符。请注意，运行时实例持有描述符的一个副本，而不是指向现有描述符的指针。也就是说，在打开回调中，您可以根据需要修改副本描述符（`runtime->hw`）。例如，如果某些芯片模型上的最大通道数仅为1，则仍然可以使用相同的硬件描述符并在稍后更改channels_max：

```c
struct snd_pcm_runtime *runtime = substream->runtime;
..
```
```c
// 常见定义
runtime->hw = snd_mychip_playback_hw;
if (chip->model == VERY_OLD_ONE)
    runtime->hw.channels_max = 1;
```

通常情况下，硬件描述符如下所示：

```c
static struct snd_pcm_hardware snd_mychip_playback_hw = {
        .info = (SNDRV_PCM_INFO_MMAP |
                 SNDRV_PCM_INFO_INTERLEAVED |
                 SNDRV_PCM_INFO_BLOCK_TRANSFER |
                 SNDRV_PCM_INFO_MMAP_VALID),
        .formats =          SNDRV_PCM_FMTBIT_S16_LE,
        .rates =            SNDRV_PCM_RATE_8000_48000,
        .rate_min =         8000,
        .rate_max =         48000,
        .channels_min =     2,
        .channels_max =     2,
        .buffer_bytes_max = 32768,
        .period_bytes_min = 4096,
        .period_bytes_max = 32768,
        .periods_min =      1,
        .periods_max =      1024,
};
```

- `info` 字段包含此 PCM 的类型和功能。位标志在 `<sound/asound.h>` 中定义为 `SNDRV_PCM_INFO_XXX`。至少，您需要指定是否支持 mmap 以及支持哪种交错格式。如果硬件支持 mmap，则应添加 `SNDRV_PCM_INFO_MMAP` 标志。如果硬件支持交错或非交错格式，则必须分别设置 `SNDRV_PCM_INFO_INTERLEAVED` 或 `SNDRV_PCM_INFO_NONINTERLEAVED` 标志。如果两者都支持，则可以同时设置。
  
  在上面的例子中，指定了 `MMAP_VALID` 和 `BLOCK_TRANSFER` 用于 OSS 的 mmap 模式。通常两者都会被设置。当然，只有当真正支持 mmap 时才会设置 `MMAP_VALID`。

- 其他可能的标志是 `SNDRV_PCM_INFO_PAUSE` 和 `SNDRV_PCM_INFO_RESUME`。`PAUSE` 位表示该 PCM 支持“暂停”操作，而 `RESUME` 位表示该 PCM 支持完整的“挂起/恢复”操作。如果设置了 `PAUSE` 标志，则下面的 `trigger` 回调函数必须处理相应的（暂停推送/释放）命令。即使没有设置 `RESUME` 标志，也可以定义挂起/恢复触发命令。详细信息请参阅 `Power Management` 部分。

- 如果 PCM 子流可以同步（通常是播放和捕获流的同步启动/停止），则可以设置 `SNDRV_PCM_INFO_SYNC_START`。在这种情况下，您需要在 `trigger` 回调函数中检查 PCM 子流的链表。这将在后面的章节中详细说明。

- `formats` 字段包含支持格式的位标志（`SNDRV_PCM_FMTBIT_XXX`）。如果硬件支持多种格式，则提供所有位或运算的结果。在上面的例子中，指定了带符号的 16 位小端格式。

- `rates` 字段包含支持采样率的位标志（`SNDRV_PCM_RATE_XXX`）。如果芯片支持连续采样率，则另外传递 `CONTINUOUS` 位。预定义的采样率位仅适用于典型采样率。如果您的芯片支持非常规采样率，则需要添加 `KNOT` 位并手动设置硬件约束（稍后解释）。

- `rate_min` 和 `rate_max` 定义最小和最大采样率。这应该与 `rates` 位相对应。

- `channels_min` 和 `channels_max` 定义最小和最大通道数。

- `buffer_bytes_max` 定义缓冲区的最大字节数。没有 `buffer_bytes_min` 字段，因为它可以从最小周期大小和最小周期数计算得出。同时，`period_bytes_min` 和 `period_bytes_max` 定义周期的最小和最大字节大小。

- `periods_max` 和 `periods_min` 定义缓冲区中的最大和最小区间数。
```
“周期”是一个术语，对应于OSS世界中的一个片段。周期定义了生成PCM中断的点。这一点强烈依赖于硬件。通常情况下，较小的周期大小会产生更多的中断，从而能够更及时地填充/排空缓冲区。在捕获的情况下，这个大小定义了输入延迟。另一方面，整个缓冲区大小定义了回放方向的输出延迟。

还有一个字段 `fifo_size`。这指定了硬件FIFO的大小，但目前既不被驱动程序使用，也不被alsa-lib使用。因此，您可以忽略这个字段。

PCM 配置
~~~~~~~~~

好的，让我们再次回到PCM运行时记录。运行时实例中最常引用的记录是PCM配置。应用程序通过alsa-lib发送`hw_params`数据后，PCM配置存储在运行时实例中。许多字段从`hw_params`和`sw_params`结构体中复制而来。例如，`format`字段保存应用程序选择的格式类型。该字段包含枚举值`SNDRV_PCM_FORMAT_XXX`。

需要注意的一点是，配置的缓冲区和周期大小以“帧”为单位存储在运行时中。在ALSA世界中，`1帧 = 通道数 * 样本大小`。对于帧和字节之间的转换，可以使用`frames_to_bytes()`和`bytes_to_frames()`辅助函数：

```c
period_bytes = frames_to_bytes(runtime, runtime->period_size);
```

此外，许多软件参数（sw_params）也以帧为单位存储。请检查字段的类型。`snd_pcm_uframes_t`表示无符号整数的帧，而`snd_pcm_sframes_t`表示带符号整数的帧。

DMA 缓冲区信息
~~~~~~~~~~~~~~

DMA缓冲区由以下四个字段定义：`dma_area`、`dma_addr`、`dma_bytes`和`dma_private`。`dma_area`持有缓冲区指针（逻辑地址）。您可以从此指针调用`memcpy()`。同时，`dma_addr`持有缓冲区的物理地址。当缓冲区为线性缓冲区时，此字段才指定。`dma_bytes`持有缓冲区的字节大小。`dma_private`用于ALSA DMA分配器。

如果您使用的是管理缓冲区分配模式或标准API函数`snd_pcm_lib_malloc_pages()`来分配缓冲区，则这些字段将由ALSA中间层设置，您不应自行更改它们。您可以读取它们，但不能写入。另一方面，如果您想自行分配缓冲区，则需要在hw_params回调中管理它。至少，`dma_bytes`是必须的。当缓冲区进行mmapped映射时，`dma_area`是必要的。如果您的驱动程序不支持mmap，则此字段不是必需的。`dma_addr`也是可选的。您可以随意使用`dma_private`。

运行状态
~~~~~~~~~

运行状态可以通过`runtime->status`访问。这是一个指向`snd_pcm_mmap_status`记录的指针。

例如，您可以通过`runtime->status->hw_ptr`获取当前DMA硬件指针。

DMA应用指针可以通过`runtime->control`访问，该指针指向一个`snd_pcm_mmap_control`记录。
然而，直接访问这个值是不推荐的。
私有数据
~~~~~~~~~~~~

你可以为子流分配一个记录，并将其存储在``runtime->private_data``中。通常，这在`PCM open 回调`_中完成。不要将此与``pcm->private_data``混用。``pcm->private_data``通常指向在创建PCM设备时静态分配的芯片实例，而``runtime->private_data``则指向在PCM打开回调中创建的动态数据结构。

```c
  static int snd_xxx_open(struct snd_pcm_substream *substream)
  {
          struct my_pcm_data *data;
          ...
          data = kmalloc(sizeof(*data), GFP_KERNEL);
          substream->runtime->private_data = data;
          ...
  }
```

分配的对象必须在`关闭回调`_中释放。
操作符
--------

好的，现在让我详细说明每个PCM回调（``ops``）。一般来说，每个回调在成功时必须返回0，或者在失败时返回一个负数错误代码，例如``-EINVAL``。为了选择合适的错误代码，建议检查内核其他部分在类似请求失败时返回的值。
每个回调函数至少需要一个参数，该参数包含一个struct snd_pcm_substream指针。要从给定的子流实例中获取芯片记录，可以使用以下宏：

```c
  int xxx(...) {
          struct mychip *chip = snd_pcm_substream_chip(substream);
          ...
}
```

该宏读取``substream->private_data``，这是``pcm->private_data``的一个副本。如果需要为每个PCM子流分配不同的数据记录，则可以覆盖前者。例如，cmi8330驱动程序为回放和捕获方向分配了不同的``private_data``，因为它为不同方向使用了两个不同的编解码器（SB-和AD兼容）。
PCM打开回调
~~~~~~~~~~~~~~~~~

```c
  static int snd_xxx_open(struct snd_pcm_substream *substream);
```

当PCM子流被打开时会调用此函数。
至少，在这里你需要初始化``runtime->hw``记录。通常，这样做：

```c
  static int snd_xxx_open(struct snd_pcm_substream *substream)
  {
          struct mychip *chip = snd_pcm_substream_chip(substream);
          struct snd_pcm_runtime *runtime = substream->runtime;

          runtime->hw = snd_mychip_playback_hw;
          return 0;
  }
```

其中``snd_mychip_playback_hw``是预定义的硬件描述。
你可以在本回调中分配私有数据，如“私有数据”_部分所述。
如果硬件配置需要更多的约束条件，请在此处设置硬件约束。更多详细信息请参见 Constraints_。

关闭回调
~~~~~~~~~~~~~~

::

  static int snd_xxx_close(struct snd_pcm_substream *substream);

很明显，当PCM子流被关闭时会调用这个函数。在 `open` 回调中分配的任何PCM子流私有实例将在此处释放：

  static int snd_xxx_close(struct snd_pcm_substream *substream)
  {
          ...
          kfree(substream->runtime->private_data);
          ...
  }

ioctl回调
~~~~~~~~~~~~~~

这用于处理对PCM ioctl的任何特殊调用。但通常你可以将其设置为NULL，那么PCM核心会调用通用ioctl回调函数 :c:func:`snd_pcm_lib_ioctl()`。如果你需要处理独特的通道信息设置或重置过程，可以在这里传递你自己的回调函数。

hw_params回调
~~~~~~~~~~~~~~~~~~~

::

  static int snd_xxx_hw_params(struct snd_pcm_substream *substream,
                               struct snd_pcm_hw_params *hw_params);

当应用程序设置了硬件参数（`hw_params`）时会调用此函数，即当缓冲区大小、周期大小、格式等为PCM子流定义好后会调用一次。
许多硬件设置应该在这个回调中完成，包括缓冲区的分配。
要初始化的参数可以通过 :c:func:`params_xxx()` 宏获取。
当你选择子流的管理缓冲区分配模式时，在这个回调被调用之前缓冲区已经分配好了。或者，你可以调用下面的帮助函数来分配缓冲区：

  snd_pcm_lib_malloc_pages(substream, params_buffer_bytes(hw_params));

:c:func:`snd_pcm_lib_malloc_pages()` 只有在DMA缓冲区预先分配的情况下可用。更多详细信息请参见 `Buffer Types`_ 部分。

请注意，这个回调和 `prepare` 回调可能会在初始化过程中被多次调用。例如，OSS仿真可能在每次通过其ioctl更改时调用这些回调。
因此，你需要小心不要多次分配相同的缓冲区，这将导致内存泄漏！多次调用上面的辅助函数是安全的。如果缓冲区已经分配，则它会自动释放之前的缓冲区。

另一个需要注意的是，默认情况下此回调是非原子的（可调度的），即当没有设置 `nonatomic` 标志时。这一点很重要，因为 `trigger` 回调是原子的（不可调度的）。也就是说，在 `trigger` 回调中无法使用互斥锁或任何与调度相关的函数。详情请参见 原子性_ 小节。

hw_free 回调
~~~~~~~~~~~~~

::

  static int snd_xxx_hw_free(struct snd_pcm_substream *substream);

此回调用于释放通过 `hw_params` 分配的资源。
此函数总是在关闭回调之前被调用。
此外，此回调也可能被多次调用。确保跟踪每项资源是否已释放。
如果你选择了PCM子流的管理缓冲区分配模式，则在调用此回调后，分配的PCM缓冲区将自动释放。否则，你需要手动释放缓冲区。通常，如果缓冲区是从预分配池中分配的，你可以使用标准API函数 `snd_pcm_lib_malloc_pages()` 来释放，例如：

  snd_pcm_lib_free_pages(substream);

prepare 回调
~~~~~~~~~~~~~

::

  static int snd_xxx_prepare(struct snd_pcm_substream *substream);

此回调在PCM“准备”时被调用。你可以在这里设置格式类型、采样率等。与 `hw_params` 的不同之处在于，`prepare` 回调会在每次调用 `snd_pcm_prepare()` 时被调用，例如在恢复欠溢出之后。

注意此回调是非原子的。你可以在该回调中安全地使用与调度相关的函数。
在此及以下的回调中，你可以通过运行时记录 `substream->runtime` 访问相关值。例如，要获取当前的速率、格式或通道数，可以访问 `runtime->rate`、`runtime->format` 或 `runtime->channels`。分配的缓冲区的物理地址设置为 `runtime->dma_area`。缓冲区和周期大小分别在 `runtime->buffer_size` 和 `runtime->period_size` 中。
请注意，此回调在每次设置时也会被多次调用。

trigger 回调
~~~~~~~~~~~~~

::

  static int snd_xxx_trigger(struct snd_pcm_substream *substream, int cmd);

此回调在PCM启动、停止或暂停时被调用。
操作在第二个参数中指定，即在`<sound/pcm.h>`中定义的`SNDRV_PCM_TRIGGER_XXX`。至少，此回调函数中必须定义`START`和`STOP`命令：

```c
switch (cmd) {
case SNDRV_PCM_TRIGGER_START:
        /* 执行启动PCM引擎的操作 */
        break;
case SNDRV_PCM_TRIGGER_STOP:
        /* 执行停止PCM引擎的操作 */
        break;
default:
        return -EINVAL;
}
```

如果PCM支持暂停操作（在硬件表的信息字段中给出），则必须在此处理`PAUSE_PUSH`和`PAUSE_RELEASE`命令。前者是暂停PCM的命令，后者是重新启动PCM的命令。

如果PCM支持挂起/恢复操作，无论是完全还是部分支持，都必须处理`SUSPEND`和`RESUME`命令。当电源管理状态发生变化时会发出这些命令。显然，`SUSPEND`和`RESUME`命令分别挂起和恢复PCM子流，通常它们分别等同于`STOP`和`START`命令。详细信息请参见`Power Management`_部分。

如前所述，默认情况下此回调函数是原子性的，除非设置了`nonatomic`标志，并且不能调用可能会休眠的函数。`trigger`回调函数应尽可能简洁，仅真正触发DMA。其他初始化工作应在`hw_params`和`prepare`回调函数中适当完成。

同步停止回调
~~~~~~~~~~~~~

```c
static int snd_xxx_sync_stop(struct snd_pcm_substream *substream);
```

此回调函数是可选的，可以传递NULL。它在PCM核心停止流之后、通过`prepare`、`hw_params`或`hw_free`改变流状态之前被调用。

由于中断处理程序可能仍在等待中，在进行下一步之前需要等待待处理的任务完成；否则可能会因为资源冲突或访问已释放的资源而导致崩溃。典型的行为是在这里调用一个同步函数，例如：c:func:`synchronize_irq()`。

对于大多数只需要调用:c:func:`synchronize_irq()`的驱动程序，有一个更简单的设置方法。

保持`sync_stop` PCM回调为NULL，驱动程序可以在请求中断后将`card->sync_irq`字段设置为返回的中断号。然后PCM核心将使用给定的中断号适当调用:c:func:`synchronize_irq()`。

如果中断处理程序由卡的析构函数释放，则无需清除`card->sync_irq`，因为卡本身正在被释放。

因此，通常你只需在驱动代码中添加一行来分配`card->sync_irq`，除非驱动程序重新获取中断。当驱动程序动态地释放和重新获取中断（例如为了挂起/恢复）时，需要适当地清除并重新设置`card->sync_irq`。
### 指针回调

```
static snd_pcm_uframes_t snd_xxx_pointer(struct snd_pcm_substream *substream)
```

此回调函数在PCM中间层查询当前硬件位置时被调用。返回的位置必须以帧为单位，范围从0到`buffer_size - 1`。

此回调通常由PCM中间层的缓冲区更新例程调用，该例程是在中断例程调用`snd_pcm_period_elapsed()`时触发的。然后PCM中间层会更新位置，并计算可用空间，唤醒睡眠中的poll线程等。
此回调默认是原子性的。

### 复制和填充静音操作

这些回调不是强制性的，在大多数情况下可以省略。
当硬件缓冲区不能位于常规内存空间中时，需要使用这些回调。有些芯片有自己的硬件缓冲区，无法映射。在这种情况下，你需要手动将数据从内存缓冲区传输到硬件缓冲区。或者，如果缓冲区在物理和虚拟内存空间上都是非连续的，也必须定义这些回调。
如果定义了这两个回调，复制和设置静音操作将由它们完成。详细内容将在后面的“缓冲区和内存管理”部分描述。

### 确认回调

此回调也不是强制性的。
此回调在读写操作中更新`appl_ptr`时被调用。像`emu10k1-fx`和`cs46xx`这样的驱动程序需要跟踪内部缓冲区中的当前`appl_ptr`，这个回调仅适用于这种目的。
回调函数可以返回0或负错误值。当返回值为`-EPIPE`时，PCM核心将其视为缓冲区XRUN，并自动将状态更改为`SNDRV_PCM_STATE_XRUN`。
此回调默认是原子性的。

### 分页回调

此回调也是可选的。mmap调用此回调来获取分页错误地址。
对于标准的SG缓冲区或vmalloc缓冲区，你不需要特殊的回调。因此，此回调应很少使用。
mmap 回调
~~~~~~~~~~~~~

这是另一个可选的回调，用于控制 mmap 行为。
当定义了这个回调时，PCM 核心会在页面被内存映射时调用此回调，而不是使用标准的辅助函数。
如果你需要特殊的处理（由于某些架构或设备特定的问题），你可以在这里按需实现所有内容。

PCM 中断处理器
---------------------

PCM 相关剩余的部分是 PCM 中断处理器。在声卡驱动中，PCM 中断处理器的作用是更新缓冲区位置，并且当缓冲区位置越过指定的周期边界时通知 PCM 中间层。为此，你需要调用 `snd_pcm_period_elapsed()` 函数。

有几种方式声卡可以生成中断：
中断在周期（片段）边界
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

这是最常见的类型：硬件在每个周期边界生成一个中断。在这种情况下，你可以在每次中断时调用 `snd_pcm_period_elapsed()`。

`snd_pcm_period_elapsed()` 需要子流指针作为参数。因此，你需要保持子流指针在芯片实例中的可访问性。例如，在芯片记录中定义一个 `substream` 字段来保存当前运行的子流指针，并在 `open` 回调中设置该指针值（并在 `close` 回调中重置）。

如果你在中断处理器中获取了一个自旋锁，并且该锁也在其他 PCM 回调中使用，则在调用 `snd_pcm_period_elapsed()` 之前必须释放该锁，因为 `snd_pcm_period_elapsed()` 在内部会调用其他 PCM 回调。

典型的代码如下所示：

```c
static irqreturn_t snd_mychip_interrupt(int irq, void *dev_id)
{
    struct mychip *chip = dev_id;
    spin_lock(&chip->lock);
    ...

    if (pcm_irq_invoked(chip)) {
        /* 调用更新器，调用前先解锁 */
        spin_unlock(&chip->lock);
        snd_pcm_period_elapsed(chip->substream);
        spin_lock(&chip->lock);
        /* 如果需要，确认中断 */
    }
    ...
}
```

这样，你就可以正确地处理 PCM 中断，并确保锁的安全使用。
```c
// 释放自旋锁并返回中断处理状态
spin_unlock(&chip->lock);
return IRQ_HANDLED;
}

// 当设备能够检测到缓冲区欠载/过载时，驱动程序可以通过调用snd_pcm_stop_xrun()函数来通知PCM核心XRUN状态。此函数会停止流并将PCM状态设置为SNDRV_PCM_STATE_XRUN。注意，该函数必须在PCM流锁之外调用，因此不能从原子回调中调用。
高频率定时器中断
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当硬件不在周期边界生成中断而是在固定的时间间隔内触发定时器中断（例如es1968或ymfpci驱动程序）时会发生这种情况。此时，需要在每次中断时检查当前硬件位置，并累加已处理的样本长度。当累积的大小超过周期大小时，调用snd_pcm_period_elapsed()函数并重置累加器。
典型的代码如下所示：

static irqreturn_t snd_mychip_interrupt(int irq, void *dev_id)
{
    struct mychip *chip = dev_id;
    spin_lock(&chip->lock);
    ...
    if (pcm_irq_invoked(chip)) {
        unsigned int last_ptr, size;
        // 获取当前硬件指针（以帧为单位）
        last_ptr = get_hw_ptr(chip);
        // 计算自上次更新以来处理的帧数
        if (last_ptr < chip->last_ptr)
            size = runtime->buffer_size + last_ptr - chip->last_ptr;
        else
            size = last_ptr - chip->last_ptr;
        // 记住最后更新的位置
        chip->last_ptr = last_ptr;
        // 累加大小
        chip->size += size;
        // 超过周期边界？
        if (chip->size >= runtime->period_size) {
            // 重置累加器
            chip->size %= runtime->period_size;
            // 调用更新函数
            spin_unlock(&chip->lock);
            snd_pcm_period_elapsed(substream);
            spin_lock(&chip->lock);
        }
        // 必要时确认中断
    }
    ...
    spin_unlock(&chip->lock);
    return IRQ_HANDLED;
}

// 关于调用snd_pcm_period_elapsed()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

无论哪种情况，即使超过了一个周期，也不需要多次调用snd_pcm_period_elapsed()。只需调用一次即可。PCM层会检查当前硬件指针并更新到最新状态。
原子性
-------

内核编程中最重要（同时也是最难调试的）问题之一是竞态条件。在Linux内核中，通常通过自旋锁、互斥锁或信号量来避免竞态条件。一般来说，如果中断处理程序中可能发生竞态条件，则必须使用原子方式管理，并且需要使用自旋锁来保护关键部分。如果关键部分不在中断处理程序代码中，并且可以接受相对长的执行时间，则应使用互斥锁或信号量代替。
如前所述，一些PCM回调是原子的，一些则不是。例如，“hw_params”回调是非原子的，而“trigger”回调是原子的。这意味着后者已经在PCM中间层持有的自旋锁下被调用，即PCM流锁。请在选择回调中的锁定方案时考虑这种原子性。
在原子回调中，不能使用可能调用schedule()或进入sleep()的函数。互斥锁和信号量可能会导致睡眠，因此不能在原子回调（例如“trigger”回调）中使用。要在这样的回调中实现延迟，请使用udelay()或mdelay()。
所有三个原子回调（trigger、pointer和ack）都在本地中断禁用的情况下被调用。
```
然而，可以请求所有的PCM操作是非原子的。
这假设所有调用点都在非原子上下文中。例如，函数 :c:func:`snd_pcm_period_elapsed()` 通常从中断处理程序中调用。但是，如果你将驱动程序设置为使用线程化的中断处理程序，则此调用也可以在非原子上下文中进行。在这种情况下，你可以在创建 `snd_pcm` 对象后设置其 `nonatomic` 字段。当设置了这个标志时，PCM核心内部会使用互斥锁和读写信号量（mutex 和 rwsem）而不是自旋锁和读写锁（spin 和 rwlocks），从而可以在非原子上下文中安全地调用所有PCM函数。

此外，在某些情况下，你可能需要在原子上下文中调用 :c:func:`snd_pcm_period_elapsed()`（例如，在“ack”或其他回调期间周期结束）。为此，有一个变体可以在PCM流锁内调用 :c:func:`snd_pcm_period_elapsed_under_stream_lock()`。

约束
------------

由于物理限制，硬件并非无限可配置。这些限制通过设置约束来表达。例如，为了将采样率限制为一些支持的值，可以使用 :c:func:`snd_pcm_hw_constraint_list()`。你需要在打开回调中调用该函数：

```c
static unsigned int rates[] = {4000, 10000, 22050, 44100};
static struct snd_pcm_hw_constraint_list constraints_rates = {
    .count = ARRAY_SIZE(rates),
    .list = rates,
    .mask = 0,
};

static int snd_mychip_pcm_open(struct snd_pcm_substream *substream)
{
    int err;
    ...
    err = snd_pcm_hw_constraint_list(substream->runtime, 0,
                                     SNDRV_PCM_HW_PARAM_RATE,
                                     &constraints_rates);
    if (err < 0)
        return err;
    ...
}
```

有许多不同的约束。查看 `sound/pcm.h` 获取完整的列表。你甚至可以定义自己的约束规则。例如，假设 `my_chip` 只有在格式为 `S16_LE` 时才支持单通道子流，否则它支持 `struct snd_pcm_hardware` 中指定的任何格式（或任何其他约束列表）。你可以构建这样的规则：

```c
static int hw_rule_channels_by_format(struct snd_pcm_hw_params *params,
                                      struct snd_pcm_hw_rule *rule)
{
    struct snd_interval *c = hw_param_interval(params,
                                               SNDRV_PCM_HW_PARAM_CHANNELS);
    struct snd_mask *f = hw_param_mask(params, SNDRV_PCM_HW_PARAM_FORMAT);
    struct snd_interval ch;

    snd_interval_any(&ch);
    if (f->bits[0] == SNDRV_PCM_FMTBIT_S16_LE) {
        ch.min = ch.max = 1;
        ch.integer = 1;
        return snd_interval_refine(c, &ch);
    }
    return 0;
}
```

然后你需要调用该函数添加你的规则：

```c
snd_pcm_hw_rule_add(substream->runtime, 0, SNDRV_PCM_HW_PARAM_CHANNELS,
                    hw_rule_channels_by_format, NULL,
                    SNDRV_PCM_HW_PARAM_FORMAT, -1);
```

规则函数在应用程序设置PCM格式时被调用，并相应地细化通道数。但应用程序可能会在设置格式之前设置通道数。因此你也需要定义逆向规则：

```c
static int hw_rule_format_by_channels(struct snd_pcm_hw_params *params,
                                      struct snd_pcm_hw_rule *rule)
{
    struct snd_interval *c = hw_param_interval(params,
                                               SNDRV_PCM_HW_PARAM_CHANNELS);
    struct snd_mask *f = hw_param_mask(params, SNDRV_PCM_HW_PARAM_FORMAT);
    struct snd_mask fmt;

    snd_mask_any(&fmt);    /* 初始化结构体 */
    if (c->min < 2) {
        fmt.bits[0] &= SNDRV_PCM_FMTBIT_S16_LE;
        return snd_mask_refine(f, &fmt);
    }
    return 0;
}
```

… 并在打开回调中调用：

```c
snd_pcm_hw_rule_add(substream->runtime, 0, SNDRV_PCM_HW_PARAM_FORMAT,
                    hw_rule_format_by_channels, NULL,
                    SNDRV_PCM_HW_PARAM_CHANNELS, -1);
```

硬件约束的一个典型用途是使缓冲区大小与周期大小对齐。默认情况下，ALSA PCM核心不强制缓冲区大小与周期大小对齐。例如，可能存在256字节周期和999字节缓冲区的组合。
然而，许多设备芯片要求缓冲区是周期的倍数。在这种情况下，可以调用 :c:func:`snd_pcm_hw_constraint_integer()` 来设置 `SNDRV_PCM_HW_PARAM_PERIODS`：

```c
snd_pcm_hw_constraint_integer(substream->runtime,
                              SNDRV_PCM_HW_PARAM_PERIODS);
```

这确保了周期数为整数，因此缓冲区大小与周期大小对齐。
硬件约束是一个非常强大的机制，用于定义首选的PCM配置，并且有许多相关的辅助函数。
我在这里不会提供更多的细节，相反，我想说的是，“Luke，使用源头。”

控制接口
=========

概述
-----
控制接口被广泛用于许多开关、滑块等，这些都可以从用户空间访问。它最重要的用途是混音器接口。换句话说，自ALSA 0.9.x版本以来，所有的混音器功能都是在控制内核API上实现的。ALSA有一个定义明确的AC97控制模块。如果你的芯片只支持AC97而没有其他功能，你可以跳过这一节。控制API在`<sound/control.h>`中定义。如果你想添加自己的控制，请包含这个文件。

控制的定义
----------
要创建一个新的控制，你需要定义以下三个回调函数：`info`、`get`和`put`。然后，定义一个`struct snd_kcontrol_new`记录，如下所示：

```c
static struct snd_kcontrol_new my_control = {
        .iface = SNDRV_CTL_ELEM_IFACE_MIXER,
        .name = "PCM Playback Switch",
        .index = 0,
        .access = SNDRV_CTL_ELEM_ACCESS_READWRITE,
        .private_value = 0xffff,
        .info = my_control_info,
        .get = my_control_get,
        .put = my_control_put
};
```

`iface`字段指定了控制类型，`SNDRV_CTL_ELEM_IFACE_XXX`，通常是`MIXER`。对于不属于混音器逻辑部分的全局控制，请使用`CARD`。如果控制与声卡上的某个特定设备密切相关，请使用`HWDEP`、`PCM`、`RAWMIDI`、`TIMER`或`SEQUENCER`，并通过`device`和`subdevice`字段指定设备编号。
`name`是名称标识字符串。自ALSA 0.9.x版本以来，控制名称非常重要，因为其作用可以通过名称分类。有预定义的标准控制名称。详细信息将在`控制名称`_子节中描述。
`index`字段保存了此控制的索引号。如果有多个具有相同名称的不同控制，则可以通过索引号来区分它们。当卡上有多个编解码器时就是这种情况。如果索引为零，可以省略上述定义。

`access`字段包含此控制的访问类型。请在此处给出`SNDRV_CTL_ELEM_ACCESS_XXX`位掩码的组合。详细信息将在`访问标志`_子节中解释。
`private_value`字段包含此记录的任意长整数值。当使用通用`info`、`get`和`put`回调时，可以通过此字段传递一个值。如果需要几个小数字，可以在位上组合它们。或者，也可以在此字段中存储某个记录的指针（转换为无符号长整型）。
`tlv`字段可用于提供关于控制的元数据；详见`元数据`_子节。
其余三个是`控制回调`_

控制名称
---------
定义控制名称有一些标准。一个控制通常由三部分组成，即“SOURCE DIRECTION FUNCTION”。
第一个参数，“SOURCE”，指定了控制的来源，是一个字符串，例如“Master”、“PCM”、“CD”和“Line”。有许多预定义的来源。

第二个参数，“DIRECTION”，根据控制的方向，是以下字符串之一：“Playback”（播放）、“Capture”（捕获）、“Bypass Playback”（旁路播放）和“Bypass Capture”（旁路捕获）。或者可以省略，这意味着同时支持播放和捕获方向。

第三个参数，“FUNCTION”，根据控制的功能，是以下字符串之一：“Switch”（开关）、“Volume”（音量）和“Route”（路由）。

因此，控制名称的例子包括“Master Capture Switch”（主控捕获开关）或“PCM Playback Volume”（PCM播放音量）。

有一些例外情况：

全局捕获和播放
~~~~~~~~~~~~~~

“Capture Source”（捕获源）、“Capture Switch”（捕获开关）和“Capture Volume”（捕获音量）用于全局捕获（输入）源、开关和音量。类似地，“Playback Switch”（播放开关）和“Playback Volume”（播放音量）用于全局输出增益开关和音量。

音调控制
~~~~~~~~~

音调控制的开关和音量指定为“Tone Control - XXX”的形式，例如“Tone Control - Switch”（音调控制开关）、“Tone Control - Bass”（低音控制）和“Tone Control - Center”（中置控制）。

3D 控制
~~~~~~~

3D 控制的开关和音量指定为“3D Control - XXX”的形式，例如“3D Control - Switch”（3D控制开关）、“3D Control - Center”（3D中心控制）和“3D Control - Space”（3D空间控制）。

麦克风增强
~~~~~~~~~~

麦克风增强开关设置为“Mic Boost”（麦克风增强）或“Mic Boost (6dB)”（麦克风增强6分贝）。

更多详细信息可以在`Documentation/sound/designs/control-names.rst`中找到。

访问标志
------------

访问标志是一个位掩码，指定了给定控制的访问类型。默认的访问类型是`SNDRV_CTL_ELEM_ACCESS_READWRITE`，这意味着允许对该控制进行读写操作。当访问标志被省略（即等于0）时，默认视为`READWRITE`访问。
当控件为只读时，传递 `SNDRV_CTL_ELEM_ACCESS_READ`。在这种情况下，您不需要定义 `put` 回调函数。

类似地，当控件为写入专用（尽管这是很少见的情况）时，您可以使用 `WRITE` 标志，并且不需要 `get` 回调函数。

如果控件的值经常变化（例如 VU 计），应设置 `VOLATILE` 标志。这意味着控件可能会在没有 `变更通知` 的情况下发生变化。应用程序应该持续轮询此类控件。

当控件可能被更新，但目前对任何事情都没有影响时，设置 `INACTIVE` 标志可能是合适的。例如，在没有任何 PCM 设备打开的情况下，PCM 控件应该是不活跃的。

有 `LOCK` 和 `OWNER` 标志来更改写权限。

控件回调
----------

信息回调
~~~~~~~~~~~~~

`info` 回调用于获取有关此控件的详细信息。必须存储给定的 struct `snd_ctl_elem_info` 对象的值。例如，对于具有单个元素的布尔控件：

```c
static int snd_myctl_mono_info(struct snd_kcontrol *kcontrol,
                              struct snd_ctl_elem_info *uinfo)
{
        uinfo->type = SNDRV_CTL_ELEM_TYPE_BOOLEAN;
        uinfo->count = 1;
        uinfo->value.integer.min = 0;
        uinfo->value.integer.max = 1;
        return 0;
}
```

`type` 字段指定了控件的类型。类型包括 `BOOLEAN`、`INTEGER`、`ENUMERATED`、`BYTES`、`IEC958` 和 `INTEGER64`。`count` 字段指定了此控件中的元素数量。例如，立体声音量会有 `count = 2`。`value` 字段是一个联合体，存储的值取决于类型。布尔类型和整数类型是相同的。

枚举类型与其他类型有所不同。您需要为选定项索引设置字符串：

```c
static int snd_myctl_enum_info(struct snd_kcontrol *kcontrol,
                          struct snd_ctl_elem_info *uinfo)
{
        static char *texts[4] = {
                "First", "Second", "Third", "Fourth"
        };
        uinfo->type = SNDRV_CTL_ELEM_TYPE_ENUMERATED;
        uinfo->count = 1;
        uinfo->value.enumerated.items = 4;
        if (uinfo->value.enumerated.item > 3)
                uinfo->value.enumerated.item = 3;
        strcpy(uinfo->value.enumerated.name,
               texts[uinfo->value.enumerated.item]);
        return 0;
}
```

上述回调可以使用辅助函数 `snd_ctl_enum_info()` 进行简化，最终代码如下所示（您可以将 `ARRAY_SIZE(texts)` 代替 4 作为第三个参数；这取决于个人喜好。）

```c
static int snd_myctl_enum_info(struct snd_kcontrol *kcontrol,
                          struct snd_ctl_elem_info *uinfo)
{
        static char *texts[4] = {
                "First", "Second", "Third", "Fourth"
        };
        return snd_ctl_enum_info(uinfo, 1, 4, texts);
}
```

为了方便起见，提供了一些常用的信息回调：`snd_ctl_boolean_mono_info()` 和 `snd_ctl_boolean_stereo_info()`。显然，前者是一个单声道布尔项的信息回调，类似于上面的 `snd_myctl_mono_info()`，而后者是一个立体声布尔项的信息回调。

获取回调
~~~~~~~~~~~~

此回调用于读取控件的当前值，以便返回给用户空间。

例如：

```c
static int snd_myctl_get(struct snd_kcontrol *kcontrol,
                         struct snd_ctl_elem_value *ucontrol)
{
        struct mychip *chip = snd_kcontrol_chip(kcontrol);
        ucontrol->value.integer.value[0] = get_some_value(chip);
        return 0;
}
```

`value` 字段取决于控件的类型以及信息回调。例如，sb 驱动程序使用此字段存储寄存器偏移量、位移和位掩码。`private_value` 字段设置如下：

```c
.private_value = reg | (shift << 16) | (mask << 24)
```

并在回调中检索：

```c
static int snd_sbmixer_get_single(struct snd_kcontrol *kcontrol,
                                  struct snd_ctl_elem_value *ucontrol)
{
        int reg = kcontrol->private_value & 0xff;
        int shift = (kcontrol->private_value >> 16) & 0xff;
        int mask = (kcontrol->private_value >> 24) & 0xff;
        ...
```
在“get”回调函数中，如果控件包含多个元素（即 `count > 1`），则必须填充所有元素。在上面的例子中，我们只填充了一个元素（`value.integer.value[0]`），因为假定 `count = 1`。

put 回调
~~~~~~~~~~~~

此回调函数用于写入来自用户空间的值。例如：

```c
static int snd_myctl_put(struct snd_kcontrol *kcontrol,
                         struct snd_ctl_elem_value *ucontrol)
{
    struct mychip *chip = snd_kcontrol_chip(kcontrol);
    int changed = 0;
    if (chip->current_value != ucontrol->value.integer.value[0]) {
        change_current_value(chip, ucontrol->value.integer.value[0]);
        changed = 1;
    }
    return changed;
}
```

如上所述，如果值发生了变化，则必须返回 1。如果值没有变化，则返回 0。如果发生致命错误，则像往常一样返回一个负的错误代码。
与“get”回调类似，当控件包含多个元素时，在此回调中也必须评估所有元素。

回调不是原子操作
~~~~~~~~~~~~~~~~~~~~~~~~

这三个回调都不是原子操作。

控件构造器
-------------------

当一切都准备就绪后，最终我们可以创建一个新的控件。为了创建控件，需要调用两个函数：`:c:func:`snd_ctl_new1()` 和 `:c:func:`snd_ctl_add()`。
最简单的方式如下：

```c
err = snd_ctl_add(card, snd_ctl_new1(&my_control, chip));
if (err < 0)
    return err;
```

其中 `my_control` 是上面定义的 `struct snd_kcontrol_new` 对象，`chip` 是要传递给 `kcontrol->private_data` 的对象指针，可以在回调中引用它。
`:c:func:`snd_ctl_new1()` 分配一个新的 `struct snd_kcontrol` 实例，而 `:c:func:`snd_ctl_add()` 将给定的控件组件分配给声卡。

更改通知
-------------------

如果你需要在中断例程中更改和更新控件，可以调用 `:c:func:`snd_ctl_notify()`。例如：

```c
snd_ctl_notify(card, SNDRV_CTL_EVENT_MASK_VALUE, id_pointer);
```

此函数接受声卡指针、事件掩码和要通知的控件 ID 指针。事件掩码指定了通知的类型，例如，在上面的例子中，通知了控件值的变化。ID 指针是指向 `struct snd_ctl_elem_id` 的指针。你可以在 `es1938.c` 或 `es1968.c` 中找到关于硬件音量中断的一些示例。

元数据
--------

为了提供混音器控件的 dB 值信息，可以使用 `sound/tlv.h` 中的一个 `DECLARE_TLV_xxx` 宏来定义一个包含这些信息的变量，并将 `tlv.p` 字段设置为指向这个变量，并在 `access` 字段中包含 `SNDRV_CTL_ELEM_ACCESS_TLV_READ` 标志；例如：

```c
static DECLARE_TLV_DB_SCALE(db_scale_my_control, -4050, 150, 0);

static struct snd_kcontrol_new my_control = {
        ..
```
```cpp
.access = SNDRV_CTL_ELEM_ACCESS_READWRITE |
           SNDRV_CTL_ELEM_ACCESS_TLV_READ,
...
.tlv.p = db_scale_my_control,
};
```

`:c:func:`DECLARE_TLV_DB_SCALE()` 宏定义了关于混频器控制的信息，其中控制值的每个步骤会以恒定的分贝数改变分贝值。第一个参数是待定义变量的名称。第二个参数是最小值，单位为 0.01 分贝。第三个参数是步长，单位为 0.01 分贝。如果最小值实际使控制静音，则将第四个参数设置为 1。

`:c:func:`DECLARE_TLV_DB_LINEAR()` 宏定义了关于混频器控制的信息，其中控制值线性影响输出。第一个参数是待定义变量的名称。第二个参数是最小值，单位为 0.01 分贝。第三个参数是最大值，单位为 0.01 分贝。如果最小值使控制静音，则将第二个参数设置为 `TLV_DB_GAIN_MUTE`。

### AC97 编码器 API
#### 概述

ALSA 的 AC97 编码器层是一个定义明确的层，你不需要编写很多代码来控制它。只需要编写低级控制例程即可。AC97 编码器 API 在 `<sound/ac97_codec.h>` 中定义。

#### 完整代码示例

```cpp
struct mychip {
    ...
    struct snd_ac97 *ac97;
    ...
};

static unsigned short snd_mychip_ac97_read(struct snd_ac97 *ac97, unsigned short reg)
{
    struct mychip *chip = ac97->private_data;
    ...
    // 从编解码器读取寄存器值
    return the_register_value;
}

static void snd_mychip_ac97_write(struct snd_ac97 *ac97, unsigned short reg, unsigned short val)
{
    struct mychip *chip = ac97->private_data;
    ...
    // 将给定的寄存器值写入编解码器
}

static int snd_mychip_ac97(struct mychip *chip)
{
    struct snd_ac97_bus *bus;
    struct snd_ac97_template ac97;
    int err;
    static struct snd_ac97_bus_ops ops = {
        .write = snd_mychip_ac97_write,
        .read = snd_mychip_ac97_read,
    };

    err = snd_ac97_bus(chip->card, 0, &ops, NULL, &bus);
    if (err < 0)
        return err;
    memset(&ac97, 0, sizeof(ac97));
    ac97.private_data = chip;
    return snd_ac97_mixer(bus, &ac97, &chip->ac97);
}
```

#### AC97 构造函数

要创建一个 AC97 实例，首先调用 `:c:func:`snd_ac97_bus()` 并传入一个包含回调函数的 `ac97_bus_ops_t` 结构体：

```cpp
struct snd_ac97_bus *bus;
static struct snd_ac97_bus_ops ops = {
    .write = snd_mychip_ac97_write,
    .read = snd_mychip_ac97_read,
};

snd_ac97_bus(card, 0, &ops, NULL, &pbus);
```

这个总线记录将在所有相关的 AC97 实例中共享。
然后调用 `snd_ac97_mixer()` 函数，并传入一个 `struct snd_ac97_template` 记录以及上面创建的总线指针：

```c
struct snd_ac97_template ac97;
int err;

memset(&ac97, 0, sizeof(ac97));
ac97.private_data = chip;
snd_ac97_mixer(bus, &ac97, &chip->ac97);
```

其中 `chip->ac97` 是指向新创建的 `ac97_t` 实例的指针。在这种情况下，芯片指针被设置为私有数据，以便读写回调函数可以引用这个芯片实例。这个实例不一定存储在芯片记录中。如果你需要从驱动程序更改寄存器值，或者需要 AC97 编码解码器的挂起/恢复功能，请保留这个指针以传递给相应的函数。

### AC97 回调函数

标准回调函数是 `read` 和 `write`。显然，它们对应于对硬件低级代码的读取和写入访问。
`read` 回调返回参数中指定的寄存器值：

```c
static unsigned short snd_mychip_ac97_read(struct snd_ac97 *ac97, unsigned short reg)
{
    struct mychip *chip = ac97->private_data;
    ...
    return the_register_value;
}
```

这里，可以从 `ac97->private_data` 铸造出 `chip`。
同时，`write` 回调用于设置寄存器值：

```c
static void snd_mychip_ac97_write(struct snd_ac97 *ac97, unsigned short reg, unsigned short val)
{
    // 设置寄存器值
}
```

这些回调函数与控制 API 的回调函数一样是非原子性的。
还有其他一些回调函数：`reset`、`wait` 和 `init`。
`reset` 回调用于复位编码解码器。如果芯片需要特殊的复位方式，可以定义这个回调。
`wait` 回调用于在标准初始化过程中增加一些等待时间。如果芯片需要额外的等待时间，则定义这个回调。
`init` 回调用于进行额外的初始化操作。

### 在驱动程序中更新寄存器

如果需要从驱动程序访问编码解码器，可以调用以下函数：`snd_ac97_write()`、`snd_ac97_read()`、`snd_ac97_update()` 和 `snd_ac97_update_bits()`。
`:c:func:`snd_ac97_write()` 和 `:c:func:`snd_ac97_update()` 这两个函数都用于将一个值设置到给定的寄存器（如 `AC97_XXX`）。它们之间的区别在于，`:c:func:`snd_ac97_update()` 如果给定的值已经设置，则不会写入该值，而 `:c:func:`snd_ac97_write()` 总是会重写该值：

```c
snd_ac97_write(ac97, AC97_MASTER, 0x8080);
snd_ac97_update(ac97, AC97_MASTER, 0x8080);
```

`:c:func:`snd_ac97_read()` 用于读取给定寄存器的值。例如：

```c
value = snd_ac97_read(ac97, AC97_MASTER);
```

`:c:func:`snd_ac97_update_bits()` 用于更新给定寄存器中的某些位：

```c
snd_ac97_update_bits(ac97, reg, mask, value);
```

此外，当 VRA 或 DRA 被编解码器支持时，还有一个用于更改给定寄存器（如 `AC97_PCM_FRONT_DAC_RATE`）采样率的函数 `:c:func:`snd_ac97_set_rate()`：

```c
snd_ac97_set_rate(ac97, AC97_PCM_FRONT_DAC_RATE, 44100);
```

可以设置采样率的寄存器如下：`AC97_PCM_MIC_ADC_RATE`、`AC97_PCM_FRONT_DAC_RATE`、`AC97_PCM_LR_ADC_RATE`、`AC97_SPDIF`。当指定 `AC97_SPDIF` 时，并不会真正改变寄存器，而是更新相应的 IEC958 状态位。

### 时钟调整

在某些芯片中，编解码器的时钟不是 48000 Hz，而是使用 PCI 时钟（以节省晶振）。在这种情况下，需要将 `bus->clock` 字段更改为相应的值。例如，intel8x0 和 es1968 驱动程序有其自己的函数来从时钟读取数据。

### /proc 文件

ALSA AC97 接口会创建一个 `/proc` 文件，例如 `/proc/asound/card0/codec97#0/ac97#0-0` 和 `ac97#0-0+regs`。你可以参考这些文件查看当前的状态和寄存器信息。

### 多个编解码器

当同一张声卡上有多个编解码器时，你需要多次调用 `:c:func:`snd_ac97_mixer()` 并且设置 `ac97.num=1` 或更大。`num` 字段指定了编解码器的编号。

如果你设置了多个编解码器，你需要为每个编解码器编写不同的回调函数，或者在回调函数中检查 `ac97->num` 的值。

### MIDI (MPU401-UART) 接口

#### 一般

许多声卡内置了 MIDI (MPU401-UART) 接口。如果声卡支持标准的 MPU401-UART 接口，那么你很可能会使用 ALSA 的 MPU401-UART API。MPU401-UART API 定义在 `<sound/mpu401.h>` 中。

一些声卡芯片具有类似的但略有不同的 MPU401 实现。例如，emu10k1 有自己的 MPU401 函数。

#### MIDI 构造器

要创建一个 rawmidi 对象，可以调用 `:c:func:`snd_mpu401_uart_new()`：

```c
struct snd_rawmidi *rmidi;
snd_mpu401_uart_new(card, 0, MPU401_HW_MPU401, port, info_flags, irq, &rmidi);
```

第一个参数是卡指针，第二个参数是这个组件的索引。你可以创建最多 8 个 rawmidi 设备。

第三个参数是硬件类型，`MPU401_HW_XXX`。如果不是特殊的类型，可以使用 `MPU401_HW_MPU401`。

第四个参数是 I/O 端口地址。许多向后兼容的 MPU401 有一个 I/O 端口，如 0x330。或者，它可能是其自身的 PCI I/O 区域的一部分。这取决于芯片设计。
第五个参数是一个用于附加信息的位标志。当上述I/O端口地址属于PCI I/O区域的一部分时，MPU401 I/O端口可能已经被驱动程序本身分配（预留）。在这种情况下，请传递一个位标志 `MPU401_INFO_INTEGRATED`，这样mpu401-uart层将自行分配I/O端口。
当控制器只支持输入或输出MIDI流时，分别传递 `MPU401_INFO_INPUT` 或 `MPU401_INFO_OUTPUT` 位标志。然后创建rawmidi实例作为单一流。
`MPU401_INFO_MMIO` 位标志用于将访问方法更改为MMIO（通过readb和writeb）而不是iob和outb。在这种情况下，您需要将iomapped地址传递给 :c:func:`snd_mpu401_uart_new()`。
当设置了 `MPU401_INFO_TX_IRQ` 时，默认中断处理程序不会检查输出流。驱动程序需要自行调用 :c:func:`snd_mpu401_uart_interrupt_tx()` 来在中断处理程序中开始处理输出流。
如果MPU-401接口与其卡上的其他逻辑设备共享中断，则设置 `MPU401_INFO_IRQ_HOOK`（参见下面的`MIDI中断处理程序`__）。
通常，端口地址对应于命令端口，而端口+1对应于数据端口。如果不是这样，您可以手动更改struct snd_mpu401中的 `cport` 字段。
然而，struct snd_mpu401指针并不是由 :c:func:`snd_mpu401_uart_new()` 显式返回的。您需要显式地将 `rmidi->private_data` 转换为struct snd_mpu401并重置 `cport` 字段，如下所示：

```c
struct snd_mpu401 *mpu;
mpu = rmidi->private_data;
```

然后按需重置 `cport` ：

```c
mpu->cport = my_own_control_port;
```

第六个参数指定了将被分配的ISA中断号。如果没有要分配的中断（因为您的代码已经在分配共享中断，或者因为设备不使用中断），则传递-1。对于没有中断的MPU-401设备，将使用轮询定时器代替。

MIDI中断处理程序
----------------------

当在 :c:func:`snd_mpu401_uart_new()` 中分配中断时，会自动使用独占的ISA中断处理程序，因此除了创建mpu401组件之外，您无需做任何其他事情。否则，您需要设置 `MPU401_INFO_IRQ_HOOK` 并在确定发生UART中断时从您自己的中断处理程序中显式调用 :c:func:`snd_mpu401_uart_interrupt()`。
在这种情况下，您需要将从 :c:func:`snd_mpu401_uart_new()` 返回的rawmidi对象的private_data作为 :c:func:`snd_mpu401_uart_interrupt()` 的第二个参数传递：

```c
snd_mpu401_uart_interrupt(irq, rmidi->private_data, regs);
```

RawMIDI接口
=============

概述
-------

Raw MIDI接口用于可以作为字节流访问的硬件MIDI端口。它不用于直接理解MIDI的合成器芯片。
ALSA负责文件和缓冲区管理。您只需编写一些代码来在缓冲区和硬件之间移动数据即可。
rawmidi API 在 `<sound/rawmidi.h>` 中定义。

### RawMIDI 构造函数

要创建一个 rawmidi 设备，需要调用 `snd_rawmidi_new()` 函数：

```c
struct snd_rawmidi *rmidi;
err = snd_rawmidi_new(chip->card, "MyMIDI", 0, outs, ins, &rmidi);
if (err < 0)
    return err;
rmidi->private_data = chip;
strcpy(rmidi->name, "My MIDI");
rmidi->info_flags = SNDRV_RAWMIDI_INFO_OUTPUT |
                    SNDRV_RAWMIDI_INFO_INPUT |
                    SNDRV_RAWMIDI_INFO_DUPLEX;
```

第一个参数是卡指针，第二个参数是设备的 ID 字符串。
第三个参数是该组件的索引。你可以最多创建 8 个 rawmidi 设备。
第四个和第五个参数分别是该设备的输出和输入子流的数量（子流相当于一个 MIDI 端口）。
设置 `info_flags` 字段来指定设备的能力。如果至少有一个输出端口，则设置 `SNDRV_RAWMIDI_INFO_OUTPUT`；如果至少有一个输入端口，则设置 `SNDRV_RAWMIDI_INFO_INPUT`；如果设备可以同时处理输出和输入，则设置 `SNDRV_RAWMIDI_INFO_DUPLEX`。

创建 rawmidi 设备后，你需要为每个子流设置操作（回调）。有辅助函数来设置设备所有子流的操作：

```c
snd_rawmidi_set_ops(rmidi, SNDRV_RAWMIDI_STREAM_OUTPUT, &snd_mymidi_output_ops);
snd_rawmidi_set_ops(rmidi, SNDRV_RAWMIDI_STREAM_INPUT, &snd_mymidi_input_ops);
```

这些操作通常定义如下：

```c
static struct snd_rawmidi_ops snd_mymidi_output_ops = {
        .open =    snd_mymidi_output_open,
        .close =   snd_mymidi_output_close,
        .trigger = snd_mymidi_output_trigger,
};
```

这些回调在 `RawMIDI 回调` 部分中有详细解释。
如果有多个子流，你应该给每个子流一个唯一的名称：

```c
struct snd_rawmidi_substream *substream;
list_for_each_entry(substream,
                    &rmidi->streams[SNDRV_RAWMIDI_STREAM_OUTPUT].substreams,
                    list) {
        sprintf(substream->name, "My MIDI Port %d", substream->number + 1);
}
/* 对于 SNDRV_RAWMIDI_STREAM_INPUT 也一样 */
```

### RawMIDI 回调

在所有回调中，可以通过 `substream->rmidi->private_data` 访问你为 rawmidi 设备设置的私有数据。
如果有多个端口，你的回调可以通过传递给每个回调的 `struct snd_rawmidi_substream` 数据确定端口索引：

```c
struct snd_rawmidi_substream *substream;
int index = substream->number;
```

#### RawMIDI 打开回调

```c
static int snd_xxx_open(struct snd_rawmidi_substream *substream);
```

当一个子流被打开时会调用此函数。你可以在这里初始化硬件，但不应立即开始传输/接收数据。

#### RawMIDI 关闭回调

```c
static int snd_xxx_close(struct snd_rawmidi_substream *substream);
```

猜猜看。
一个 rawmidi 设备的 `open` 和 `close` 回调是通过互斥锁进行序列化的，并且可以睡眠。
### 原始MIDI触发回调函数用于输出子流

```c
static void snd_xxx_output_trigger(struct snd_rawmidi_substream *substream, int up);
```

当子流缓冲区中有需要传输的数据时，会使用非零的 `up` 参数调用此函数。要从缓冲区读取数据，请调用 `snd_rawmidi_transmit_peek()` 函数。它将返回已读取的字节数；如果缓冲区中没有更多数据，则返回的字节数将少于请求的字节数。在成功传输数据后，调用 `snd_rawmidi_transmit_ack()` 函数从子流缓冲区中移除这些数据：

```c
unsigned char data;
while (snd_rawmidi_transmit_peek(substream, &data, 1) == 1) {
    if (snd_mychip_try_to_transmit(data)) {
        snd_rawmidi_transmit_ack(substream, 1);
    } else {
        break; /* 硬件FIFO已满 */
    }
}
```

如果你事先知道硬件可以接受数据，可以使用 `snd_rawmidi_transmit()` 函数，该函数一次性读取并移除缓冲区中的数据：

```c
while (snd_mychip_transmit_possible()) {
    unsigned char data;
    if (snd_rawmidi_transmit(substream, &data, 1) != 1) {
        break; /* 没有更多数据 */
    }
    snd_mychip_transmit(data);
}
```

如果你事先知道你可以接受多少字节，可以使用 `snd_rawmidi_transmit*()` 函数的一个大于一的缓冲区大小。 `trigger` 回调函数不应休眠。如果硬件FIFO在子流缓冲区清空之前已满，则必须稍后继续传输数据，可以在中断处理程序中或在硬件没有MIDI传输中断的情况下通过定时器来完成。当需要中止数据传输时，会使用零 `up` 参数调用 `trigger` 回调函数。

### 原始MIDI触发回调函数用于输入子流

```c
static void snd_xxx_input_trigger(struct snd_rawmidi_substream *substream, int up);
```

使用非零 `up` 参数启用接收数据，或者使用零 `up` 参数禁用接收数据。 `trigger` 回调函数不应休眠；实际从设备读取数据通常是在中断处理程序中完成的。当数据接收被启用时，你的中断处理程序应该为所有接收到的数据调用 `snd_rawmidi_receive()` 函数：

```c
void snd_mychip_midi_interrupt(...) {
    while (mychip_midi_available()) {
        unsigned char data;
        data = mychip_midi_read();
        snd_rawmidi_receive(substream, &data, 1);
    }
}
```

### 排空回调函数

```c
static void snd_xxx_drain(struct snd_rawmidi_substream *substream);
```

这仅用于输出子流。此函数应等待所有从子流缓冲区读取的数据被传输完毕。这确保了设备可以在不丢失数据的情况下关闭，并且驱动程序可以卸载。此回调是可选的。如果你不在 `snd_rawmidi_ops` 结构体中设置 `drain`，ALSA 将简单地等待 50 毫秒。

### 其他设备

#### FM OPL3

FM OPL3 仍然在许多芯片中使用（主要是为了向后兼容）。ALSA 还有一个不错的 OPL3 FM 控制层。OPL3 API 定义在 `<sound/opl3.h>` 中。
FM寄存器可以通过在`<sound/asound_fm.h>`中定义的direct-FM API直接访问。在ALSA原生模式下，FM寄存器通过硬件依赖设备direct-FM扩展API进行访问；而在OSS兼容模式下，可以通过`/dev/dmfmX`设备使用OSS direct-FM兼容API访问FM寄存器。

创建OPL3组件时，有两个函数可以调用。第一个是用于创建`opl3_t`实例的构造函数：

```c
struct snd_opl3 *opl3;
snd_opl3_create(card, lport, rport, OPL3_HW_OPL3_XXX, integrated, &opl3);
```

第一个参数是卡指针，第二个参数是左端口地址，第三个参数是右端口地址。大多数情况下，右端口位于左端口+2的位置。
第四个参数是硬件类型。
当左端口和右端口已经被卡驱动程序分配时，将非零值传递给第五个参数（`integrated`）。否则，`opl3`模块将自行分配指定的端口。
如果访问硬件需要特殊方法而不是标准I/O访问，您可以使用`snd_opl3_new()`函数单独创建`opl3`实例：

```c
struct snd_opl3 *opl3;
snd_opl3_new(card, OPL3_HW_OPL3_XXX, &opl3);
```

然后为私有访问函数设置`command`、`private_data`和`private_free`。`l_port`和`r_port`不一定需要设置。只有`command`必须正确设置。可以从`opl3->private_data`字段中检索数据。

通过`snd_opl3_new()`创建`opl3`实例后，调用`snd_opl3_init()`以初始化芯片到适当状态。请注意，`snd_opl3_create()`始终内部调用此函数。
如果`opl3`实例创建成功，则为该`opl3`创建一个hwdep设备：

```c
struct snd_hwdep *opl3hwdep;
snd_opl3_hwdep_new(opl3, 0, 1, &opl3hwdep);
```

第一个参数是您创建的`opl3_t`实例，第二个参数是索引号，通常为0。
第三个参数是分配给OPL3端口的序列器客户端的索引偏移。如果有MPU401-UART，请在此处设置为1（UART始终占用0）。

### 硬件依赖设备

一些芯片需要用户空间访问以进行特殊控制或加载微代码。在这种情况下，您可以创建一个hwdep（硬件依赖）设备。hwdep API在`<sound/hwdep.h>`中定义。可以在`op3`驱动程序或`isa/sb/sb16_csp.c`中找到示例。
通过`snd_hwdep_new()`创建`hwdep`实例：

```c
struct snd_hwdep *hw;
snd_hwdep_new(card, "My HWDEP", 0, &hw);
```

其中第三个参数是索引号。
然后可以将任何指针值传递给`private_data`。如果您分配了私有数据，还应该定义一个析构函数。析构函数设置在`private_free`字段中：

```c
struct mydata *p = kmalloc(sizeof(*p), GFP_KERNEL);
hw->private_data = p;
hw->private_free = mydata_free;
```

析构函数的实现如下：

```c
static void mydata_free(struct snd_hwdep *hw)
{
    struct mydata *p = hw->private_data;
    kfree(p);
}
```

可以为此实例定义任意文件操作。文件操作定义在`ops`表中。例如，假设这个芯片需要一个ioctl：

```c
hw->ops.open = mydata_open;
hw->ops.ioctl = mydata_ioctl;
hw->ops.release = mydata_release;
```

并根据需要实现回调函数。
IEC958 (S/PDIF)
---------------

通常，IEC958 设备的控制是通过控制接口实现的。有一个宏 `SNDRV_CTL_NAME_IEC958()`（定义在 `<include/asound.h>` 中）用于组合 IEC958 控制的名字字符串。
对于 IEC958 状态位有一些标准控制。这些控制使用类型 `SNDRV_CTL_ELEM_TYPE_IEC958`，元素大小固定为 4 字节数组（`value.iec958.status[x]`）。对于 `info` 回调函数，你不需要指定这种类型的值字段（但是计数字段必须设置）。

“IEC958 播放消费者掩码” 用于返回消费者模式下的 IEC958 状态位的掩码。类似地，“IEC958 播放专业掩码” 返回专业模式下的掩码。它们都是只读控制。
同时，“IEC958 播放默认” 控制被定义为获取和设置当前默认的 IEC958 位。
由于历史原因，播放掩码和播放默认控制的两种变体可以在 `SNDRV_CTL_ELEM_IFACE_PCM` 或 `SNDRV_CTL_ELEM_IFACE_MIXER` 接口中实现。然而，驱动程序应该在同一接口上暴露掩码和默认值。
此外，你可以定义控制开关来启用或禁用或设置原始位模式。实现将取决于芯片，但控制名称应为 “IEC958 xxx”，最好使用 `SNDRV_CTL_NAME_IEC958()` 宏。
你可以找到一些示例，例如 `pci/emu10k1`、`pci/ice1712` 或 `pci/cmipci.c`。

缓冲区和内存管理
============================

缓冲区类型
------------

ALSA 提供了多种不同的缓冲区分配函数，具体取决于总线和架构。所有这些都有一个一致的 API。物理连续页的分配是通过 `snd_malloc_xxx_pages()` 函数完成的，其中 xxx 是总线类型。
带有回退机制的页分配是通过 `snd_dma_alloc_pages_fallback()` 函数完成的。该函数尝试分配指定数量的页，但如果可用的页不足，则会尝试减少请求大小，直到找到足够的空间，最小到一页。
要释放页面，请调用函数 :c:func:`snd_dma_free_pages()`。
通常，ALSA 驱动程序会在模块加载时预先分配并保留一大块连续的物理空间以供后续使用。这称为“预分配”。如前所述，您可以在 PCM 实例构造时（对于 PCI 总线的情况）调用以下函数：

```python
snd_pcm_lib_preallocate_pages_for_all(pcm, SNDRV_DMA_TYPE_DEV, &pci->dev, size, max);
```

其中 `size` 是要预分配的字节大小，而 `max` 是通过 `prealloc` proc 文件设置的最大大小。分配器将在给定大小范围内尝试获取尽可能大的区域。

第二个参数（类型）和第三个参数（设备指针）取决于总线类型。对于普通设备，将设备指针（通常与 `card->dev` 相同）作为第三个参数传递，并使用 `SNDRV_DMA_TYPE_DEV` 类型。

与总线无关的连续缓冲区可以使用 `SNDRV_DMA_TYPE_CONTINUOUS` 类型进行预分配。在这种情况下，您可以将设备指针设为 NULL，这是默认模式，意味着使用 `GFP_KERNEL` 标志进行分配。

如果您需要一个受限（较低地址）的内存区域，请设置设备的相干 DMA 掩码位，并像普通设备内存分配那样传递设备指针。对于这种类型，如果不需要地址限制，也可以将设备指针设为 NULL。

对于分散/聚集缓冲区，请使用 `SNDRV_DMA_TYPE_DEV_SG` 并传递设备指针（参见《非连续缓冲区》_部分）。

一旦缓冲区被预分配，您可以在 `hw_params` 回调中使用分配器：

```python
snd_pcm_lib_malloc_pages(substream, size);
```

请注意，您必须先进行预分配才能使用此函数。
但是大多数驱动程序使用“管理缓冲区分配模式”，而不是手动分配和释放。

这可以通过调用 :c:func:`snd_pcm_set_managed_buffer_all()` 而不是 :c:func:`snd_pcm_lib_preallocate_pages_for_all()` 来实现：

```python
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV, &pci->dev, size, max);
```

传递的参数在这两个函数中是相同的。
管理模式下的区别在于，在调用PCM `hw_params` 回调之前，PCM 内核会内部调用 `:c:func:snd_pcm_lib_malloc_pages()`，并且在PCM `hw_free` 回调之后自动调用 `:c:func:snd_pcm_lib_free_pages()`。因此，驱动程序不再需要显式地在其回调中调用这些函数。这使得许多驱动程序可以将 `hw_params` 和 `hw_free` 入口设置为NULL。

外部硬件缓冲区
-------------------------

有些芯片有自己的硬件缓冲区，并且无法从主机内存进行DMA传输。在这种情况下，你需要选择以下两种方法之一：1）直接将音频数据复制/设置到外部硬件缓冲区；或2）创建一个中间缓冲区，并在中断（最好是在任务项中）将数据从中间缓冲区复制/设置到外部硬件缓冲区。

第一种情况适用于外部硬件缓冲区足够大的情况。这种方法不需要任何额外的缓冲区，因此更高效。你需要定义用于数据传输的 `copy` 回调，以及播放时的 `fill_silence` 回调。然而，有一个缺点：它不能被映射（mmap）。GUS的GF1 PCM或emu8000的波表PCM就是这样的例子。

第二种情况允许对缓冲区进行映射（mmap），尽管你必须处理一个中断或任务项来将数据从中间缓冲区传输到硬件缓冲区。vxpocket驱动程序就是一个例子。

另一种情况是芯片使用PCI内存映射区域作为缓冲区而不是主机内存。在这种情况下，只有在某些架构（如Intel架构）上才能进行映射（mmap）。在非映射模式下，数据无法按常规方式传输。因此，你需要定义 `copy` 和 `fill_silence` 回调，就像上面的情况一样。可以在 `rme32.c` 和 `rme96.c` 中找到相关示例。

`copy` 和 `silence` 回调的实现取决于硬件是否支持交错或非交错样本。`copy` 回调的定义如下，根据方向（播放或捕获）略有不同：

```c
static int playback_copy(struct snd_pcm_substream *substream,
               int channel, unsigned long pos,
               struct iov_iter *src, unsigned long count);
static int capture_copy(struct snd_pcm_substream *substream,
               int channel, unsigned long pos,
               struct iov_iter *dst, unsigned long count);
```

在交错样本的情况下，第二个参数（`channel`）不会被使用。第三个参数（`pos`）指定字节位置。第四个参数对于播放和捕获的意义不同。对于播放，它包含源数据指针；而对于捕获，则是目标数据指针。最后一个参数是需要复制的字节数。

在这个回调中要做的事情也因方向不同而异。在播放的情况下，你将指定位置（`pos`）处的指定指针（`src`）中的给定数量的数据（`count`）复制到硬件缓冲区中。如果编码类似于memcpy的方式，复制过程如下：

```c
my_memcpy_from_iter(my_buffer + pos, src, count);
```

对于捕获方向，你将硬件缓冲区中指定位置（`pos`）处的给定数量的数据（`count`）复制到指定指针（`dst`）中：

```c
my_memcpy_to_iter(dst, my_buffer + pos, count);
```

`src` 或 `dst` 是一个包含指针和大小的 `struct iov_iter` 指针。使用现有的帮助函数来复制或访问数据，如 `linux/uio.h` 中定义的那样。

细心的读者可能会注意到，这些回调接收的是以字节为单位的参数，而不是像其他回调那样以帧为单位。这是因为这样可以使编码更容易，如上面的例子所示，并且也有助于统一交错和非交错的情况。
在非交错样本的情况下，实现会稍微复杂一些。回调函数会为每个通道调用一次，并传递给第二个参数，因此每次传输总共会被调用N次。其他参数的意义与交错样本的情况几乎相同。回调函数应将数据从/复制到给定的用户空间缓冲区，但仅针对给定的通道。详细信息，请参阅 `isa/gus/gus_pcm.c` 或 `pci/rme9652/rme9652.c` 示例。

通常对于播放，还会定义另一个回调函数 `fill_silence`。它的实现方式类似于上面的复制回调函数：

```c
static int silence(struct snd_pcm_substream *substream, int channel,
                   unsigned long pos, unsigned long count);
```

参数的意义与 `copy` 回调函数相同，尽管没有缓冲区指针参数。在交错样本的情况下，通道参数没有意义，就像 `copy` 回调函数一样。

`fill_silence` 回调函数的作用是在硬件缓冲区指定偏移量（`pos`）处设置给定数量（`count`）的静音数据。假设数据格式是有符号的（即静音数据是0），使用类似 memset 的函数实现如下：

```c
my_memset(my_buffer + pos, 0, count);
```

在非交错样本的情况下，实现又会变得稍微复杂一些，因为每次传输都会为每个通道调用N次。例如，请参阅 `isa/gus/gus_pcm.c`。

### 非连续缓冲区

如果您的硬件支持像 emu10k1 中的页表或像 via82xx 中的缓冲描述符，您可以使用分散/聚集（SG）DMA。ALSA 提供了一个处理 SG 缓冲区的接口。API 在 `<sound/pcm.h>` 中提供。

为了创建 SG 缓冲区处理器，您需要在 PCM 构造器中像其他 PCI 预分配一样调用 `snd_pcm_set_managed_buffer()` 或 `snd_pcm_set_managed_buffer_all()`，并传入 `SNDRV_DMA_TYPE_DEV_SG`：

```c
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV_SG,
                               &pci->dev, size, max);
```

其中 `pci` 是芯片的 `struct pci_dev` 指针。

`struct snd_sg_buf` 实例会在 `substream->dma_private` 中创建。您可以像这样进行类型转换：

```c
struct snd_sg_buf *sgbuf = (struct snd_sg_buf *)substream->dma_private;
```

然后，在调用 `snd_pcm_lib_malloc_pages()` 时，通用 SG 缓冲区处理器将分配给定大小的非连续内核页面，并将其映射为虚拟上连续的内存。虚拟指针通过 `runtime->dma_area` 访问。物理地址（`runtime->dma_addr`）设置为零，因为缓冲区在物理上是非连续的。物理地址表设置在 `sgbuf->table` 中。您可以使用 `snd_pcm_sgbuf_get_addr()` 获取特定偏移量处的物理地址。

如果您需要显式释放 SG 缓冲区数据，请像往常一样调用标准 API 函数 `snd_pcm_lib_free_pages()`。

### Vmalloc 分配的缓冲区

您可以使用通过 `vmalloc()` 分配的缓冲区，例如用于中间缓冲区。

您可以简单地通过标准 `snd_pcm_lib_malloc_pages()` 和相关函数进行分配，设置缓冲区预分配类型为 `SNDRV_DMA_TYPE_VMALLOC`：

```c
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_VMALLOC,
                               NULL, 0, 0);
```

这里将 NULL 作为设备指针参数传递，表示将分配默认页面（GFP_KERNEL 和 GFP_HIGHMEM）。

请注意，这里将零作为大小和最大大小参数传递。由于每次 `vmalloc` 调用都应该成功，因此我们不需要像其他连续页面那样预先分配缓冲区。
### 采购接口
==============

ALSA 提供了一个易于使用的 procfs 接口。这些 proc 文件对于调试非常有用。如果你编写了一个驱动程序并且希望获取运行状态或寄存器转储，我建议你设置 proc 文件。API 可以在 `<sound/info.h>` 中找到。

要创建一个 proc 文件，请调用 `snd_card_proc_new()` 函数：

```c
struct snd_info_entry *entry;
int err = snd_card_proc_new(card, "my-file", &entry);
```

其中第二个参数指定了要创建的 proc 文件的名称。上述示例将在卡目录下创建一个名为 `my-file` 的文件，例如 `/proc/asound/card0/my-file`。

像其他组件一样，通过 `snd_card_proc_new()` 创建的 proc 条目将在卡注册和释放函数中自动注册和释放。当创建成功时，该函数会将新实例存储在第三个参数中。它被初始化为只读文本 proc 文件。如果要将此 proc 文件作为只读文本文件使用，则需要通过 `snd_info_set_text_ops()` 设置读回调和私有数据：

```c
snd_info_set_text_ops(entry, chip, my_proc_read);
```

其中第二个参数（`chip`）是在回调中使用的私有数据。第三个参数指定了读缓冲区大小，第四个参数（`my_proc_read`）是回调函数，定义如下：

```c
static void my_proc_read(struct snd_info_entry *entry,
                         struct snd_info_buffer *buffer)
{
        struct my_chip *chip = entry->private_data;

        snd_iprintf(buffer, "This is my chip!\n");
        snd_iprintf(buffer, "Port = %ld\n", chip->port);
}
```

在读回调中，可以使用 `snd_iprintf()` 输出字符串，其工作方式与正常的 `printf()` 相同。

文件权限可以在之后更改，默认情况下所有用户都只能读取。如果你想添加写权限（默认为 root 用户），可以这样做：

```c
entry->mode = S_IFREG | S_IRUGO | S_IWUSR;
```

并设置写缓冲区大小和回调函数：

```c
entry->c.text.write = my_proc_write;
```

在写回调中，可以使用 `snd_info_get_line()` 获取文本行，并使用 `snd_info_get_str()` 从行中检索字符串。一些示例可以在 `core/oss/mixer_oss.c` 和 `core/oss/pcm_oss.c` 中找到。

对于原始数据 proc 文件，可以按以下方式设置属性：

```c
static const struct snd_info_entry_ops my_file_io_ops = {
        .read = my_file_io_read,
};

entry->content = SNDRV_INFO_CONTENT_DATA;
entry->private_data = chip;
entry->c.ops = &my_file_io_ops;
entry->size = 4096;
entry->mode = S_IFREG | S_IRUGO;
```

对于原始数据，必须正确设置 `size` 字段。这指定了 proc 文件访问的最大大小。原始模式下的读写回调比文本模式更直接。你需要使用低级别的 I/O 函数，如 `copy_from_user()` 和 `copy_to_user()` 来传输数据：

```c
static ssize_t my_file_io_read(struct snd_info_entry *entry,
                               void *file_private_data,
                               struct file *file,
                               char *buf,
                               size_t count,
                               loff_t pos)
{
        if (copy_to_user(buf, local_data + pos, count))
                return -EFAULT;
        return count;
}
```

如果 info 条目的大小已正确设置，`count` 和 `pos` 将保证在 0 和给定大小之间。除非有其他条件要求，否则无需在回调中检查范围。

### 电源管理
================

如果芯片应该支持挂起/恢复功能，你需要向驱动程序添加电源管理代码。电源管理的附加代码应通过 `CONFIG_PM` 宏进行 ifdef，或者用 `__maybe_unused` 属性注释；否则编译器会报错。

如果驱动程序 *完全* 支持挂起/恢复，即设备可以在挂起后正确恢复到之前的状态，你可以设置 PCM 信息字段中的 `SNDRV_PCM_INFO_RESUME` 标志。通常，当芯片的寄存器可以安全地保存和恢复到 RAM 中时，这是可能的。如果设置了这个标志，在恢复回调完成后会调用带有 `SNDRV_PCM_TRIGGER_RESUME` 的触发回调。

即使驱动程序不完全支持 PM，但仍然可以部分实现挂起/恢复，也值得实现挂起/恢复回调。在这种情况下，应用程序可以通过调用 `snd_pcm_prepare()` 重置状态并适当地重新启动流。因此，你可以定义下面的挂起/恢复回调，但不要在 PCM 信息中设置 `SNDRV_PCM_INFO_RESUME` 标志。
请注意，带有 `SUSPEND` 的触发器在调用 `:c:func:`snd_pcm_suspend_all()` 时总是会被调用，无论是否设置了 `SNDRV_PCM_INFO_RESUME` 标志。`RESUME` 标志只影响 `:c:func:`snd_pcm_resume()` 的行为。（因此，理论上，在没有设置 `SNDRV_PCM_INFO_RESUME` 标志的情况下，`SNDRV_PCM_TRIGGER_RESUME` 不需要在触发回调中处理。但是，出于兼容性原因，最好保留它。）

驱动程序需要根据设备所连接的总线定义挂起/恢复钩子。对于 PCI 驱动程序，回调函数如下所示：

```c
static int __maybe_unused snd_my_suspend(struct device *dev)
{
        .... /* 执行挂起操作 */
        return 0;
}
static int __maybe_unused snd_my_resume(struct device *dev)
{
        .... /* 执行恢复操作 */
        return 0;
}
```

实际挂起工作的方案如下：

1. 获取卡和芯片数据。
2. 调用 `:c:func:`snd_power_change_state()` 并传入 `SNDRV_CTL_POWER_D3hot` 来改变电源状态。
3. 如果使用了 AC97 编解码器，对每个编解码器调用 `:c:func:`snd_ac97_suspend()`。
4. 必要时保存寄存器值。
5. 必要时停止硬件。

典型的代码如下所示：

```c
static int __maybe_unused mychip_suspend(struct device *dev)
{
        /* (1) */
        struct snd_card *card = dev_get_drvdata(dev);
        struct mychip *chip = card->private_data;
        /* (2) */
        snd_power_change_state(card, SNDRV_CTL_POWER_D3hot);
        /* (3) */
        snd_ac97_suspend(chip->ac97);
        /* (4） */
        snd_mychip_save_registers(chip);
        /* (5) */
        snd_mychip_stop_hardware(chip);
        return 0;
}
```

实际恢复工作的方案如下：

1. 获取卡和芯片数据。
2. 重新初始化芯片。
3. 必要时恢复保存的寄存器值。
4. 恢复混音器，例如通过调用 `:c:func:`snd_ac97_resume()`。
5. 重启硬件（如果有）。
6. 调用 :c:func:`snd_power_change_state()` 并传入 `SNDRV_CTL_POWER_D0` 来通知相关进程

典型的代码如下所示：

```c
static int __maybe_unused mychip_resume(struct pci_dev *pci)
{
        /* (1) */
        struct snd_card *card = dev_get_drvdata(dev);
        struct mychip *chip = card->private_data;
        /* (2) */
        snd_mychip_reinit_chip(chip);
        /* (3）*/
        snd_mychip_restore_registers(chip);
        /* (4）*/
        snd_ac97_resume(chip->ac97);
        /* (5）*/
        snd_mychip_restart_chip(chip);
        /* (6）*/
        snd_power_change_state(card, SNDRV_CTL_POWER_D0);
        return 0;
}
```

请注意，当此回调被调用时，PCM 流已经被通过其自身的电源管理操作（PM ops）内部调用 :c:func:`snd_pcm_suspend_all()` 暂停了。

好的，我们现在有了所有回调。让我们来设置这些回调。在初始化声卡时，请确保可以从声卡实例中获取芯片数据，通常可以通过 `private_data` 字段获取，如果你单独创建了芯片数据的话：

```c
static int snd_mychip_probe(struct pci_dev *pci,
                            const struct pci_device_id *pci_id)
{
        ...
        struct snd_card *card;
        struct mychip *chip;
        int err;
        ...

        err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                           0, &card);
        ...

        chip = kzalloc(sizeof(*chip), GFP_KERNEL);
        ...

        card->private_data = chip;
        ...
}
```

当你使用 :c:func:`snd_card_new()` 创建芯片数据时，无论如何都可以通过 `private_data` 字段访问它：

```c
static int snd_mychip_probe(struct pci_dev *pci,
                            const struct pci_device_id *pci_id)
{
        ...
        struct snd_card *card;
        struct mychip *chip;
        int err;
        ...

        err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                           sizeof(struct mychip), &card);
        ...
}
```
```c
chip = card->private_data;
...
}

如果需要空间来保存寄存器，请在此处分配缓冲区，因为在挂起阶段无法分配内存将是致命的。分配的缓冲区应在相应的析构函数中释放。

接下来，为 pci_driver 设置挂起/恢复回调：

  static DEFINE_SIMPLE_DEV_PM_OPS(snd_my_pm_ops, mychip_suspend, mychip_resume);

  static struct pci_driver driver = {
          .name = KBUILD_MODNAME,
          .id_table = snd_my_ids,
          .probe = snd_my_probe,
          .remove = snd_my_remove,
          .driver = {
                  .pm = &snd_my_pm_ops,
          },
  };

模块参数
=========

ALSA 有标准的模块选项。至少每个模块应该有 `index`、`id` 和 `enable` 选项。
如果模块支持多个声卡（通常最多 8 张 = `SNDRV_CARDS`），它们应该是数组。默认初始值已经定义为常量以方便编程：

  static int index[SNDRV_CARDS] = SNDRV_DEFAULT_IDX;
  static char *id[SNDRV_CARDS] = SNDRV_DEFAULT_STR;
  static int enable[SNDRV_CARDS] = SNDRV_DEFAULT_ENABLE_PNP;

如果模块只支持一张声卡，则可以是单个变量。在这种情况下 `enable` 选项并不总是必要的，但最好有一个虚拟选项以保持兼容性。
模块参数必须使用标准的 `module_param()`、`module_param_array()` 和 `MODULE_PARM_DESC()` 宏声明。
典型的代码如下所示：

  #define CARD_NAME "我的芯片"

  module_param_array(index, int, NULL, 0444);
  MODULE_PARM_DESC(index, "用于 " CARD_NAME " 声卡的索引值。");
  module_param_array(id, charp, NULL, 0444);
  MODULE_PARM_DESC(id, "用于 " CARD_NAME " 声卡的 ID 字符串。");
  module_param_array(enable, bool, NULL, 0444);
  MODULE_PARM_DESC(enable, "启用 " CARD_NAME " 声卡。");

此外，不要忘记定义模块描述和许可证。
特别是，最近的 modprobe 需要定义模块许可为 GPL 等，否则系统将显示为“被污染”：

  MODULE_DESCRIPTION("用于我的芯片的声卡驱动程序");
  MODULE_LICENSE("GPL");

设备管理资源
===============

在上述示例中，所有资源都是手动分配和释放的。但人类本质上是懒惰的，特别是开发者更懒。因此有一些方法可以自动化释放部分；这就是设备管理资源（devres 或 devm 家族）。例如，通过 `devm_kmalloc()` 分配的对象将在设备解绑时自动释放。
ALSA 核心也提供了设备管理助手，即 `snd_devm_card_new()` 函数来创建一个声卡对象。
调用此函数而不是普通的 `snd_card_new()`，你就可以忽略显式的 `snd_card_free()` 调用，因为该函数会在错误和移除路径中自动调用。
需要注意的一点是在调用 `snd_card_register()` 之后，`snd_card_free()` 的调用应放在调用链的最开始位置。
```
此外，“private_free”回调总是在声卡释放时被调用，因此请务必在“private_free”回调中放入硬件清理程序。它甚至可能在你实际设置之前，在早期的错误路径中就被调用了。为了避免这种无效的初始化，你可以在 :c:func:`snd_card_register()` 调用成功后设置“private_free”回调。

另一点需要注意的是，一旦你以这种方式管理声卡，你应该尽可能多地为每个组件使用设备管理助手。混合使用正常资源和管理资源可能会导致释放顺序混乱。

如何将你的驱动程序加入ALSA树
=====================================

概述
-------

到目前为止，你已经学会了如何编写驱动代码。现在你可能会有一个问题：如何将自己的驱动程序加入ALSA驱动树？在这里（终于 :)），简要描述了标准程序。

假设你为名为“xyz”的声卡创建了一个新的PCI驱动程序。该声卡模块名称应为snd-xyz。新的驱动程序通常会放在alsa-driver树中，即对于PCI卡来说位于`sound/pci`目录下。

在以下各节中，假设驱动代码将放入Linux内核树中。这里涵盖两种情况：一个由单个源文件组成的驱动程序和一个由多个源文件组成的驱动程序。

单个源文件的驱动程序
--------------------------------

1. 修改`sound/pci/Makefile`

   假设你有一个名为xyz.c的文件。添加以下两行：

     ```
     snd-xyz-y := xyz.o
     obj-$(CONFIG_SND_XYZ) += snd-xyz.o
     ```

2. 创建Kconfig条目

   在Kconfig中为你的xyz驱动程序添加新的条目：

     ```
     config SND_XYZ
       tristate "Foobar XYZ"
       depends on SND
       select SND_PCM
       help
         Say Y here to include support for Foobar XYZ soundcard.
         To compile this driver as a module, choose M here; 
         the module will be called snd-xyz.
     ```

   行`select SND_PCM`指定了驱动程序xyz支持PCM。

   除了SND_PCM外，还可以选择以下组件：SND_RAWMIDI, SND_TIMER, SND_HWDEP, SND_MPU401_UART, SND_OPL3_LIB, SND_OPL4_LIB, SND_VX_LIB, SND_AC97_CODEC。

   对于每个支持的组件添加相应的select命令。
请注意，某些选择隐含了低级选择。例如，
PCM 包含了 TIMER，MPU401_UART 包含了 RAWMIDI，AC97_CODEC 包含了 PCM，OPL3_LIB 包含了 HWDEP。您无需再次指定低级选择。

有关 Kconfig 脚本的详细信息，请参阅 kbuild 文档。
具有多个源文件的驱动程序
----------------------------

假设 snd-xyz 驱动程序有多个源文件。它们位于新的子目录 `sound/pci/xyz` 中。

1. 在 `sound/pci/Makefile` 中添加一个新的目录（`sound/pci/xyz`），如下所示：

       obj-$(CONFIG_SND) += sound/pci/xyz/

2. 在目录 `sound/pci/xyz` 下创建一个 Makefile：

         snd-xyz-y := xyz.o abc.o def.o
         obj-$(CONFIG_SND_XYZ) += snd-xyz.o

3. 创建 Kconfig 入口

   这个过程与上一节相同。

有用的函数
===========

:c:func:`snd_printk()` 及其相关函数
--------------------------------------

.. note:: 本小节描述了一些用于增强标准 :c:func:`printk()` 及其相关函数的辅助函数。
然而，通常情况下，不再推荐使用这些辅助函数。如果可能的话，请尽量使用标准函数如 :c:func:`dev_err()` 或 :c:func:`pr_err()`。

ALSA 提供了一个详细的 :c:func:`printk()` 函数版本。如果内核配置 `CONFIG_SND_VERBOSE_PRINTK` 被设置，该函数将打印给定的消息以及调用者的文件名和行号。`KERN_XXX` 前缀也会被处理，就像原始的 :c:func:`printk()` 一样，因此建议加上这个前缀，例如：`snd_printk(KERN_ERR "Oh my, sorry, it's extremely bad!\\n");`

还有用于调试的 :c:func:`printk()`：
:c:func:`snd_printd()` 可以用于一般的调试目的。
如果设置了 `CONFIG_SND_DEBUG`，此函数会被编译，并且工作方式与 :c:func:`snd_printk()` 相同。如果没有设置调试标志，ALSA 编译时会忽略它。
:c:func:`snd_printdd()` 只有在设置了 `CONFIG_SND_DEBUG_VERBOSE` 时才会被编译。
:c:func:`snd_BUG()`
-------------------

此宏会在当前点显示 `BUG?` 消息和堆栈跟踪，类似于 :c:func:`snd_BUG_ON()`。它有助于表明此处发生了致命错误。如果没有设置调试标志，此宏将被忽略。
:c:func:`snd_BUG_ON()`
----------------------

:c:func:`snd_BUG_ON()` 宏与 :c:func:`WARN_ON()` 宏类似。例如，可以使用 `snd_BUG_ON(!pointer);` 或作为条件使用，如 `if (snd_BUG_ON(non_zero_is_bug)) return -EINVAL;`。

该宏接受一个条件表达式进行评估。当设置了 `CONFIG_SND_DEBUG` 时，如果表达式的值非零，则会显示警告消息（如 `BUG? (xxx)`），通常还会跟随堆栈跟踪。在这两种情况下，它都会返回评估后的值。

致谢
====

我要感谢 Phil Kerr 对本文档改进和校正的帮助。
Kevin Conder 将原始纯文本格式化为 DocBook 格式。
Giuliano Pochini 纠正了拼写错误，并在硬件约束部分提供了示例代码。
