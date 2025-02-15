编写ALSA驱动程序
======================

:作者: Takashi Iwai <tiwai@suse.de>

前言
=======

本文档描述了如何编写 `ALSA（高级Linux声音架构）<http://www.alsa-project.org/>`__ 驱动程序。本文档主要关注PCI声卡。对于其他设备类型，API可能也不同。但是，至少ALSA内核API是一致的，因此对于编写这些驱动程序仍有一定的帮助。本文档的目标读者是有足够的C语言技能并具备基本Linux内核编程知识的人。本文档不解释Linux内核编码的一般主题，也不涉及低级驱动程序实现细节。它仅描述了使用ALSA编写PCI声卡驱动的标准方法。
文件树结构
===================

一般
-------

ALSA驱动程序的文件树结构如下所示：

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

此目录包含ALSA驱动程序的核心中间层。在此目录中存储了原生的ALSA模块。子目录包含不同的模块，并且依赖于内核配置。
core/oss
~~~~~~~~

此目录中存储了OSS PCM和混音器仿真模块的代码。由于ALSA rawmidi代码非常小，OSS rawmidi仿真被包含在其中。序列器代码存储在 ``core/seq/oss`` 目录中（见下文）。
core/seq
~~~~~~~~

此目录及其子目录用于ALSA序列器。此目录包含序列器核心以及主要的序列器模块，如snd-seq-midi、snd-seq-virmidi等。它们仅在内核配置中设置了 ``CONFIG_SND_SEQUENCER`` 时编译。
core/seq/oss
~~~~~~~~~~~~

此处包含OSS序列器仿真的代码。
include目录
-----------------

这是ALSA驱动程序公共头文件的存放位置，这些文件将导出到用户空间或被不同目录中的多个文件引用。原则上，私有头文件不应放置在此目录中，但由于历史原因，您可能会在此处找到一些文件。

drivers目录
-----------------

此目录包含不同架构上不同驱动程序之间共享的代码。因此，它们不应该是特定于架构的。例如，虚拟PCM驱动程序和串行MIDI驱动程序可以在该目录中找到。在子目录中，可以找到独立于总线和CPU架构的组件的代码。

drivers/mpu401
~~~~~~~~~~~~~~

MPU401和MPU401-UART模块存储在此处。

drivers/opl3 和 opl4
~~~~~~~~~~~~~~~~~~~~~

OPL3和OPL4 FM合成器的代码位于此处。
i2c 目录
--------

此目录包含 ALSA 的 i2c 组件。
尽管 Linux 上有一个标准的 i2c 层，但 ALSA 对于某些声卡有自己的 i2c 代码，因为声卡只需要简单的操作，而标准的 i2c API 对于此目的来说过于复杂。

synth 目录
----------

此目录包含合成器中间层模块。
到目前为止，只有 Emu8000/Emu10k1 合成器驱动程序位于 `synth/emux` 子目录下。

pci 目录
--------

此目录及其子目录包含了 PCI 声卡的顶级卡模块以及与 PCI 总线相关的特定代码。
从单个文件编译的驱动程序直接存储在 pci 目录中，而由多个源文件组成的驱动程序则存储在其自己的子目录中（例如 emu10k1、ice1712）。

isa 目录
--------

此目录及其子目录包含了 ISA 声卡的顶级卡模块。

arm、ppc 和 sparc 目录
----------------------

这些目录用于存储针对这些架构之一的特定顶级卡模块。

usb 目录
--------

此目录包含 USB 音频驱动程序。
USB MIDI 驱动程序已集成到 USB 音频驱动程序中。
### PCMCIA 目录

PCMCIA，特别是PCCard驱动程序将放在这里。CardBus驱动程序将放在PCI目录中，因为它们的API与标准PCI卡相同。

### soc 目录

此目录包含ASoC（ALSA系统级芯片）层的代码，包括ASoC核心、编解码器和机器驱动程序。

### oss 目录

这里包含OSS/Lite代码。在撰写本文时，除了m68k上的dmasound外，其他所有代码都已移除。

### PCI 驱动程序的基本流程
#### 概述

PCI声卡的最小流程如下：

- 定义PCI ID表（参见“PCI条目”部分）
- 创建`probe`回调函数
- 创建`remove`回调函数
- 创建一个包含上述三个指针的`struct pci_driver`结构体
- 创建一个`init`函数，仅调用`:c:func:`pci_register_driver()`来注册上面定义的pci_driver表
- 创建一个`exit`函数，用于调用`:c:func:`pci_unregister_driver()`函数
完整代码示例
------------

下面展示了代码示例。目前某些部分还未实现，但将在接下来的章节中填充。在`:c:func:`snd_mychip_probe()`函数中的注释行中的数字指的是在接下来的部分中解释的细节：
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
    /* 其余实现将在“PCI资源管理”部分中给出 */
};

/* 特定于芯片的析构函数
 * （见“PCI资源管理”）
 */
static int snd_mychip_free(struct mychip *chip)
{
    .... /* 将在后面实现... */
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

    /* 在这里检查PCI可用性
     * （见“PCI资源管理”）
     */
    ...
    /* 使用零填充分配特定于芯片的数据 */
    chip = kzalloc(sizeof(*chip), GFP_KERNEL);
    if (chip == NULL)
        return -ENOMEM;

    chip->card = card;

    /* 初始化剩余部分在这里；将在后面实现，
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

/* 构造函数 —— 见“驱动程序构造函数”小节 */
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
    .... /* 在后面实现 */

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

/* 析构函数 —— 见“析构函数”小节 */
static void snd_mychip_remove(struct pci_dev *pci)
{
    snd_card_free(pci_get_drvdata(pci));
}
```

驱动程序构造函数
------------------

PCI驱动程序的实际构造函数是`probe`回调。由于任何PCI设备都可能是热插拔设备，因此不能使用`__init`前缀来使用`probe`回调和其他从`probe`回调调用的组件构造函数。
在`probe`回调中，通常采用以下方案：

1) 检查并递增设备索引
~~~~~~~~~~~~~~~~~~~~~~~~

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

其中`enable[dev]`是模块选项
每次`probe`回调被调用时，检查设备是否可用。如果不可用，则简单地递增设备索引并返回。dev也将在后面递增(`步骤7 设置PCI驱动数据并返回零._`)。

2) 创建一个卡片实例
~~~~~~~~~~~~~~~~~~~~~~~~

```c
struct snd_card *card;
int err;
...
```
翻译成中文:

错误处理 (`snd_card_new` 调用) 如下所示：

```c
err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                     0, &card);
```

具体细节将在 `声卡及组件管理`_ 部分进行解释。

3) 创建主组件
~~~~~~~~~~~~~~

在这个部分，分配 PCI 资源：

```c
struct mychip *chip;
...
err = snd_mychip_create(card, pci, &chip);
if (err < 0)
    goto error;
```

具体细节将在 `PCI 资源管理`_ 部分进行解释。

当出现错误时，探测函数需要处理这些错误。在本例中，我们有一个单一的错误处理路径，位于函数末尾：

```c
error:
    snd_card_free(card);
    return err;
```

由于每个组件都可以被正确释放，因此大多数情况下单个 `snd_card_free()` 调用应该足够了。

4) 设置驱动 ID 和名称字符串
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```c
strcpy(card->driver, "My Chip");
strcpy(card->shortname, "My Own Chip 123");
sprintf(card->longname, "%s at 0x%lx irq %i",
        card->shortname, chip->port, chip->irq);
```

`driver` 字段保存芯片的最小 ID 字符串。这是由 alsa-lib 的配置器使用的，因此请保持简单但独特。即使是同一个驱动程序也可以有不同的驱动 ID 来区分每种芯片类型的功能。

`shortname` 字段是一个更详细的名称字符串。`longname` 字段包含了 `/proc/asound/cards` 中显示的信息。

5) 创建其他组件，例如混音器、MIDI 等
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在这里，定义基本组件，如 `PCM 接口`__、混音器（例如 `AC97 编解码器 API`__）、MIDI（例如 `MIDI (MPU401-UART) 接口`__）以及其他接口。
此外，如果你需要一个`进程文件 (Proc Interface)`__，也在这里定义它。
6) 注册卡片实例
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  int err = snd_card_register(card);
  if (err < 0)
          goto error;

这部分将在 `卡片和组件的管理`_ 部分进行解释。
7) 设置PCI驱动数据并返回零
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  pci_set_drvdata(pci, card);
  dev++;
  return 0;

在上面的代码中，卡片记录被保存。这个指针也在移除回调和电源管理回调中使用。
析构函数
----------

析构函数，即移除回调，简单地释放卡片实例。之后ALSA中间层会自动释放所有已连接的组件。这通常只是调用 :c:func:`snd_card_free()`：

  static void snd_mychip_remove(struct pci_dev *pci)
  {
          snd_card_free(pci_get_drvdata(pci));
  }

上述代码假设卡片指针已经被设置为PCI驱动的数据。
头文件
------------

对于上面的例子，至少需要以下头文件：

  #include <linux/init.h>
  #include <linux/pci.h>
  #include <linux/slab.h>
  #include <sound/core.h>
  #include <sound/initval.h>

最后一个头文件仅当模块选项在源文件中定义时是必要的。如果代码被分割到多个文件中，没有模块选项的文件不需要包含它。
除了这些头文件之外，你还需要 ``<linux/interrupt.h>`` 来处理中断，以及 ``<linux/io.h>`` 来访问I/O。如果你使用了 :c:func:`mdelay()` 或者 :c:func:`udelay()` 函数，则还需要包含 ``<linux/delay.h>``。
ALSA接口，如PCM和控制APIs，在其他的`<sound/xxx.h>`头文件中定义。这些头文件必须在`<sound/core.h>`之后被包含。

### 卡和组件的管理

#### 卡实例

对于每块声卡，都需要分配一个“卡”记录。
卡记录是声卡的核心管理部分。它管理着声卡上所有设备（组件）的列表，比如PCM、混音器、MIDI、合成器等。此外，卡记录还保存着卡的ID和名称字符串，管理proc文件的根目录，并控制电源管理和热插拔断开的状态。卡记录中的组件列表用于在销毁时正确释放资源。

如上所述，创建一个卡实例需要调用`snd_card_new()`函数：

```c
struct snd_card *card;
int err;
err = snd_card_new(&pci->dev, index, id, module, extra_size, &card);
```

该函数接受六个参数：父设备指针、卡索引号、ID字符串、模块指针（通常为`THIS_MODULE`）、额外数据空间的大小以及返回卡实例的指针。`extra_size`参数用于为`card->private_data`分配芯片特定数据的空间。需要注意的是，这些数据是由`snd_card_new()`函数分配的。
第一个参数，即结构体`struct device`的指针，指定了父设备。对于PCI设备，通常会传递`&pci->`。

#### 组件

创建卡后，可以将组件（设备）附加到卡实例上。在ALSA驱动程序中，一个组件表示为`struct snd_device`对象。组件可以是PCM实例、控制接口、原始MIDI接口等，每个这样的实例都有一个组件条目。

组件可以通过`snd_device_new()`函数创建：

```c
snd_device_new(card, SNDRV_DEV_XXX, chip, &ops);
```

这需要卡指针、设备级别(`SNDRV_DEV_XXX`)、数据指针和回调指针(`&ops`)作为参数。设备级别定义了组件的类型以及注册和注销的顺序。对于大多数组件来说，设备级别已经定义好了。对于自定义组件，可以使用`SNDRV_DEV_LOWLEVEL`。

此函数本身不会分配数据空间。数据必须手动预先分配，并将其指针作为参数传递。这个指针（上述示例中的`chip`）用作实例的标识符。

每个预定义的ALSA组件，如AC97和PCM，在其构造函数内部都会调用`snd_device_new()`。每个组件的析构函数定义在回调指针中。因此，对于这样的组件，您不需要关心调用析构函数。
如果你希望创建自己的组件，你需要将析构函数设置为 `dev_free` 回调函数在 `ops` 中，以便可以通过 :c:func:`snd_card_free()` 自动释放。下一个示例将展示芯片特定数据的实现。

### 芯片特定数据

芯片特定信息，例如 I/O 端口地址、其资源指针或中断请求（IRQ）号，存储在芯片特定记录中：

```c
struct mychip {
    ...
};
```

一般来说，有两种方法来分配芯片记录：

1. 通过 :c:func:`snd_card_new()` 分配
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    如上所述，你可以将额外数据长度传递给 :c:func:`snd_card_new()` 的第五个参数，例如：

    ```c
    err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                       sizeof(struct mychip), &card);
    ```

    `struct mychip` 是芯片记录的类型。
    
    返回后，可以这样访问分配的记录：

    ```c
    struct mychip *chip = card->private_data;
    ```

    使用这种方法，你不需要分配两次。记录会与卡片实例一起被释放。

2. 分配一个额外设备
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    在通过 :c:func:`snd_card_new()` 分配卡片实例（第四个参数为 `0`）之后，调用 :c:func:`kzalloc()` ：

    ```c
    struct snd_card *card;
    struct mychip *chip;
    err = snd_card_new(&pci->dev, index[dev], id[dev], THIS_MODULE,
                       0, &card);
    ....
    chip = kzalloc(sizeof(*chip), GFP_KERNEL);
    ```

    芯片记录至少应该有一个字段来持有卡片指针：

    ```c
    struct mychip {
        struct snd_card *card;
        ...
    };
    ```

    然后，在返回的芯片实例中设置卡片指针：

    ```c
    chip->card = card;
    ```

    接下来，初始化字段，并使用指定的 `ops` 将此芯片记录注册为低级设备：

    ```c
    static const struct snd_device_ops ops = {
        .dev_free = snd_mychip_dev_free,
    };
    ...
    ```
The provided code snippet is a detailed example of how to integrate a custom sound chip driver into the Linux kernel, specifically focusing on PCI resource management and the creation and deletion of device instances. Below is a translation of the given text and code comments into simplified Chinese.

```c
// 创建一个新的snd_device实例
snd_device_new(card, SNDRV_DEV_LOWLEVEL, chip, &ops);

// :c:func:`snd_mychip_dev_free()` 是设备析构函数，它将调用实际的析构函数:
static int snd_mychip_dev_free(struct snd_device *device)
{
    return snd_mychip_free(device->device_data);
}

// 其中 :c:func:`snd_mychip_free()` 是实际的析构函数
// 这种方法的缺点是代码量明显较大
// 但是优点是你可以通过设置 `snd_device_ops` 在注册和卸载声卡时触发自己的回调
// 关于声卡的注册和卸载，请参阅下面的小节
// 注册和释放
// ------------------------

// 所有组件分配完毕后，通过调用 :c:func:`snd_card_register()` 来注册声卡实例。
// 此时可以访问设备文件。也就是说，在调用 :c:func:`snd_card_register()` 之前，
// 组件从外部是安全不可见的。如果此调用失败，则应在释放声卡后退出探测函数
// 通过 :c:func:`snd_card_free()` 来释放声卡实例，所有组件会自动被此调用释放
// 对于支持热插拔的设备，可以使用 :c:func:`snd_card_free_when_closed()`。
// 这个函数会延迟销毁直到所有设备关闭为止
// PCI资源管理
// ======================

// 完整代码示例
// --------------

// 在这一节中，我们将完成芯片特定的构造器、析构器和PCI条目。下面是示例代码:

struct mychip {
    struct snd_card *card;
    struct pci_dev *pci;

    unsigned long port;
    int irq;
};

static int snd_mychip_free(struct mychip *chip)
{
    // 如果有必要，禁用硬件
    .... /* (本文档未实现) */

    // 释放中断
    if (chip->irq >= 0)
        free_irq(chip->irq, chip);
    // 释放I/O端口和内存
    pci_release_regions(chip->pci);
    // 禁用PCI条目
    pci_disable_device(chip->pci);
    // 释放数据
    kfree(chip);
    return 0;
}

// 芯片特定的构造器
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

    // 初始化PCI条目
    err = pci_enable_device(pci);
    if (err < 0)
        return err;
    // 检查PCI可用性（28位DMA）
    if (pci_set_dma_mask(pci, DMA_BIT_MASK(28)) < 0 ||
        pci_set_consistent_dma_mask(pci, DMA_BIT_MASK(28)) < 0) {
        printk(KERN_ERR "无法设置28位DMA掩码\n");
        pci_disable_device(pci);
        return -ENXIO;
    }

    chip = kzalloc(sizeof(*chip), GFP_KERNEL);
    if (chip == NULL) {
        pci_disable_device(pci);
        return -ENOMEM;
    }

    // 初始化变量
    chip->card = card;
    chip->pci = pci;
    chip->irq = -1;

    // (1) 分配PCI资源
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

    // (2) 初始化芯片硬件
    .... /*   (本文档未实现) */

    err = snd_device_new(card, SNDRV_DEV_LOWLEVEL, chip, &ops);
    if (err < 0) {
        snd_mychip_free(chip);
        return err;
    }

    *rchip = chip;
    return 0;
}

// PCI ID
static struct pci_device_id snd_mychip_ids[] = {
    { PCI_VENDOR_ID_FOO, PCI_DEVICE_ID_BAR,
      PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0, },
    ...
{ 0, }
};
MODULE_DEVICE_TABLE(pci, snd_mychip_ids);

// pci_driver定义
static struct pci_driver driver = {
    .name = KBUILD_MODNAME,
    .id_table = snd_mychip_ids,
    .probe = snd_mychip_probe,
    .remove = snd_mychip_remove,
};

// 模块初始化
static int __init alsa_card_mychip_init(void)
{
    return pci_register_driver(&driver);
}

// 模块清理
static void __exit alsa_card_mychip_exit(void)
{
    pci_unregister_driver(&driver);
}

module_init(alsa_card_mychip_init)
module_exit(alsa_card_mychip_exit)

EXPORT_NO_SYMBOLS; /* 仅适用于旧内核版本 */

// 一些注意事项
// --------------

// PCI资源的分配在“probe”函数中完成，并且通常为此目的编写一个额外的 :c:func:`xxx_create()` 函数
// 在PCI设备的情况下，分配资源前必须调用 :c:func:`pci_enable_device()` 函数。
// 同时需要设置适当的PCI DMA掩码来限制可访问的I/O范围。在某些情况下，你可能还需要调用 :c:func:`pci_set_master()` 函数
```

这段代码示例详细展示了如何为自定义声卡驱动程序在Linux内核中实现PCI资源管理和设备实例的创建与销毁过程。
假设一个28位的掩码，需要添加的代码如下所示：

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
---------

I/O端口和中断的分配是通过标准内核函数完成的。这些资源必须在析构函数中释放（参见下文）。
现在假设PCI设备有一个8字节的I/O端口和一个中断。那么struct mychip将具有以下字段：

  ```c
  struct mychip {
          struct snd_card *card;

          unsigned long port;
          int irq;
  };
  ```

对于I/O端口（以及内存区域），你需要拥有用于标准资源管理的资源指针。对于中断，你只需要保留中断号（整数）。但在实际分配之前，你需要将这个数字初始化为-1，因为中断号0是有效的。端口地址及其资源指针可以通过`:c:func:`kzalloc()`自动初始化为null，因此你不必关心重置它们。
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
返回值`chip->port`通过`:c:func:`kmalloc()`由`:c:func:`request_region()`分配。该指针必须通过`:c:func:`kfree()`释放，但这里存在一个问题。这个问题将在稍后解释。
中断源的分配如下所示：

  ```c
  if (request_irq(pci->irq, snd_mychip_interrupt,
                  IRQF_SHARED, KBUILD_MODNAME, chip)) {
          printk(KERN_ERR "无法获取中断号%d\n", pci->irq);
          snd_mychip_free(chip);
          return -EBUSY;
  }
  chip->irq = pci->irq;
  ```

其中`:c:func:`snd_mychip_interrupt()`是在`稍后定义的中断处理程序`__。请注意，`chip->irq`应该仅在`:c:func:`request_irq()`成功时定义。
在PCI总线上，中断可以共享。因此，在`:c:func:`request_irq()`中使用`IRQF_SHARED`作为中断标志。
`:c:func:`request_irq()`的最后一个参数是传递给中断处理程序的数据指针。通常，特定于芯片的记录用于此目的，但你也可以使用任何你喜欢的内容。
此时我不会详细介绍中断处理程序，但至少可以解释其外观。中断处理程序通常如下所示：

  ```c
  static irqreturn_t snd_mychip_interrupt(int irq, void *dev_id)
  {
          struct mychip *chip = dev_id;
          ...
          return IRQ_HANDLED;
  }
  ```

请求IRQ之后，你可以将其传递给`card->sync_irq`字段：

  ```c
          card->irq = chip->irq;
  ```

这允许PCM核心在适当的时候自动调用`:c:func:`synchronize_irq()`，例如在`hw_free`之前。
有关详细信息，请参阅后面的`同步停止回调`_部分。
现在让我们为上面提到的资源编写相应的析构函数。
析构函数的作用很简单：如果已经激活，则禁用硬件，并释放资源。到目前为止，我们还没有硬件部分，因此禁用代码在这里不编写。
为了释放资源，“检查并释放”的方法是一种更安全的方式。
对于中断，可以这样做：

  如果 (chip->irq >= 0)
          free_irq(chip->irq, chip);

由于中断号可以从0开始，你应该使用一个负值（例如-1）初始化 `chip->irq`，这样你就可以像上面那样检查中断号的有效性。
当你通过 `pci_request_region()` 或 `pci_request_regions()` 函数请求I/O端口或内存区域，如本例所示，使用对应的函数 `pci_release_region()` 或 `pci_release_regions()` 来释放这些资源：

  pci_release_regions(chip->pci);

如果你是手动通过 `request_region()` 或 `request_mem_region()` 请求的，你可以通过 `release_resource()` 来释放它。假设你将 `request_region()` 返回的资源指针保存在 `chip->res_port` 中，那么释放过程如下：

  release_and_free_resource(chip->res_port);

不要忘记在最后调用 `pci_disable_device()`。
最后，释放芯片特定的数据结构：

  kfree(chip);

我们没有实现上面提到的硬件禁用部分。如果你需要做这个，请注意析构函数可能在芯片初始化完成之前就被调用。最好有一个标志来跳过硬件禁用，如果硬件尚未初始化的话。
当使用 `snd_device_new()` 并带有 `SNDRV_DEV_LOWLEVEL` 参数将芯片数据分配给设备时，其析构函数最后被调用。也就是说，在所有其他组件（如 PCM 和控制）已经被释放之后，才确保会调用这个析构函数。你不需要显式地停止 PCM 等组件，只需调用低级硬件停止即可。
管理内存映射区域几乎与管理 I/O 端口相同。你需要以下两个字段：

  struct mychip {
          ...
unsigned long iobase_phys;
          void __iomem *iobase_virt;
  };

分配的过程如下：

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
### PCI区域释放与映射

当然，使用 `pci_iomap()` 函数会使得事情变得简单一些，例如：

```c
err = pci_request_regions(pci, "My Chip");
if (err < 0) {
        kfree(chip);
        return err;
}
chip->iobase_virt = pci_iomap(pci, 0, 0);
```

这需要在析构函数中配对调用 `pci_iounmap()`。

### PCI 设备条目

到现在为止，一切进展顺利。让我们完成剩余的 PCI 相关工作。首先，我们需要为这个芯片组创建一个 `struct pci_device_id` 表。这是一个包含 PCI 厂商/设备ID号以及一些掩码的表。例如：

```c
static struct pci_device_id snd_mychip_ids[] = {
        { PCI_VENDOR_ID_FOO, PCI_DEVICE_ID_BAR,
          PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0, },
        ...
{ 0, }
};
MODULE_DEVICE_TABLE(pci, snd_mychip_ids);
```

`struct pci_device_id` 的前两个字段是厂商和设备ID。如果你没有特别的理由去过滤匹配的设备，你可以像上面那样保留其余字段。`struct pci_device_id` 的最后一个字段可以存储私有数据以供该条目使用。你可以在其中指定任何值，例如，为支持的设备ID定义特定的操作。在 intel8x0 驱动中有一个这样的例子。
列表的最后一条记录是一个终结符。你必须指定这样一个全零记录。

然后，准备 `struct pci_driver` 结构体记录：

```c
static struct pci_driver driver = {
        .name = KBUILD_MODNAME,
        .id_table = snd_mychip_ids,
        .probe = snd_mychip_probe,
        .remove = snd_mychip_remove,
};
```

`probe` 和 `remove` 函数已经在前面的部分中定义过了。`name` 字段是此设备的名称字符串。请注意，你不能在此字符串中使用斜杠（"/"）。

最后，模块入口点：

```c
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
```

请注意这些模块入口点被标记上了 `__init` 和 `__exit` 前缀。

### PCM 接口

#### 一般性介绍

ALSA 的 PCM 中间层非常强大，每个驱动只需要实现访问其硬件的低级函数即可。

为了访问 PCM 层，你需要首先包含 `<sound/pcm.h>`。此外，如果你要访问与 `hw_param` 相关的一些函数，可能还需要包含 `<sound/pcm_params.h>`。
每个卡设备最多可以有四个PCM实例。一个PCM实例对应一个PCM设备文件。实例数量的限制仅来自于Linux设备号可用的位大小。
一旦使用了64位的设备号，我们将会有更多的PCM实例可用。

一个PCM实例由PCM播放和捕获流组成，而每一个PCM流又包含一个或多个PCM子流。一些声卡支持多种播放功能。例如，emu10k1具有32个立体声音频子流的PCM播放功能。在这种情况下，每次打开时，通常会自动选择并打开一个空闲的子流。同时，如果只有一个子流存在并且已经被打开，那么后续的打开操作要么被阻塞，要么返回“EAGAIN”错误，这取决于文件打开模式。但是，在你的驱动程序中不必关心这些细节。PCM中间层将处理这些工作。

完整代码示例
--------------

下面的示例代码没有包括任何硬件访问例程，仅展示了如何构建PCM接口的基本框架：

```c
#include <sound/pcm.h>
...

/* 硬件定义 */
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

/* 硬件定义 */
static struct snd_pcm_hardware snd_mychip_capture_hw = {
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

/* 打开回调 */
static int snd_mychip_playback_open(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        struct snd_pcm_runtime *runtime = substream->runtime;

        runtime->hw = snd_mychip_playback_hw;
        /* 这里将进行更多硬件初始化 */
        ...
return 0;
}

/* 关闭回调 */
static int snd_mychip_playback_close(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        /* 这里将放置与硬件相关的代码 */
        ...
return 0;
}

/* 打开回调 */
static int snd_mychip_capture_open(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        struct snd_pcm_runtime *runtime = substream->runtime;

        runtime->hw = snd_mychip_capture_hw;
        /* 这里将进行更多硬件初始化 */
        ...
return 0;
}

/* 关闭回调 */
static int snd_mychip_capture_close(struct snd_pcm_substream *substream)
{
        struct mychip *chip = snd_pcm_substream_chip(substream);
        /* 这里将放置与硬件相关的代码 */
        ...
return 0;
}

/* hw_params 回调 */
static int snd_mychip_pcm_hw_params(struct snd_pcm_substream *substream,
                                 struct snd_pcm_hw_params *hw_params)
{
        /* 这里将放置与硬件相关的代码 */
        ...
return 0;
}

/* hw_free 回调 */
static int snd_mychip_pcm_hw_free(struct snd_pcm_substream *substream)
{
        /* 这里将放置与硬件相关的代码 */
        ...
}
```

这段代码展示了如何为播放和捕获设置硬件参数，并且定义了相应的回调函数来处理打开、关闭、参数设置等操作。
### 返回0;
      }

      /// 准备回调函数
      static int snd_mychip_pcm_prepare(struct snd_pcm_substream *substream)
      {
              struct mychip *chip = snd_pcm_substream_chip(substream);
              struct snd_pcm_runtime *runtime = substream->runtime;

              /// 根据当前配置设置硬件
              /// 例如...
              mychip_set_sample_format(chip, runtime->format);
              mychip_set_sample_rate(chip, runtime->rate);
              mychip_set_channels(chip, runtime->channels);
              mychip_set_dma_setup(chip, runtime->dma_addr,
                                   chip->buffer_size,
                                   chip->period_size);
              return 0;
      }

      /// 触发回调函数
      static int snd_mychip_pcm_trigger(struct snd_pcm_substream *substream,
                                        int cmd)
      {
              switch (cmd) {
              case SNDRV_PCM_TRIGGER_START:
                      /// 执行一些启动PCM引擎的操作
                      ...
                      break;
              case SNDRV_PCM_TRIGGER_STOP:
                      /// 执行一些停止PCM引擎的操作
                      ...
                      break;
              default:
                      return -EINVAL;
              }
      }

      /// 指针回调函数
      static snd_pcm_uframes_t
      snd_mychip_pcm_pointer(struct snd_pcm_substream *substream)
      {
              struct mychip *chip = snd_pcm_substream_chip(substream);
              unsigned int current_ptr;

              /// 获取当前硬件指针
              current_ptr = mychip_get_hw_pointer(chip);
              return current_ptr;
      }

      /// 操作符
      static struct snd_pcm_ops snd_mychip_playback_ops = {
              .open =        snd_mychip_playback_open,
              .close =       snd_mychip_playback_close,
              .hw_params =   snd_mychip_pcm_hw_params,
              .hw_free =     snd_mychip_pcm_hw_free,
              .prepare =     snd_mychip_pcm_prepare,
              .trigger =     snd_mychip_pcm_trigger,
              .pointer =     snd_mychip_pcm_pointer,
      };

      /// 操作符
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
       * 录音定义在这里省略..
*/

      /// 创建一个PCM设备
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
              /// 设置操作符
              snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK,
                              &snd_mychip_playback_ops);
              snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE,
                              &snd_mychip_capture_ops);
              /// 预分配缓冲区
              /// 注意：这可能会失败
              snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV,
                                             &chip->pci->dev,
                                             64*1024, 64*1024);
              return 0;
      }


PCM 构造器
--------------

一个PCM实例由函数 :c:func:`snd_pcm_new()` 分配。最好是为PCM创建一个构造器，例如：

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

函数 :c:func:`snd_pcm_new()` 接受六个参数。第一个参数是该PCM分配的声卡指针，第二个参数是ID字符串。
第三个参数（`index`，在上面的例子中为0）是新PCM的索引号。它从0开始。如果你创建了多个PCM实例，则需要为此参数指定不同的数字。例如，对于第二个PCM设备，`index = 1`。
第四和第五个参数分别是播放和录音子流的数量。这里都使用了1。如果没有播放或录音子流可用，则将0传递给相应的参数。
如果芯片支持多个播放或录音，则可以指定更多的数量，但在打开/关闭等回调函数中必须妥善处理这些数量。当你需要知道你正在引用哪个子流时，可以通过以下方式从传递给每个回调函数的 `struct snd_pcm_substream` 数据中获取它：

```c
  struct snd_pcm_substream *substream;
  int index = substream->number;
```


创建PCM之后，你需要为每个PCM流设置操作符：

```c
  snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK,
                  &snd_mychip_playback_ops);
  snd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE,
                  &snd_mychip_capture_ops);
```

操作符通常像这样定义：

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

所有回调函数都在“操作符”小节中进行了描述。
设置操作符后，你可能想要预先分配缓冲区并设置托管分配模式。为此，只需调用以下函数：

  snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV,
                                 &chip->pci->dev,
                                 64*1024, 64*1024);

这将默认分配一个最多64kB的缓冲区。缓冲区管理的详细信息将在后面的`缓冲区和内存管理`_部分中描述。
此外，你还可以在`pcm->info_flags`中为这个PCM设置一些额外的信息。可用的值定义在`<sound/asound.h>`中的`SNDRV_PCM_INFO_XXX`，这些用于硬件定义（稍后会描述）。如果你的声音芯片仅支持半双工，可以这样指定：

  pcm->info_flags = SNDRV_PCM_INFO_HALF_DUPLEX;

...以及析构函数？
-------------------

对于PCM实例的析构函数并非总是必要的。由于PCM设备将由中间层代码自动释放，因此你不必显式调用析构函数。
如果内部创建了特殊记录并且需要释放它们，则需要析构函数。在这种情况下，将析构函数设置为`pcm->private_free`：

      static void mychip_pcm_free(struct snd_pcm *pcm)
      {
              struct mychip *chip = snd_pcm_chip(pcm);
              /* 释放你自己的数据 */
              kfree(chip->my_private_pcm_data);
              /* 进行其他你喜欢的操作 */
              ...
      }

      static int snd_mychip_new_pcm(struct mychip *chip)
      {
              struct snd_pcm *pcm;
              ...
/* 分配你自己的数据 */
              chip->my_private_pcm_data = kmalloc(...);
              /* 设置析构函数 */
              pcm->private_data = chip;
              pcm->private_free = mychip_pcm_free;
              ...
}

运行时指针 — PCM信息的宝箱
--------------------------------

当PCM子流被打开时，会分配一个PCM运行时实例，并将其分配给子流。可以通过`substream->runtime`访问此运行时指针。此运行时指针包含了控制PCM所需的大部分信息：hw_params 和 sw_params 配置的副本、缓冲区指针、mmap记录、自旋锁等。
可以在`<sound/pcm.h>`中找到运行时实例的定义。以下是该文件的相关部分：

  struct _snd_pcm_runtime {
          /* -- 状态 -- */
          struct snd_pcm_substream *trigger_master;
          snd_timestamp_t trigger_tstamp;	/* 触发时间戳 */
          int overrange;
          snd_pcm_uframes_t avail_max;
          snd_pcm_uframes_t hw_ptr_base;	/* 缓冲区重启时的位置 */
          snd_pcm_uframes_t hw_ptr_interrupt; /* 中断时的位置*/

          /* -- 硬件参数 -- */
          snd_pcm_access_t access;	/* 访问模式 */
          snd_pcm_format_t format;	/* SNDRV_PCM_FORMAT_* */
          snd_pcm_subformat_t subformat;	/* 子格式 */
          unsigned int rate;		/* 每秒采样率 */
          unsigned int channels;		/* 通道数 */
          snd_pcm_uframes_t period_size;	/* 周期大小 */
          unsigned int periods;		/* 周期数 */
          snd_pcm_uframes_t buffer_size;	/* 缓冲区大小 */
          unsigned int tick_time;		/* tick时间 */
          snd_pcm_uframes_t min_align;	/* 格式的最小对齐 */
          size_t byte_align;
          unsigned int frame_bits;
          unsigned int sample_bits;
          unsigned int info;
          unsigned int rate_num;
          unsigned int rate_den;
  
          /* -- 软件参数 -- */
          struct timespec tstamp_mode;	/* mmap时间戳更新 */
          unsigned int period_step;
          unsigned int sleep_min;		/* 最小tick数以睡眠 */
          snd_pcm_uframes_t start_threshold;
          /*
           * 下面两个阈值可以缓解播放缓冲区的欠读；当
           * hw_avail低于阈值时，将触发相应的动作：
           */
          snd_pcm_uframes_t stop_threshold;	/* - 停止播放 */
          snd_pcm_uframes_t silence_threshold;	/* - 预填充缓冲区静音 */
          snd_pcm_uframes_t silence_size;       /* 静音预填充的最大大小；当>=边界时，
                                                 * 立即用静音填充已播放区域 */
          snd_pcm_uframes_t boundary;	/* 指针包裹点 */

          /* 自动静音器的内部数据 */
          snd_pcm_uframes_t silence_start; /* 开始静音区域的指针 */
          snd_pcm_uframes_t silence_filled; /* 已填充的静音大小 */

          snd_pcm_sync_id_t sync;		/* 硬件同步ID */

          /* -- 内存映射 -- */
          volatile struct snd_pcm_mmap_status *status;
          volatile struct snd_pcm_mmap_control *control;
          atomic_t mmap_count;

          /* -- 锁定 / 调度 -- */
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
          unsigned int timer_resolution;	/* 定时器分辨率 */

          /* -- DMA -- */
          unsigned char *dma_area;	/* DMA区域 */
          dma_addr_t dma_addr;		/* 物理总线地址（主CPU无法访问） */
          size_t dma_bytes;		/* DMA区域大小 */

          struct snd_dma_buffer *dma_buffer_p;	/* 分配的缓冲区 */

  #if defined(CONFIG_SND_PCM_OSS) || defined(CONFIG_SND_PCM_OSS_MODULE)
          /* -- OSS相关 -- */
          struct snd_pcm_oss_runtime oss;
  #endif
  };

对于每个声音驱动程序的操作符（回调），这些记录大多应该是只读的。只有PCM中间层更改/更新它们。例外是硬件描述（hw）、DMA缓冲区信息和私有数据。除此之外，如果你使用标准的托管缓冲区分配模式，则无需自己设置DMA缓冲区信息。

在下面的部分中，解释了一些重要的记录。
硬件描述
~~~~~~~~~

硬件描述符（struct snd_pcm_hardware）包含基本硬件配置的定义。最重要的是，你需要在`PCM打开回调`_中定义它。请注意，运行时实例持有描述符的一个副本，而不是指向现有描述符的指针。也就是说，在打开回调中，你可以根据需要修改复制的描述符（`runtime->hw`）。例如，如果某些芯片模型上的最大通道数仅为1，则仍然可以使用相同的硬件描述符并在之后更改channels_max： 

          struct snd_pcm_runtime *runtime = substream->runtime;
          ..
The following translation provides the equivalent text in Chinese:

将 `runtime->hw` 设置为 `snd_mychip_playback_hw`; /* 公共定义 */
如果 `chip->model` 等于 `VERY_OLD_ONE`，
那么 `runtime->hw.channels_max` 应设置为 1。

通常情况下，硬件描述符如下所示：

```c
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
```

- `info` 字段包含了此 PCM 的类型和能力。位标志在 `<sound/asound.h>` 中定义为 `SNDRV_PCM_INFO_XXX`。至少，你需要指定是否支持 mmap 以及支持哪种交错格式。如果硬件支持 mmap，则需要添加 `SNDRV_PCM_INFO_MMAP` 标志。如果硬件支持交错或非交错格式，则必须分别设置 `SNDRV_PCM_INFO_INTERLEAVED` 或 `SNDRV_PCM_INFO_NONINTERLEAVED` 标志。如果两者都支持，则可以同时设置。
在上述示例中，指定了 `MMAP_VALID` 和 `BLOCK_TRANSFER` 用于 OSS mmap 模式。通常两者都会被设置。当然，只有当真正支持 mmap 时才设置 `MMAP_VALID`。
其他可能的标志是 `SNDRV_PCM_INFO_PAUSE` 和 `SNDRV_PCM_INFO_RESUME`。`PAUSE` 标志意味着 PCM 支持“暂停”操作，而 `RESUME` 标志则意味着支持完整的“挂起/恢复”操作。如果设置了 `PAUSE` 标志，则下面的 `trigger` 回调函数必须处理相应的（暂停推/释放）命令。即使没有设置 `RESUME` 标志，也可以定义挂起/恢复触发命令。详情请参阅 `电源管理` 部分。
如果 PCM 子流可以同步（通常是播放和捕获流的同步启动/停止），还可以给出 `SNDRV_PCM_INFO_SYNC_START`。在这种情况下，你可能需要在 `trigger` 回调函数中检查 PCM 子流的链表。这将在后面的章节中进行说明。
- `formats` 字段包含支持的格式位标志（`SNDRV_PCM_FMTBIT_XXX`）。如果硬件支持多种格式，则应提供所有或运算的位。在上面的例子中，指定了带符号的 16 位小端格式。
- `rates` 字段包含支持的采样率位标志（`SNDRV_PCM_RATE_XXX`）。如果芯片支持连续的采样率，还需传递 `CONTINUOUS` 位。预定义的采样率位仅适用于典型采样率。如果你的芯片支持非常规采样率，则需要添加 `KNOT` 位，并手动设置硬件约束（稍后解释）。
- `rate_min` 和 `rate_max` 定义了最小和最大的采样率。这应该与 `rates` 位相对应。
- `channels_min` 和 `channels_max` 定义了最小和最大的声道数。
- `buffer_bytes_max` 定义了缓冲区的最大字节数。没有 `buffer_bytes_min` 字段，因为它可以从最小周期大小和最小周期数计算得出。同时，`period_bytes_min` 和 `period_bytes_max` 定义了周期的最小和最大字节数。
- `periods_max` 和 `periods_min` 定义了缓冲区中的最大和最小周期数。
“周期”一词在 OSS 世界中对应于一个片段。周期定义了生成 PCM 中断的点。这个点强烈依赖于硬件。通常，较小的周期大小会带来更多的中断，这使得能够更及时地填充/排空缓冲区。在捕获的情况下，此大小定义了输入延迟。另一方面，整个缓冲区大小定义了播放方向上的输出延迟。

- 还有一个字段 `fifo_size`。它指定了硬件 FIFO 的大小，但目前既没有被驱动程序使用，也没有在 alsa-lib 中使用。因此，您可以忽略这个字段。

PCM 配置
~~~~~~~~~

好的，让我们再次回到 PCM 运行时记录。运行实例中最常引用的记录是 PCM 配置。应用程序通过 alsa-lib 发送 `hw_params` 数据后，PCM 配置存储在运行实例中。从 `hw_params` 和 `sw_params` 结构体中有许多字段被复制过来。例如，`format` 字段保存由应用程序选择的格式类型。该字段包含枚举值 `SNDRV_PCM_FORMAT_XXX`。

需要注意的一点是，配置的缓冲区和周期大小以“帧”形式存储在运行时中。在 ALSA 世界里，`1 帧 = 通道数 * 样本大小`。为了在帧和字节之间进行转换，您可以使用辅助函数 :c:func:`frames_to_bytes()` 和 :c:func:`bytes_to_frames()`，例如：

  period_bytes = frames_to_bytes(runtime, runtime->period_size);

此外，许多软件参数（sw_params）也以帧的形式存储。
请检查字段的类型。`snd_pcm_uframes_t` 是用于帧的无符号整数，而 `snd_pcm_sframes_t` 是用于帧的有符号整数。

DMA 缓冲信息
~~~~~~~~~~~~

DMA 缓冲区由以下四个字段定义：`dma_area`、`dma_addr`、`dma_bytes` 和 `dma_private`。`dma_area` 持有缓冲区指针（逻辑地址）。您可以从此指针调用 :c:func:`memcpy()`。同时，`dma_addr` 持有缓冲区的物理地址。当缓冲区为线性缓冲区时，才指定此字段。`dma_bytes` 持有缓冲区的字节大小。`dma_private` 用于 ALSA DMA 分配器。

如果您使用管理缓冲区分配模式或标准 API 函数 :c:func:`snd_pcm_lib_malloc_pages()` 来分配缓冲区，则这些字段将由 ALSA 中间层设置，您不应自行更改它们。您可以读取它们，但不能写入。另一方面，如果您想自己分配缓冲区，您需要在 hw_params 回调中管理它。至少，`dma_bytes` 是必需的。当缓冲区被内存映射时，`dma_area` 是必要的。如果您的驱动程序不支持内存映射，则此字段不是必需的。`dma_addr` 也是可选的。您可以随意使用 `dma_private`。

运行状态
~~~~~~~~

运行状态可以通过 `runtime->status` 引用。这是一个指向 `struct snd_pcm_mmap_status` 记录的指针。

例如，您可以通过 `runtime->status->hw_ptr` 获取当前 DMA 硬件指针。

DMA 应用程序指针可以通过 `runtime->control` 引用，它指向 `struct snd_pcm_mmap_control` 记录。
然而，直接访问这个值并不推荐。
私有数据
~~~~~~~~~~~~

你可以为子流分配一个记录，并将其存储在``runtime->private_data``中。通常，这在`PCM打开回调`_中完成。不要将此与``pcm->private_data``混合使用。``pcm->private_data``通常指向在创建PCM设备时静态分配的芯片实例，而``runtime->private_data``则指向在PCM打开回调中创建的动态数据结构，如下所示：

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

所分配的对象必须在`关闭回调`_中释放。
操作符
---------

好的，现在让我详细说明每个PCM回调（``ops``）。一般来说，如果成功，每个回调都必须返回0；若失败，则返回一个负错误号，例如``-EINVAL``。为了选择合适的错误号，建议检查内核其他部分在类似请求失败时返回的值。

每个回调函数至少接受一个参数，其中包含一个struct snd_pcm_substream指针。要从给定的子流实例中获取芯片记录，可以使用以下宏：

```c
  int xxx(...) {
          struct mychip *chip = snd_pcm_substream_chip(substream);
          ...
}
```

该宏读取``substream->private_data``，这是``pcm->private_data``的一个副本。如果你需要为每个PCM子流分配不同的数据记录，可以覆盖前者。例如，cmi8330驱动程序为播放和捕获方向分配了不同的``private_data``，因为它使用两种不同的编解码器（SB-兼容和AD-兼容）来处理不同方向的数据。
PCM打开回调
~~~~~~~~~~~~~~~~~

```c
  static int snd_xxx_open(struct snd_pcm_substream *substream);
```

当打开PCM子流时会调用此函数。
至少，在这里你需要初始化``runtime->hw``记录。通常，这会像下面这样实现：

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

你可以在该回调中分配私有数据，如“私有数据”_部分所述。
如果硬件配置需要更多的限制条件，在这里也设置硬件限制。有关更多详细信息，请参阅 _Constraints_。
关闭回调
~~~~~~~~~~~~~~

::
  
  static int snd_xxx_close(struct snd_pcm_substream *substream);

很明显，当PCM子流被关闭时会调用这个函数。
在`open`回调中为PCM子流分配的任何私有实例将在这里释放： 

::
  
  static int snd_xxx_close(struct snd_pcm_substream *substream)
  {
          ...
kfree(substream->runtime->private_data);
          ...
}

ioctl回调
~~~~~~~~~~~~~~

这用于处理任何对PCM ioctl的特殊调用。但是通常你可以将其设为NULL，这样PCM核心将调用通用ioctl回调函数 :c:func:`snd_pcm_lib_ioctl()`。 如果你需要处理一个独特的通道信息设置或重置过程，你可以在这里传递你自己的回调函数。
hw_params回调
~~~~~~~~~~~~~~~~~~~

::
  
  static int snd_xxx_hw_params(struct snd_pcm_substream *substream,
                               struct snd_pcm_hw_params *hw_params);

当应用程序设置硬件参数（`hw_params`）时，会调用此函数，即在缓冲区大小、周期大小、格式等为PCM子流定义后调用一次。
许多硬件设置应该在这个回调中完成，包括缓冲区的分配。
初始化所需的参数可以通过`:c:func:`params_xxx()`宏获取。
当你选择为子流管理缓冲区分配模式时，在这个回调被调用之前，一个缓冲区已经分配好了。或者，你可以通过下面的辅助函数来分配缓冲区：

::
  
  snd_pcm_lib_malloc_pages(substream, params_buffer_bytes(hw_params));

`:c:func:`snd_pcm_lib_malloc_pages()`仅在DMA缓冲区预先分配的情况下可用。更多细节请参阅`缓冲区类型`_部分。
请注意，这个回调和`prepare`回调可能在初始化过程中被多次调用。例如，OSS仿真可能会在每次通过其ioctl更改时调用这些回调。
因此，你需要小心不要多次分配相同的缓冲区，这将导致内存泄漏！多次调用上面的辅助函数是可以的。当已经分配了缓冲区时，它会自动释放之前的缓冲区。
另外需要注意的是，默认情况下此回调是非原子性的（可调度的），即没有设置`nonatomic`标志。这一点很重要，因为`trigger`回调是原子性的（不可调度的）。也就是说，在`trigger`回调中不能使用互斥锁或任何与调度相关的功能。请参阅子节“Atomicity_”以获取更多详细信息。

`hw_free` 回调
~~~~~~~~~~~~~~~~~

```
static int snd_xxx_hw_free(struct snd_pcm_substream *substream);
```

这个函数被调用来释放通过`hw_params`分配的资源。
该函数总是在关闭回调被调用之前被调用。
同时，该回调也可能被多次调用。你需要跟踪每项资源是否已经被释放。
当你为PCM子流选择了管理缓冲区分配模式时，在该回调被调用后，已分配的PCM缓冲区会被自动释放。否则你必须手动释放缓冲区。通常情况下，如果缓冲区是从预分配池中分配的，你可以使用标准API函数`c:func:`snd_pcm_lib_malloc_pages()`来释放，例如：

```
snd_pcm_lib_free_pages(substream);
```

`prepare`回调
~~~~~~~~~~~~~~~~~

```
static int snd_xxx_prepare(struct snd_pcm_substream *substream);
```

当PCM处于“准备”状态时调用此回调。你可以在这里设置格式类型、采样率等。与`hw_params`的不同之处在于，`prepare`回调将在每次调用`c:func:`snd_pcm_prepare()`时被调用，例如在从欠取样恢复等情况时。
请注意，此回调也是非原子性的。你可以在该回调中安全地使用与调度相关的功能。
在此和以下的回调中，你可以通过运行时记录`substream->runtime`来引用这些值。例如，要获取当前的速率、格式或通道数，请访问`runtime->rate`、`runtime->format`或`runtime->channels`。已分配缓冲区的物理地址被设置为`runtime->dma_area`。缓冲区和周期的大小分别位于`runtime->buffer_size`和`runtime->period_size`中。
需要注意的是，此回调也会在每次设置时被多次调用。

`trigger`回调
~~~~~~~~~~~~~~~~~

```
static int snd_xxx_trigger(struct snd_pcm_substream *substream, int cmd);
```

当PCM开始、停止或暂停时调用此函数。
操作在第二个参数中指定，即在`<sound/pcm.h>`中定义的`SNDRV_PCM_TRIGGER_XXX`。至少，“START”和“STOP”命令必须在这个回调中定义，如下所示：

```c
switch (cmd) {
  case SNDRV_PCM_TRIGGER_START:
          /* 执行一些启动PCM引擎的操作 */
          break;
  case SNDRV_PCM_TRIGGER_STOP:
          /* 执行一些停止PCM引擎的操作 */
          break;
  default:
          return -EINVAL;
}
```

如果PCM支持暂停操作（硬件表的信息字段中给出），则也必须处理“PAUSE_PUSH”和“PAUSE_RELEASE”命令。前者是暂停PCM的命令，后者则是重新启动PCM的命令。
如果PCM支持挂起/恢复操作，无论是否支持完全或部分挂起/恢复，都必须处理“SUSPEND”和“RESUME”命令。这些命令是在电源管理状态发生改变时发出的。显然，“SUSPEND”和“RESUME”命令分别挂起和恢复PCM子流，并且通常它们等同于“STOP”和“START”命令。详情请参阅`电源管理`_部分。

如前所述，除非设置了`nonatomic`标志，否则此回调默认是原子性的，你不能调用可能休眠的函数。`trigger`回调应尽可能简洁，只真正触发DMA。其他工作应在`hw_params`和`prepare`回调中适当地初始化。

### sync_stop 回调

```c
static int snd_xxx_sync_stop(struct snd_pcm_substream *substream);
```

此回调是可选的，可以传递NULL。它在PCM核心停止流之后、通过`prepare`、`hw_params`或`hw_free`改变流状态之前被调用。
由于中断处理程序可能仍在等待执行，因此我们需要等到待处理任务完成后再进入下一步；否则可能会因为资源冲突或访问已释放资源而导致崩溃。典型的行为是在这里调用同步函数，例如：:c:func:`synchronize_irq()`。

对于大多数只需要调用:c:func:`synchronize_irq()`的驱动程序，还有一个更简单的设置方法。
保持`sync_stop` PCM回调为NULL的同时，驱动程序可以在请求IRQ后将返回的中断号设置到`card->sync_irq`字段。这样，PCM核心会适当使用给定的IRQ调用:c:func:`synchronize_irq()`。

如果中断处理程序由卡的析构函数释放，则无需清除`card->sync_irq`，因为卡本身正在被释放。
因此，通常你只需在驱动程序代码中添加一行来分配`card->sync_irq`，除非驱动程序重新获取IRQ。当驱动程序动态地释放并重新获取IRQ时（例如，在挂起/恢复期间），需要适当地清除和重新设置`card->sync_irq`。
指针回调
~~~~~~~~~

::

  static snd_pcm_uframes_t snd_xxx_pointer(struct snd_pcm_substream *substream)

此回调函数在PCM中间层查询缓冲区中的当前硬件位置时被调用。返回的位置必须以帧为单位，范围从0到`buffer_size - 1`。

此回调通常由PCM中间层的缓冲区更新例程调用，该例程是在中断例程调用:c:func:`snd_pcm_period_elapsed()`时触发的。随后，PCM中间层会更新位置并计算可用空间，并唤醒睡眠中的轮询线程等。
此回调默认是原子性的。

复制和填充静音操作
~~~~~~~~~~~~~~~~~~~~~~~~~

这些回调不是强制性的，在大多数情况下可以省略。
当硬件缓冲区不能位于正常内存空间中时，需要使用这些回调。有些芯片有自己的硬件缓冲区，这些缓冲区不可映射。在这种情况下，你必须手动将数据从内存缓冲区传输到硬件缓冲区。或者，如果缓冲区在物理和虚拟内存空间上都是非连续的，也必须定义这些回调。
如果定义了这两个回调，复制和设置静音操作将通过它们完成。详细内容将在后面的`缓冲区与内存管理`_部分描述。

确认回调
~~~~~~~~~~~~

此回调也不是强制性的。此回调在`appl_ptr`在读写操作中更新时被调用。像emu10k1-fx和cs46xx这样的驱动程序需要跟踪内部缓冲区中的当前`appl_ptr`，而此回调仅适用于此类目的。
回调函数可能返回0或负错误值。当返回值为`-EPIPE`时，PCM核心将其视为缓冲区溢出（XRUN），并自动将状态更改为`SNDRV_PCM_STATE_XRUN`。
此回调默认是原子性的。

页回调
~~~~~~~~~~~~~

此回调也是可选的。mmap调用此回调来获取页错误地址。
对于标准的SG缓冲区或vmalloc缓冲区，你无需特别的回调。因此，此回调应该很少使用。
### mmap 回调

这是另一个可选的回调，用于控制 mmap 行为。
当定义时，PCM 核心会在页面被内存映射时调用此回调，而不是使用标准辅助函数。
如果你需要特殊处理（由于某些架构或设备特定问题），请在这里按照你的喜好实现所有内容。

### PCM 中断处理器
---

PCM 相关的其余部分是 PCM 中断处理器。在声卡驱动程序中，PCM 中断处理器的作用是更新缓冲区位置，并在缓冲区位置跨过指定周期边界时通知 PCM 中间层。为了通知这一点，可以调用 `snd_pcm_period_elapsed()` 函数。

有几种方式声卡芯片可以生成中断：

#### 在周期（片段）边界处的中断
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

这是最常见的类型：硬件在每个周期边界生成一个中断。在这种情况下，你可以在每次中断时调用 `snd_pcm_period_elapsed()`。

`snd_pcm_period_elapsed()` 以子流指针作为其参数。因此，你需要保持子流指针可以从芯片实例中访问。例如，在芯片记录中定义 `substream` 字段来保存当前运行中的子流指针，并在 `open` 回调中设置指针值（并在 `close` 回调中重置）。

如果你在中断处理器中获取了自旋锁，并且该锁也在其他 PCM 回调中使用，则在调用 `snd_pcm_period_elapsed()` 之前必须释放锁，因为 `snd_pcm_period_elapsed()` 会调用其他 PCM 回调函数。

典型的代码如下所示:

```c
static irqreturn_t snd_mychip_interrupt(int irq, void *dev_id)
{
    struct mychip *chip = dev_id;
    spin_lock(&chip->lock);
    ...

    if (pcm_irq_invoked(chip)) {
        /* 调用更新器，调用前解锁 */
        spin_unlock(&chip->lock);
        snd_pcm_period_elapsed(chip->substream);
        spin_lock(&chip->lock);
        /* 如果需要的话，确认中断 */
    }
    ...
}
```
翻译如下：

解锁 `chip->lock` 旋锁并返回 IRQ_HANDLED。

```c
      spin_unlock(&chip->lock);
      return IRQ_HANDLED;
}
```

当设备能够检测到缓冲区欠溢/过溢时，驱动程序可以通过调用 `snd_pcm_stop_xrun()` 函数来通知 PCM 核心 XRUN 状态。此函数会停止流并将 PCM 状态设置为 `SNDRV_PCM_STATE_XRUN`。请注意，该函数必须在 PCM 流锁之外调用，因此不能从原子回调中调用。
### 高频定时器中断

当硬件不在周期边界生成中断，而是在固定频率的定时器中断发出时（例如 es1968 或 ymfpci 驱动程序），你需要在每次中断时检查当前的硬件位置并累积处理过的样本长度。当累积的大小超过周期大小时，调用 `snd_pcm_period_elapsed()` 并重置累积器。典型的代码如下所示：

```c
static irqreturn_t snd_mychip_interrupt(int irq, void *dev_id)
{
    struct mychip *chip = dev_id;
    spin_lock(&chip->lock);
    ...
    if (pcm_irq_invoked(chip)) {
        unsigned int last_ptr, size;
        /* 获取当前硬件指针（以帧为单位） */
        last_ptr = get_hw_ptr(chip);
        /* 计算自上次更新以来处理的帧数 */
        if (last_ptr < chip->last_ptr)
            size = runtime->buffer_size + last_ptr - chip->last_ptr;
        else
            size = last_ptr - chip->last_ptr;
        /* 记录最后更新的点 */
        chip->last_ptr = last_ptr;
        /* 累积大小 */
        chip->size += size;
        /* 超过周期边界？ */
        if (chip->size >= runtime->period_size) {
            /* 重置累积器 */
            chip->size %= runtime->period_size;
            /* 调用更新器 */
            spin_unlock(&chip->lock);
            snd_pcm_period_elapsed(substream);
            spin_lock(&chip->lock);
        }
        /* 必要时确认中断 */
    }
    ...
    spin_unlock(&chip->lock);
    return IRQ_HANDLED;
}
```

### 调用 `snd_pcm_period_elapsed()`

无论何种情况，即使超过了一个周期，也不必多次调用 `snd_pcm_period_elapsed()`。只需调用一次即可。PCM 层将检查当前硬件指针并更新至最新状态。
### 原子性

内核编程中最重要（同时也是最难调试）的问题之一是竞态条件。在 Linux 内核中，通常通过旋锁、互斥锁或信号量来避免这类问题。一般来说，如果一个中断处理器中可能发生竞态条件，则必须以原子方式管理，并且需要使用旋锁来保护关键部分。如果关键部分不在中断处理器代码中并且可以接受执行时间相对较长的情况，那么应该使用互斥锁或信号量代替。
如前所述，一些 PCM 回调是原子的，而另一些则不是。例如，`hw_params` 回调是非原子的，而 `trigger` 回调是原子的。这意味着后者已经在由 PCM 中间层持有的旋锁中被调用，即 PCM 流锁。在选择回调中的锁定方案时，请考虑这种原子性。
在原子回调中，你不能使用可能调用 `schedule()` 或进入 `sleep()` 的函数。信号量和互斥锁可能会导致睡眠，因此不能在原子回调（例如 `trigger` 回调）中使用。要在这样的回调中实现延迟，请使用 `udelay()` 或 `mdelay()`。
所有三个原子回调（`trigger`、`pointer` 和 `ack`）都在禁用本地中断的情况下被调用。
然而，可以要求所有的PCM操作是非原子的。
这假设所有调用点都在非原子上下文中。例如，函数
:c:func:`snd_pcm_period_elapsed()` 通常从中断处理程序中调用。但是，如果你设置驱动程序使用线程化的中断处理程序，则此调用也可以在非原子上下文中进行。在这种情况下，你可以在创建 `snd_pcm` 结构体对象后设置其 `nonatomic` 字段。当设置了这个标志时，PCM核心内部会使用互斥锁和读写信号量而不是自旋锁和读写锁，这样你就可以安全地在非原子上下文中调用所有PCM函数。
同样，在某些情况下，你可能需要在原子上下文中调用
:c:func:`snd_pcm_period_elapsed()`（例如，在 `ack` 或其他回调期间周期结束）。为此目的，有一个变体可以在PCM流锁内调用
:c:func:`snd_pcm_period_elapsed_under_stream_lock()`。
约束
---------
由于物理限制，硬件并非无限可配置。
这些限制通过设置约束来表达。
例如，为了将采样率限制为一些支持的值，可以使用 :c:func:`snd_pcm_hw_constraint_list()`。你需要在打开回调中调用此函数：

```c
      static unsigned int rates[] =
              {4000, 10000, 22050, 44100};
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

有许多不同的约束。查看 `sound/pcm.h` 以获取完整列表。你甚至可以定义自己的约束规则。例如，假设 `my_chip` 可以管理一个通道数为1的子流，条件是格式为 `S16_LE`，否则它支持 `struct snd_pcm_hardware` 中指定的任何格式（或任何其他约束列表）。你可以构建这样的规则：

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

然后你需要调用此函数添加你的规则：

```c
  snd_pcm_hw_rule_add(substream->runtime, 0, SNDRV_PCM_HW_PARAM_CHANNELS,
                      hw_rule_channels_by_format, NULL,
                      SNDRV_PCM_HW_PARAM_FORMAT, -1);
```

规则函数在应用程序设置PCM格式时被调用，并相应地细化通道数量。但应用程序可能会在设置格式之前设置通道数量。因此你也需要定义逆向规则：

```c
      static int hw_rule_format_by_channels(struct snd_pcm_hw_params *params,
                                            struct snd_pcm_hw_rule *rule)
      {
              struct snd_interval *c = hw_param_interval(params,
                    SNDRV_PCM_HW_PARAM_CHANNELS);
              struct snd_mask *f = hw_param_mask(params, SNDRV_PCM_HW_PARAM_FORMAT);
              struct snd_mask fmt;

              snd_mask_any(&fmt);    /* 初始化结构 */
              if (c->min < 2) {
                      fmt.bits[0] &= SNDRV_PCM_FMTBIT_S16_LE;
                      return snd_mask_refine(f, &fmt);
              }
              return 0;
      }
```

... 并在打开回调中：

```c
  snd_pcm_hw_rule_add(substream->runtime, 0, SNDRV_PCM_HW_PARAM_FORMAT,
                      hw_rule_format_by_channels, NULL,
                      SNDRV_PCM_HW_PARAM_CHANNELS, -1);
```

hw约束的一个典型用法是使缓冲区大小与周期大小对齐。默认情况下，ALSA PCM核心不强制缓冲区大小必须与周期大小对齐。例如，有可能出现256字节周期与999字节缓冲区的组合。
然而，许多设备芯片要求缓冲区必须是周期的倍数。在这种情况下，可以为 `SNDRV_PCM_HW_PARAM_PERIODS` 调用 :c:func:`snd_pcm_hw_constraint_integer()`：

```c
  snd_pcm_hw_constraint_integer(substream->runtime,
                                SNDRV_PCM_HW_PARAM_PERIODS);
```

这确保了周期数是整数，从而缓冲区大小与周期大小对齐。
hw约束是一个非常强大的机制，用于定义首选的PCM配置，并且有相关的辅助函数。
我在这里不会给出更多细节，相反，我想说的是，“Luke，利用源头。”

控制接口
=========

总览
----

控制接口被广泛用于许多开关、滑块等，这些都可从用户空间访问。它最重要的用途是混音器接口。换句话说，自从ALSA 0.9.x版本开始，所有的混音器功能都是基于控制内核API实现的。
ALSA有一个明确定义的AC97控制模块。如果你的芯片只支持AC97而没有其他功能，你可以跳过本节。
控制API在`<sound/control.h>`中定义。如果你想添加自己的控制，请包含这个文件。

控制定义
--------

为了创建一个新的控制，你需要定义以下三个回调函数：`info`、`get`和`put`。然后，定义一个`snd_kcontrol_new`结构体，例如：

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

`iface`字段指定了控制类型，即`SNDRV_CTL_ELEM_IFACE_XXX`，这通常是`MIXER`。对于全局控制（逻辑上不属于混音器的一部分），请使用`CARD`。如果控制与声卡上的某个特定设备紧密相关，则使用`HWDEP`、`PCM`、`RAWMIDI`、`TIMER`或`SEQUENCER`，并使用`device`和`subdevice`字段指定设备编号。

`name`是名称标识符字符串。自从ALSA 0.9.x版本开始，控制名称变得非常重要，因为其作用是通过名称来分类的。有一些预定义的标准控制名称。具体细节将在`控制名称`_小节中描述。

`index`字段保存了该控制的索引号。如果有多个具有相同名称但不同特性的控制，可以通过索引号加以区分。当卡上有多个编解码器时就会出现这种情况。如果索引为零，则可以省略上述定义。

`access`字段包含了该控制的访问类型。在这里给出`SNDRV_CTL_ELEM_ACCESS_XXX`的位掩码组合。具体细节将在`访问标志`_小节中解释。

`private_value`字段包含了一个任意的长整型值。当使用通用的`info`、`get`和`put`回调函数时，你可以通过这个字段传递一个值。如果需要几个较小的数字，你可以将它们按位组合在一起。或者，也可以在这个字段中存储一个指向某些记录的指针（转换为无符号长整型）。

`tlv`字段可用于提供关于控制的元数据；参见`元数据`_小节。

其余三个是`控制回调函数`_。
控制名称
--------

定义控制名称时有一些标准。通常，一个控制是由三部分组成的：“源 方向 功能”。
首先，“SOURCE”指定了控制的来源，它是一个字符串，例如“主控（Master）”、“PCM”、“CD”和“线路（Line）”。有许多预定义的来源。

其次，“DIRECTION”根据控制的方向来指定，可以是以下字符串之一：“播放（Playback）”、“捕捉（Capture）”、“旁路播放（Bypass Playback）”和“旁路捕捉（Bypass Capture）”。或者，它可以被省略，意味着同时支持播放和捕捉方向。

最后，“FUNCTION”根据控制的功能来指定，可以是以下字符串之一：“开关（Switch）”、“音量（Volume）”和“路由（Route）”。

因此，控制名称的例子包括“主控捕捉开关（Master Capture Switch）”或“PCM播放音量（PCM Playback Volume）”。

有一些例外情况：

### 全局捕捉和播放

对于全局捕捉（输入）源、开关和音量，使用“捕捉源（Capture Source）”、“捕捉开关（Capture Switch）”和“捕捉音量（Capture Volume）”。同样地，对于全局输出增益开关和音量，则使用“播放开关（Playback Switch）”和“播放音量（Playback Volume）”。

### 音调控制

音调控制开关和音量通过“音调控制 - XXX”的形式来指定，例如“音调控制 - 开关（Tone Control - Switch）”、“音调控制 - 低音（Tone Control - Bass）”、“音调控制 - 中心（Tone Control - Center）”。

### 3D 控制

3D 控制开关和音量通过“3D 控制 - XXX”的形式来指定，例如“3D 控制 - 开关（3D Control - Switch）”、“3D 控制 - 中心（3D Control - Center）”、“3D 控制 - 空间（3D Control - Space）”。

### 麦克风增强

麦克风增强开关设置为“麦克风增强（Mic Boost）”或“麦克风增强（6dB）（Mic Boost (6dB)）”。

更详细的信息可以在`Documentation/sound/designs/control-names.rst`中找到。

### 访问标志

访问标志是一个位掩码，用于指定给定控制的访问类型。默认访问类型是`SNDRV_CTL_ELEM_ACCESS_READWRITE`，这意味着允许对这个控制进行读写操作。当访问标志被省略（即等于0）时，默认视为`READWRITE`访问。
当控件为只读时，应传递 ``SNDRV_CTL_ELEM_ACCESS_READ``。在这种情况下，您无需定义 ``put`` 回调函数。
类似地，如果控件为只写（虽然这种情况很少见），您可以使用 ``WRITE`` 标志，并且不需要定义 ``get`` 回调函数。
如果控件的值频繁变化（例如 VU 计量表），则应设置 ``VOLATILE`` 标志。这意味着控件可能在没有 `更改通知` 的情况下发生变化。应用程序应当持续轮询此类控件。
如果控件可能会被更新，但目前对任何内容都没有影响，则设置 ``INACTIVE`` 标志可能是合适的。例如，在没有打开 PCM 设备的情况下，PCM 控件应当处于非活动状态。
还有 ``LOCK`` 和 ``OWNER`` 标志用于更改写权限。

### 控件回调

#### info 回调

``info`` 回调用于获取此控件的详细信息。它必须存储给定的 struct `snd_ctl_elem_info` 对象的值。例如，对于具有单个元素的布尔控件：

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

`type` 字段指定了控件的类型。可以是 `BOOLEAN`, `INTEGER`, `ENUMERATED`, `BYTES`, `IEC958` 或 `INTEGER64`。`count` 字段指定了此控件中的元素数量。例如，立体声音量的 `count` 值为 2。`value` 字段是一个联合体，其存储的值取决于类型。布尔类型和整数类型的处理方式相同。

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

上述回调可以通过辅助函数 :c:func:`snd_ctl_enum_info()` 简化。最终代码如下所示（您可以将 `ARRAY_SIZE(texts)` 作为第三个参数传入；这取决于个人喜好）：

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

为了方便起见，提供了一些常见的 info 回调：:c:func:`snd_ctl_boolean_mono_info()` 和 :c:func:`snd_ctl_boolean_stereo_info()`。显然，前者是用于单声道布尔项的 info 回调，类似于上面的 :c:func:`snd_myctl_mono_info()`，而后者是用于双声道布尔项的。

#### get 回调

此回调用于读取控件的当前值，以便将其返回给用户空间。例如：

```c
static int snd_myctl_get(struct snd_kcontrol *kcontrol,
                         struct snd_ctl_elem_value *ucontrol)
{
        struct mychip *chip = snd_kcontrol_chip(kcontrol);
        ucontrol->value.integer.value[0] = get_some_value(chip);
        return 0;
}
```

`value` 字段也取决于控件的类型以及 info 回调。例如，sb 驱动程序使用该字段来存储寄存器偏移量、位移和位掩码。`private_value` 字段如下设置：

```c
.private_value = reg | (shift << 16) | (mask << 24)
```

并在回调中检索，如：

```c
static int snd_sbmixer_get_single(struct snd_kcontrol *kcontrol,
                                  struct snd_ctl_elem_value *ucontrol)
{
        int reg = kcontrol->private_value & 0xff;
        int shift = (kcontrol->private_value >> 16) & 0xff;
        int mask = (kcontrol->private_value >> 24) & 0xff;
        ...
```
在`get`回调函数中，如果控件包含多个元素（即`count > 1`），则必须填充所有这些元素。在上面的例子中，我们只填充了一个元素（`value.integer.value[0]`），因为我们假设`count = 1`。
put回调函数
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

如上所述，如果值发生改变，则必须返回1；如果值没有变化，则返回0。如果发生任何致命错误，则像平常一样返回一个负的错误代码。
如同在`get`回调函数中，当控件包含多个元素时，在这个回调函数中也必须评估所有元素。
回调函数不是原子操作
~~~~~~~~~~~~~~~~~~~~~~~~

这三个回调函数都不是原子操作。
控件构造器
-------------------

当一切都准备就绪后，最后我们可以创建一个新的控件。为了创建控件，需要调用两个函数：`:c:func:`snd_ctl_new1()` 和 `:c:func:`snd_ctl_add()`。
最简单的方式可以这样做：

```c
err = snd_ctl_add(card, snd_ctl_new1(&my_control, chip));
if (err < 0)
    return err;
```

其中 `my_control` 是上面定义的 `struct snd_kcontrol_new` 对象，而 `chip` 是要传递给 `kcontrol->private_data` 的对象指针，可以在回调函数中引用它。
`:c:func:`snd_ctl_new1()` 分配一个新的 `struct snd_kcontrol` 实例，而 `:c:func:`snd_ctl_add()` 将给定的控件组件添加到声卡上。
更改通知
-------------------

如果你需要在中断例程中更改并更新一个控件，你可以调用 `:c:func:`snd_ctl_notify()`。例如：

```c
snd_ctl_notify(card, SNDRV_CTL_EVENT_MASK_VALUE, id_pointer);
```

该函数接受声卡指针、事件掩码以及要通知的控件ID指针作为参数。事件掩码指定了通知的类型，例如在上面的例子中，通知的是控件值的改变。ID指针是指向 `struct snd_ctl_elem_id` 的指针。你可以在 `es1938.c` 或 `es1968.c` 中找到关于硬件音量中断的一些示例。
元数据
--------

为了提供关于混音器控制dB值的信息，可以使用 `<sound/tlv.h>` 中的一个 `DECLARE_TLV_xxx` 宏来定义一个包含这些信息的变量，设置 `tlv.p` 字段指向这个变量，并在 `access` 字段中包括 `SNDRV_CTL_ELEM_ACCESS_TLV_READ` 标志；如下所示：

```c
static DECLARE_TLV_DB_SCALE(db_scale_my_control, -4050, 150, 0);

static struct snd_kcontrol_new my_control = {
        ..
```
这段文档主要描述了ALSA（Advanced Linux Sound Architecture）中AC97 Codec层的使用方法，包括定义混音器控制信息的宏以及AC97 Codec实例创建的过程。下面是该段落的中文翻译：

```
.access = SNDRV_CTL_ELEM_ACCESS_READWRITE |
          SNDRV_CTL_ELEM_ACCESS_TLV_READ,
...
.tlv.p = db_scale_my_control,
};
```

`:c:func:` `DECLARE_TLV_DB_SCALE()` 宏定义了一个混音器控制的相关信息，其中每个步骤的变化会以一个固定的分贝值来改变混音器控制的值。第一个参数是需要定义的变量名。第二个参数是最小值，单位为0.01分贝。第三个参数是步长大小，单位也是0.01分贝。如果最小值实际上会使控制静音，则将第四个参数设置为1。

`:c:func:` `DECLARE_TLV_DB_LINEAR()` 宏定义了一个混音器控制的信息，其中混音器控制的值以线性方式影响输出。第一个参数是需要定义的变量名。第二个参数是最小值，单位为0.01分贝。第三个参数是最大值，单位同样为0.01分贝。如果最小值使控制静音，则将第二个参数设置为`TLV_DB_GAIN_MUTE`。

### AC97 Codec API

#### 概述

ALSA中的AC97 Codec层是非常规范化的，因此你不需要编写大量代码来控制它。只需要提供低级别的控制例程即可。AC97 Codec API在 `<sound/ac97_codec.h>` 中定义。

#### 完整代码示例

```c
struct mychip {
        ...
struct snd_ac97 *ac97;
        ...
};

static unsigned short snd_mychip_ac97_read(struct snd_ac97 *ac97,
                                            unsigned short reg)
{
        struct mychip *chip = ac97->private_data;
        ...
/* 在这里从Codec读取寄存器值 */
        return the_register_value;
}

static void snd_mychip_ac97_write(struct snd_ac97 *ac97,
                                  unsigned short reg, unsigned short val)
{
        struct mychip *chip = ac97->private_data;
        ...
/* 将给定的寄存器值写入Codec */
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

#### 创建AC97实例

为了创建一个AC97实例，首先调用 `snd_ac97_bus()` 函数，并传入包含回调函数的 `ac97_bus_ops_t` 结构体：

```c
struct snd_ac97_bus *bus;
static struct snd_ac97_bus_ops ops = {
        .write = snd_mychip_ac97_write,
        .read = snd_mychip_ac97_read,
};

snd_ac97_bus(card, 0, &ops, NULL, &pbus);
```

这个总线记录会在所有关联的AC97实例间共享。
```
然后使用一个 `struct snd_ac97_template` 记录及上述创建的总线指针来调用函数 `snd_ac97_mixer()` ：

```c
struct snd_ac97_template ac97;
int err;

memset(&ac97, 0, sizeof(ac97));
ac97.private_data = chip;
snd_ac97_mixer(bus, &ac97, &chip->ac97);
```

这里的 `chip->ac97` 是指向新创建的一个 `ac97_t` 实例的指针。在这种情况下，芯片指针被设置为私有数据，以便读/写回调函数可以引用这个芯片实例。这个实例不一定存储在芯片记录中。如果你需要从驱动程序中更改寄存器值，或者需要 AC97 编码解码器的挂起/恢复功能，请保留此指针并传递给相应的函数。

### AC97 回调函数

标准回调函数包括 `read` 和 `write`。显然，它们对应于对硬件低级代码进行读和写的函数。
`read` 回调返回参数中指定的寄存器值：

```c
static unsigned short snd_mychip_ac97_read(struct snd_ac97 *ac97,
                                            unsigned short reg)
{
    struct mychip *chip = ac97->private_data;
    ...
    return the_register_value;
}
```

这里，芯片可以从 `ac97->private_data` 铸造得到。
同时，`write` 回调用于设置寄存器值：

```c
static void snd_mychip_ac97_write(struct snd_ac97 *ac97,
                                   unsigned short reg, unsigned short val)
{
    // 设置寄存器值的代码
}
```

这些回调函数与控制API回调一样是非原子性的。
还有其他一些回调函数：`reset`、`wait` 和 `init`。
`reset` 回调用于重置编码解码器。如果芯片需要特定类型的重置，则可以定义此回调。
`wait` 回调用于在标准初始化过程中增加等待时间。如果芯片需要额外的等待时间，则定义此回调。
`init` 回调用于进行额外的编码解码器初始化。

### 在驱动程序中更新寄存器

如果你需要从驱动程序访问编码解码器，你可以调用以下函数：`snd_ac97_write()`、`snd_ac97_read()`、`snd_ac97_update()` 和 `snd_ac97_update_bits()`。
`:c:func:`snd_ac97_write()` 和 `:c:func:`snd_ac97_update()` 这两个函数都用于将一个值设置给指定的寄存器（`AC97_XXX`）。它们之间的区别在于 `:c:func:`snd_ac97_update()` 在给定的值已经设置的情况下不会重写该值，而 `:c:func:`snd_ac97_write()` 总是会重写值。例如：

  * `snd_ac97_write(ac97, AC97_MASTER, 0x8080);`
  * `snd_ac97_update(ac97, AC97_MASTER, 0x8080);`

`:c:func:`snd_ac97_read()` 用于读取指定寄存器的值。例如：

  * `value = snd_ac97_read(ac97, AC97_MASTER);`

`:c:func:`snd_ac97_update_bits()` 用于更新指定寄存器中的一些位：

  * `snd_ac97_update_bits(ac97, reg, mask, value);`

另外，如果编解码器支持VRA或DRA，则存在一个函数来更改给定寄存器（如 `AC97_PCM_FRONT_DAC_RATE`）的采样率：`:c:func:`snd_ac97_set_rate()`：

  * `snd_ac97_set_rate(ac97, AC97_PCM_FRONT_DAC_RATE, 44100);`

可以设置以下寄存器来更改采样率：`AC97_PCM_MIC_ADC_RATE`、`AC97_PCM_FRONT_DAC_RATE`、`AC97_PCM_LR_ADC_RATE`、`AC97_SPDIF`。当指定 `AC97_SPDIF` 时，并没有真正改变寄存器，而是更新了相应的IEC958状态位。

### 时钟调整

在某些芯片中，编解码器的时钟不是48000，而是使用PCI时钟（以节省晶体振荡器！）。在这种情况下，需要将字段 `bus->clock` 设置为相应的值。例如，intel8x0和es1968驱动程序有其自己的函数来从时钟读取数据。

### 临时文件

ALSA AC97接口将创建一个临时文件，例如 `/proc/asound/card0/codec97#0/ac97#0-0` 和 `ac97#0-0+regs`。您可以参考这些文件查看当前的状态和寄存器的值。

### 多个编解码器

当同一张卡上有多个编解码器时，您需要多次调用 `:c:func:`snd_ac97_mixer()` 并且 `ac97.num=1` 或更大。字段 `num` 指定了编解码器的编号。
如果您设置了多个编解码器，则要么为每个编解码器编写不同的回调函数，要么在回调例程中检查 `ac97->num`。

### MIDI（MPU401-UART）接口

#### 一般

许多声卡内置了MIDI（MPU401-UART）接口。当声卡支持标准的MPU401-UART接口时，您很可能可以使用ALSA的MPU401-UART API。MPU401-UART API定义在 `<sound/mpu401.h>` 中。
一些声卡芯片有一个类似但略有不同的MPU401实现。例如，emu10k1有自己的MPU401例程。

#### MIDI构造器

要创建一个rawmidi对象，请调用 `:c:func:`snd_mpu401_uart_new()`：

  * `struct snd_rawmidi *rmidi;`
  * `snd_mpu401_uart_new(card, 0, MPU401_HW_MPU401, port, info_flags, irq, &rmidi);`

第一个参数是指向声卡的指针，第二个参数是这个组件的索引。您可以创建最多8个rawmidi设备。
第三个参数是硬件的类型 `MPU401_HW_XXX`。如果不是特殊的类型，您可以使用 `MPU401_HW_MPU401`。
第四个参数是I/O端口地址。许多向后兼容的MPU401都有一个I/O端口，如0x330。或者，它可能是其自身PCI I/O区域的一部分。这取决于芯片的设计。
第五个参数是一个位标志，用于提供额外的信息。当上面的I/O端口地址属于PCI I/O区域的一部分时，MPU401 I/O端口可能已经被驱动程序本身分配（预留）。在这种情况下，请传递一个位标志`MPU401_INFO_INTEGRATED`，这样mpu401-uart层将自行分配I/O端口。
当控制器只支持输入或输出MIDI流时，分别传递`MPU401_INFO_INPUT`或`MPU401_INFO_OUTPUT`位标志。然后rawmidi实例将被创建为单一流。
`MPU401_INFO_MMIO`位标志用于将访问方法改为MMIO（通过readb和writeb）而不是iob和outb。在这种情况下，您必须将iomapped地址传递给:c:func:`snd_mpu401_uart_new()`。
当设置了`MPU401_INFO_TX_IRQ`时，默认中断处理程序中不会检查输出流。驱动程序需要自行调用:c:func:`snd_mpu401_uart_interrupt_tx()`以在中断处理程序中开始处理输出流。
如果MPU-401接口与其卡上的其他逻辑设备共享中断，则设置`MPU401_INFO_IRQ_HOOK`（参见[下面](MIDI Interrupt Handler_))。
通常，端口地址对应于命令端口，而端口+1则对应于数据端口。如果不是这样，您可以稍后手动更改struct snd_mpu401中的`cport`字段。
然而，struct snd_mpu401指针并不会由:c:func:`snd_mpu401_uart_new()`显式返回。您需要明确地将`rmidi->private_data`转换为struct snd_mpu401，并重置`cport`字段，如下所示：

```c
struct snd_mpu401 *mpu;
mpu = rmidi->private_data;
mpu->cport = my_own_control_port;
```

第六个参数指定了要分配的ISA中断编号。如果您不希望分配中断（因为您的代码已经分配了一个共享中断，或者因为设备不使用中断），请传递-1。对于没有中断的MPU-401设备，将使用轮询定时器代替。

### MIDI中断处理程序

当在:c:func:`snd_mpu401_uart_new()`中分配了中断时，会自动使用专用的ISA中断处理程序，因此除了创建mpu401组件之外，您无需做任何其他事情。否则，您需要设置`MPU401_INFO_IRQ_HOOK`，并在确定发生了UART中断时从自己的中断处理程序中显式调用:c:func:`snd_mpu401_uart_interrupt()`。
在这种情况下，您需要将从:c:func:`snd_mpu401_uart_new()`返回的rawmidi对象的`private_data`作为:c:func:`snd_mpu401_uart_interrupt()`的第二个参数传递：

```c
snd_mpu401_uart_interrupt(irq, rmidi->private_data, regs);
```

### RawMIDI接口

#### 概览

Raw MIDI接口用于可以通过字节流访问的硬件MIDI端口。它不用于那些不直接理解MIDI的合成芯片。
ALSA负责文件和缓冲区管理。您只需编写一些代码来在缓冲区与硬件之间移动数据即可。
`rawmidi` API 在 `<sound/rawmidi.h>` 中定义。

### RawMIDI 构造器

要创建一个 `rawmidi` 设备，需要调用函数 `snd_rawmidi_new()`：

```c
struct snd_rawmidi *rmidi;
int err = snd_rawmidi_new(chip->card, "MyMIDI", 0, outs, ins, &rmidi);
if (err < 0)
        return err;
rmidi->private_data = chip;
strcpy(rmidi->name, "My MIDI");
rmidi->info_flags = SNDRV_RAWMIDI_INFO_OUTPUT |
                    SNDRV_RAWMIDI_INFO_INPUT |
                    SNDRV_RAWMIDI_INFO_DUPLEX;
```

第一个参数是声卡指针，第二个参数是设备的ID字符串。
第三个参数是该组件的索引。你可以创建最多8个 `rawmidi` 设备。
第四和第五个参数分别是该设备输出和输入子流的数量（一个子流相当于一个MIDI端口）。
设置 `info_flags` 字段来指定设备的能力。如果至少有一个输出端口，则设置 `SNDRV_RAWMIDI_INFO_OUTPUT`；如果至少有一个输入端口，则设置 `SNDRV_RAWMIDI_INFO_INPUT`；如果设备可以同时处理输出和输入，则设置 `SNDRV_RAWMIDI_INFO_DUPLEX`。
创建 `rawmidi` 设备后，你需要为每个子流设置操作符（回调）。有辅助函数可以为设备的所有子流设置操作符：

```c
snd_rawmidi_set_ops(rmidi, SNDRV_RAWMIDI_STREAM_OUTPUT, &snd_mymidi_output_ops);
snd_rawmidi_set_ops(rmidi, SNDRV_RAWMIDI_STREAM_INPUT, &snd_mymidi_input_ops);
```

这些操作符通常这样定义：

```c
static struct snd_rawmidi_ops snd_mymidi_output_ops = {
        .open =    snd_mymidi_output_open,
        .close =   snd_mymidi_output_close,
        .trigger = snd_mymidi_output_trigger,
};
```

这些回调在“RawMIDI 回调”部分中解释。
如果有多个子流，你应该给它们每一个都指定一个独特的名称：

```c
struct snd_rawmidi_substream *substream;
list_for_each_entry(substream,
                    &rmidi->streams[SNDRV_RAWMIDI_STREAM_OUTPUT].substreams,
                    list) {
        sprintf(substream->name, "My MIDI Port %d", substream->number + 1);
}
/* 对于 SNDRV_RAWMIDI_STREAM_INPUT 同样适用 */
```

### RawMIDI 回调

在所有的回调中，你为 `rawmidi` 设备设置的私有数据可以通过 `substream->rmidi->private_data` 访问。
如果有多个端口，你的回调可以从传递给每个回调的 `struct snd_rawmidi_substream` 数据确定端口索引：

```c
struct snd_rawmidi_substream *substream;
int index = substream->number;
```

#### RawMIDI 打开回调

```c
static int snd_xxx_open(struct snd_rawmidi_substream *substream);
```

当一个子流被打开时会调用这个回调。你可以在其中初始化硬件，但不应该立即开始发送/接收数据。

#### RawMIDI 关闭回调

```c
static int snd_xxx_close(struct snd_rawmidi_substream *substream);
```

不言而喻，
`rawmidi` 设备的 `open` 和 `close` 回调是通过互斥锁序列化的，并且可以休眠。
针对输出子流的 RawMIDI 触发回调
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

      static void snd_xxx_output_trigger(struct snd_rawmidi_substream *substream, int up);

当子流缓冲区中有待传输的数据时，会使用非零的 `up` 参数调用此函数。
要从缓冲区读取数据，请调用 :c:func:`snd_rawmidi_transmit_peek()`。它将返回已读取的字节数；当缓冲区中没有更多数据时，这个数字会小于请求的字节数。成功传输数据后，请调用 :c:func:`snd_rawmidi_transmit_ack()` 以从子流缓冲区移除这些数据。

```c
unsigned char data;
while (snd_rawmidi_transmit_peek(substream, &data, 1) == 1) {
        if (snd_mychip_try_to_transmit(data))
                snd_rawmidi_transmit_ack(substream, 1);
        else
                break; /* 硬件FIFO已满 */
}
```

如果您事先知道硬件可以接受数据，您可以使用 :c:func:`snd_rawmidi_transmit()` 函数，它一次性读取并移除缓冲区中的某些数据。

```c
while (snd_mychip_transmit_possible()) {
        unsigned char data;
        if (snd_rawmidi_transmit(substream, &data, 1) != 1)
                break; /* 没有更多数据 */
        snd_mychip_transmit(data);
}
```

如果您事先知道可以接受多少字节，可以在 `snd_rawmidi_transmit*()` 函数中使用大于一的缓冲区大小。`trigger` 回调不能休眠。如果硬件 FIFO 已满而子流缓冲区还未清空，则您必须稍后继续传输数据，这可以在中断处理程序中完成，或者如果没有MIDI传输中断的话，可以通过定时器来实现。当需要中止数据传输时，会使用零值的 `up` 参数调用 `trigger` 回调。

针对输入子流的 RawMIDI 触发回调
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

      static void snd_xxx_input_trigger(struct snd_rawmidi_substream *substream, int up);

使用非零的 `up` 参数调用来启用接收数据，或使用零值的 `up` 参数调用来禁用接收数据。
`trigger` 回调不能休眠；实际的数据读取通常在中断处理程序中完成。
当启用数据接收时，您的中断处理程序应该为所有接收到的数据调用 :c:func:`snd_rawmidi_receive()`。

```c
void snd_mychip_midi_interrupt(...)
{
        while (mychip_midi_available()) {
                unsigned char data;
                data = mychip_midi_read();
                snd_rawmidi_receive(substream, &data, 1);
        }
}
```

排空回调
~~~~~~~~~~~~~~

::

      static void snd_xxx_drain(struct snd_rawmidi_substream *substream);

此函数仅用于输出子流。该函数应等待直到从子流缓冲区读取的所有数据都已传输完毕。
这样可以确保设备关闭和驱动卸载时不会丢失数据。
此回调是可选的。如果您不在 `struct snd_rawmidi_ops` 结构体中设置 `drain`，ALSA 将简单地等待 50 毫秒。

其他设备
=====================

FM OPL3
-------

FM OPL3 仍然被许多芯片使用（主要是为了向后兼容）。ALSA 也提供了一个优秀的 OPL3 FM 控制层。OPL3 API 在 `<sound/opl3.h>` 中定义。
FM寄存器可以通过在`<sound/asound_fm.h>`中定义的直接FM API直接访问。在ALSA原生模式下，FM寄存器通过硬件依赖设备的直接FM扩展API访问；而在OSS兼容模式下，FM寄存器可以通过`/dev/dmfmX`设备中的OSS直接FM兼容API进行访问。

为了创建OPL3组件，你需要调用两个函数。第一个是构造一个`opl3_t`实例：

```c
struct snd_opl3 *opl3;
snd_opl3_create(card, lport, rport, OPL3_HW_OPL3_XXX,
                integrated, &opl3);
```

第一个参数是卡指针，第二个参数是左端口地址，第三个参数是右端口地址。在大多数情况下，右端口位于左端口+2的位置。
第四个参数是硬件类型。
如果左端口和右端口已经被卡驱动程序分配，将非零值传递给第五个参数(``integrated``)。否则，opl3模块将自行分配指定的端口。
如果访问硬件需要特殊方法而不是标准I/O访问，你可以单独使用`:c:func:`snd_opl3_new()`创建opl3实例：

```c
struct snd_opl3 *opl3;
snd_opl3_new(card, OPL3_HW_OPL3_XXX, &opl3);
```

然后为私有访问函数、私有数据以及析构函数设置`command`、`private_data`和`private_free`。`l_port`和`r_port`不一定需要设置。只有`command`必须正确设置。可以从`opl3->private_data`字段获取数据。

通过`:c:func:`snd_opl3_new()`创建opl3实例后，调用`:c:func:`snd_opl3_init()`以将芯片初始化到适当的状态。注意`:c:func:`snd_opl3_create()`总是内部调用它。
如果成功创建了opl3实例，则为该opl3创建一个hwdep设备：

```c
struct snd_hwdep *opl3hwdep;
snd_opl3_hwdep_new(opl3, 0, 1, &opl3hwdep);
```

第一个参数是你创建的`opl3_t`实例，第二个参数是索引号，通常为0。
第三个参数是为OPL3端口分配的序列器客户端的索引偏移。如果有MPU401-UART，这里应设置为1（UART始终占用0）。

### 硬件依赖设备

一些芯片需要用户空间访问以实现特殊控制或加载微代码。在这种情况下，可以创建一个hwdep（硬件依赖）设备。hwdep API在`<sound/hwdep.h>`中定义。你可以在opl3驱动程序或`isa/sb/sb16_csp.c`中找到示例。
创建`hwdep`实例是通过`:c:func:`snd_hwdep_new()`完成的：

```c
struct snd_hwdep *hw;
snd_hwdep_new(card, "My HWDEP", 0, &hw);
```

其中第三个参数是索引号。
然后可以将任何指针值传递给`private_data`。如果你指定了私有数据，也应该定义一个析构函数。析构函数设置在`private_free`字段中：

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

可以为这个实例定义任意文件操作。文件操作符定义在`ops`表中。例如，假设此芯片需要一个ioctl：

```c
hw->ops.open = mydata_open;
hw->ops.ioctl = mydata_ioctl;
hw->ops.release = mydata_release;
```

并根据需要实现回调函数。
IEC958 (S/PDIF)
---------------

通常，IEC958设备的控制是通过控制接口实现的。有一个宏用于组合IEC958控制的名字字符串，即：:c:func:`SNDRV_CTL_NAME_IEC958()`，在`<include/asound.h>`中定义。
对于IEC958状态位有一些标准控制。这些控制使用类型`SNDRV_CTL_ELEM_TYPE_IEC958`，元素大小固定为4字节数组（value.iec958.status[x]）。对于`info`回调函数，您不需要为此类型指定值字段（但是必须设置count字段）。
“IEC958播放消费者模式掩码”用于返回消费者模式下IEC958状态位的位掩码。类似地，“IEC958播放专业模式掩码”返回专业模式下的位掩码。它们都是只读控制。
同时，“IEC958播放默认值”控制被定义用于获取和设置当前默认的IEC958位。
由于历史原因，播放掩码和播放默认值控制的两种变体都可以在`SNDRV_CTL_ELEM_IFACE_PCM`或`SNDRV_CTL_ELEM_IFACE_MIXER`接口上实现。
不过驱动程序应该在同一接口上暴露掩码和默认值。
此外，您可以定义控制开关以启用/禁用或设置原始位模式。实现取决于芯片，但控制应该命名为“IEC958 xxx”，最好使用:c:func:`SNDRV_CTL_NAME_IEC958()`宏。
可以找到几个例子，例如`pci/emu10k1`、`pci/ice1712`或`pci/cmipci.c`。

缓冲区与内存管理
==================

缓冲区类型
------------

ALSA根据总线和架构提供了几种不同的缓冲区分配函数。所有这些函数都有一个一致的API。物理连续页的分配通过:c:func:`snd_malloc_xxx_pages()`函数完成，其中xxx代表总线类型。
带有回退机制的页分配通过:c:func:`snd_dma_alloc_pages_fallback()`函数完成。此函数尝试分配指定数量的页，但如果可用的页不足，则会尝试减小请求大小直到找到足够的空间，直至最小为一页。
要释放页面，调用函数 :c:func:`snd_dma_free_pages()`。
通常，ALSA 驱动程序会在模块加载时尝试分配并预留一个大的连续物理空间以供后续使用。这被称为“预分配”。如前所述，你可以在 PCM 实例构造时（在 PCI 总线的情况下）调用以下函数：

```python
snd_pcm_lib_preallocate_pages_for_all(pcm, SNDRV_DMA_TYPE_DEV,
                                      &pci->dev, size, max);
```

其中 `size` 是要预分配的字节大小，而 `max` 是通过 `prealloc` proc 文件设置的最大大小。分配器将尝试在给定的大小范围内获取尽可能大的区域。

第二个参数（类型）和第三个参数（设备指针）取决于总线。对于普通设备，将设备指针（通常与 `card->dev` 相同）作为第三个参数传递，并且类型为 `SNDRV_DMA_TYPE_DEV`。

与总线无关的连续缓冲区可以使用 `SNDRV_DMA_TYPE_CONTINUOUS` 类型进行预分配。在这种情况下，你可以向设备指针传递 NULL，这是默认模式，意味着使用 `GFP_KERNEL` 标志进行分配。

如果你需要一个受限（较低）地址，则为设备设置一致的 DMA 遮罩位，并像普通设备内存分配一样传递设备指针。对于此类情况，如果不需要地址限制，仍然允许向设备指针传递 NULL。

对于分散/聚集缓冲区，请使用 `SNDRV_DMA_TYPE_DEV_SG` 与设备指针（参见 `Non-Contiguous Buffers`_ 部分）。

一旦缓冲区被预分配，你就可以在 `hw_params` 回调中使用分配器：

```python
snd_pcm_lib_malloc_pages(substream, size);
```

请注意，你必须先进行预分配才能使用此函数。

但是大多数驱动程序使用“受管理的缓冲区分配模式”，而不是手动分配和释放。这可以通过调用 :c:func:`snd_pcm_set_managed_buffer_all()` 而不是 :c:func:`snd_pcm_lib_preallocate_pages_for_all()` 来实现：

```python
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV,
                               &pci->dev, size, max);
```

这里传递的参数对两个函数是相同的。
在受管理模式下的不同之处在于，PCM 核心会在调用 PCM `hw_params` 回调之前内部调用 `snd_pcm_lib_malloc_pages()`，并在 PCM `hw_free` 回调之后自动调用 `snd_pcm_lib_free_pages()`。因此，驱动程序不再需要在其回调中显式调用这些函数。这使得许多驱动程序可以将 `hw_params` 和 `hw_free` 入口设置为 NULL。
外部硬件缓冲区
-------------------------
一些芯片有自己的硬件缓冲区，并且无法从主机内存进行 DMA 传输。在这种情况下，您需要选择以下两种方式之一：1）直接将音频数据复制/设置到外部硬件缓冲区；或 2）创建一个中间缓冲区，并在中断（或最好是在任务中）将数据从该中间缓冲区复制/设置到外部硬件缓冲区。如果外部硬件缓冲区足够大，则第一种情况可以很好地工作。这种方法不需要任何额外的缓冲区，因此更高效。您需要定义用于数据传输的 `copy` 回调，以及用于播放的 `fill_silence` 回调。但是，存在一个缺点：它不能被 mmapped。GUS 的 GF1 PCM 或 emu8000 的 wavetable PCM 就是此类方法的例子。
第二种情况允许对缓冲区进行 mmapped，尽管您必须处理中断或任务以将数据从中间缓冲区传输到硬件缓冲区。您可以在 vxpocket 驱动程序中找到此类示例。
另一种情况是，芯片使用 PCI 内存映射区域作为缓冲区，而不是主机内存。在这种情况下，只有在像 Intel 这样的架构上才能使用 mmapped。在非 mmapped 模式下，数据无法按照正常方式进行传输。因此，您还需要定义 `copy` 和 `fill_silence` 回调，就像上面的情况一样。您可以在 `rme32.c` 和 `rme96.c` 中找到此类示例。
`copy` 和 `silence` 回调的实现取决于硬件是否支持交错或非交错样本。`copy` 回调如下定义，根据方向是播放还是捕获略有不同：

  * 对于播放：
    
    static int playback_copy(struct snd_pcm_substream *substream, int channel, unsigned long pos, struct iov_iter *src, unsigned long count);
  * 对于捕获：
    
    static int capture_copy(struct snd_pcm_substream *substream, int channel, unsigned long pos, struct iov_iter *dst, unsigned long count);

在交错样本的情况下，第二个参数 (`channel`) 不被使用。第三个参数 (`pos`) 指定字节位置。
第四个参数对于播放和捕获的意义不同。对于播放，它包含源数据指针；对于捕获，它是目标数据指针。
最后一个参数是要复制的字节数量。
在这个回调中需要做的事情也因播放和捕获方向而异。在播放的情况下，您将指定数量的数据 (`count`) 从指定的指针 (`src`) 复制到硬件缓冲区中的指定偏移量 (`pos`)。如果编码类似于 memcpy 的方式，复制可能如下所示：

  * 对于播放：
    
    my_memcpy_from_iter(my_buffer + pos, src, count);
  * 对于捕获：
    
    my_memcpy_to_iter(dst, my_buffer + pos, count);

给定的 `src` 或 `dst` 是包含指针和大小的 `struct iov_iter` 指针。使用现有帮助程序根据 `linux/uio.h` 中的定义来复制或访问数据。
细心的读者可能会注意到这些回调接收的是以字节为单位的参数，而不是像其他回调那样以帧为单位。这是因为这样可以使编码更容易，如上面的例子所示，并且也使得交错和非交错情况更容易统一。
对于非交错样本的情况，实现会稍微复杂一些。回调函数针对每个通道被调用，并将通道作为第二个参数传递，因此每次传输总共会被调用N次。其他参数的意义与交错情况下的几乎相同。回调函数应该从/到给定的用户空间缓冲区复制数据，但仅限于给定的通道。具体细节，请参考 `isa/gus/gus_pcm.c` 或 `pci/rme9652/rme9652.c` 中的例子。

通常，在播放时，还会定义另一个回调函数 `fill_silence`。它的实现方式与上面提到的复制回调函数类似：

```c
static int silence(struct snd_pcm_substream *substream, int channel,
                   unsigned long pos, unsigned long count);
```

参数的意义与 `copy` 回调函数中的相同，不过这里没有缓冲区指针参数。在交错样本的情况下，通道参数没有意义，就像 `copy` 回调函数中一样。

`fill_silence` 回调函数的作用是在硬件缓冲区的指定偏移位置 (`pos`) 设置指定数量 (`count`) 的静音数据。假设数据格式是带符号的（即静音数据为0），使用类似于 memset 的函数来实现可能会像这样：

```c
my_memset(my_buffer + pos, 0, count);
```

对于非交错样本的情况，实现再次变得稍微复杂些，因为每次传输针对每个通道都会被调用N次。例如，可以参考 `isa/gus/gus_pcm.c`。
### 非连续缓冲区

如果你的硬件支持如 emu10k1 中的页表或者如 via82xx 中的缓冲描述符，你可以使用分散/集中（scatter-gather, SG）DMA。ALSA 提供了一个用于处理 SG 缓冲区的接口。该API在 `<sound/pcm.h>` 中提供。

为了创建 SG 缓冲区处理器，可以在PCM构造器中像处理其他PCI预分配那样使用 `snd_pcm_set_managed_buffer()` 或者 `snd_pcm_set_managed_buffer_all()` 函数，并且使用 `SNDRV_DMA_TYPE_DEV_SG` 类型。你需要传递 `&pci->dev`，其中 `pci` 是指向芯片的 `struct pci_dev` 指针：

```c
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_DEV_SG,
                               &pci->dev, size, max);
```

`struct snd_sg_buf` 实例会在 `substream->dma_private` 中创建。你可以像这样进行类型转换：

```c
struct snd_sg_buf *sgbuf = (struct snd_sg_buf *)substream->dma_private;
```

然后，在 `snd_pcm_lib_malloc_pages()` 调用中，通用的SG缓冲区处理器将会分配给定大小的非连续内核页面，并将它们映射为虚拟连续内存。虚拟指针可以通过 `runtime->dma_area` 访问。物理地址 (`runtime->dma_addr`) 被设置为零，因为缓冲区在物理上是非连续的。物理地址表在 `sgbuf->table` 中设置。你可通过 `snd_pcm_sgbuf_get_addr()` 函数获取特定偏移量处的物理地址。

如果你需要显式释放SG缓冲区数据，可以像往常一样调用标准API函数 `snd_pcm_lib_free_pages()`。
### Vmalloc分配的缓冲区

可以通过 `vmalloc()` 分配一个缓冲区，比如作为一个中间缓冲区。

你可以在设置了 `SNDRV_DMA_TYPE_VMALLOC` 类型的缓冲区预分配后简单地通过标准的 `snd_pcm_lib_malloc_pages()` 等函数进行分配：

```c
snd_pcm_set_managed_buffer_all(pcm, SNDRV_DMA_TYPE_VMALLOC,
                               NULL, 0, 0);
```

这里传递 NULL 作为设备指针参数，这表明将会分配默认页面（GFP_KERNEL 和 GFP_HIGHMEM）。

同时请注意，这里同时传递了0作为大小和最大大小的参数。由于每次 `vmalloc` 调用都应该成功，我们不需要像处理其他连续页面那样预先分配缓冲区。
### 采购接口
=============

ALSA为`procfs`提供了一个简单的接口。这些`proc`文件对于调试非常有用。如果你正在编写驱动程序并希望获取运行状态或寄存器转储，我建议你设置`proc`文件。API可以在`<sound/info.h>`中找到。
要创建一个`proc`文件，请调用函数`snd_card_proc_new()`：

```c
struct snd_info_entry *entry;
int err = snd_card_proc_new(card, "my-file", &entry);
```

其中第二个参数指定了要创建的`proc`文件的名称。上述示例将在卡目录下创建一个名为`my-file`的文件，例如`/proc/asound/card0/my-file`。
像其他组件一样，通过`snd_card_proc_new()`创建的`proc`条目将在卡注册和释放函数中自动注册和释放。
当创建成功时，该函数会在第三个参数所给定的指针中存储一个新的实例。它被初始化为只读文本`proc`文件。若要将此`proc`文件直接用作只读文本文件，则需要通过`snd_info_set_text_ops()`设置读取回调及私有数据：

```c
snd_info_set_text_ops(entry, chip, my_proc_read);
```

其中第二个参数(`chip`)是回调中使用的私有数据。第三个参数指定读取缓冲区大小，第四个参数(`my_proc_read`)是回调函数，定义如下：

```c
static void my_proc_read(struct snd_info_entry *entry,
                         struct snd_info_buffer *buffer);
```

在读取回调中，使用`snd_iprintf()`来输出字符串，这与普通的`printf()`函数的工作方式相同。例如：

```c
static void my_proc_read(struct snd_info_entry *entry,
                         struct snd_info_buffer *buffer)
{
        struct my_chip *chip = entry->private_data;

        snd_iprintf(buffer, "This is my chip!\n");
        snd_iprintf(buffer, "Port = %ld\n", chip->port);
}
```

可以之后更改文件权限。默认情况下，它们对所有用户都是只读的。如果你想添加用户的写入权限（默认为root），可以这样做：

```c
entry->mode = S_IFREG | S_IRUGO | S_IWUSR;
```

然后设置写入缓冲区大小和回调：

```c
entry->c.text.write = my_proc_write;
```

在写入回调中，你可以使用`snd_info_get_line()`来获取文本行，并使用`snd_info_get_str()`从行中检索字符串。`core/oss/mixer_oss.c`、`core/oss/`和`pcm_oss.c`中有一些例子。
对于原始数据`proc`文件，应这样设置属性：

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

对于原始数据，必须适当地设置`size`字段。这指定了`proc`文件访问的最大尺寸。
原始模式下的读取/写入回调比文本模式更为直接。你需要使用低级别的I/O函数如`copy_from_user()`和`copy_to_user()`来进行数据传输：

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

如果已正确设置了信息条目的大小，`count`和`pos`都保证适合于0到给定尺寸之间。除非有其他条件要求，否则无需在回调中检查范围。

### 功率管理
=============

如果芯片需要支持挂起/恢复功能，你需要在驱动程序中添加功率管理代码。功率管理相关的额外代码应该在`CONFIG_PM`条件下ifdef，或者注释为`__maybe_unused`属性；否则编译器会报错。
如果驱动程序*完全*支持挂起/恢复，也就是说设备可以在挂起调用后被正确地恢复到其状态，那么可以在PCM信息字段中设置`SNDRV_PCM_INFO_RESUME`标志。通常，当芯片的寄存器可以安全地保存和恢复到RAM中时，这是可能的。如果设置了这个标志，在恢复回调完成后会调用触发回调`SNDRV_PCM_TRIGGER_RESUME`。
即使驱动程序不完全支持PM，但仍然可以部分实现挂起/恢复，那么实施挂起/恢复回调仍然是值得的。在这种情况下，应用程序可以通过调用`snd_pcm_prepare()`重置状态，并适当地重新启动流。因此，可以定义下面的挂起/恢复回调，但不要在PCM信息标志中设置`SNDRV_PCM_INFO_RESUME`。
请注意，带有 `SUSPEND` 的触发器总是在调用 `:c:func:`snd_pcm_suspend_all()` 时被调用，无论是否有设置 ```SNDRV_PCM_INFO_RESUME``` 标志。`RESUME` 标志仅影响 `:c:func:`snd_pcm_resume()` 的行为。（因此，理论上，在没有设置 `SNDRV_PCM_INFO_RESUME` 标志的情况下，触发回调中不需要处理 `SNDRV_PCM_TRIGGER_RESUME`。但出于兼容性的原因，最好还是保留它。）

驱动程序需要根据设备所连接的总线定义挂起/恢复钩子。对于 PCI 驱动程序而言，回调函数看起来如下所示：

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

实际挂起任务的流程如下：

1. 获取卡片和芯片数据
2. 调用 `:c:func:`snd_power_change_state()` 并传入 `SNDRV_CTL_POWER_D3hot` 来改变电源状态
3. 如果使用了 AC97 编解码器，则对每个编解码器调用 `:c:func:`snd_ac97_suspend()`
4. 如果需要，保存寄存器值
5. 如果需要，停止硬件
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
          /* (4) */
          snd_mychip_save_registers(chip);
          /* (5) */
          snd_mychip_stop_hardware(chip);
          return 0;
  }
```

实际恢复任务的流程如下：

1. 获取卡片和芯片数据
2. 重新初始化芯片
3. 如果需要，恢复已保存的寄存器
4. 恢复混音器，例如通过调用 `:c:func:`snd_ac97_resume()`
5. 重启硬件（如果有的话）
调用 :c:func:`snd_power_change_state()` 并传入 `SNDRV_CTL_POWER_D0` 来通知各个进程。

典型的代码如下所示：

```c
static int __maybe_unused mychip_resume(struct pci_dev *pci)
{
        /* (1) */
        struct snd_card *card = dev_get_drvdata(pci->dev);
        struct mychip *chip = card->private_data;
        /* (2) */
        snd_mychip_reinit_chip(chip);
        /* (3) */
        snd_mychip_restore_registers(chip);
        /* (4）*/
        snd_ac97_resume(chip->ac97);
        /* (5) */
        snd_mychip_restart_chip(chip);
        /* (6) */
        snd_power_change_state(card, SNDRV_CTL_POWER_D0);
        return 0;
}
```

请注意，当此回调被调用时，PCM 流已经被通过它自己的电源管理操作（PM ops）暂停，内部调用了 :c:func:`snd_pcm_suspend_all()`。
好的，我们现在有了所有回调函数。让我们来设置它们。在声卡初始化过程中，确保可以从声卡实例中获取芯片数据，通常通过 `private_data` 字段获取，如果你是单独创建的芯片数据的话：

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

当你使用 :c:func:`snd_card_new()` 创建芯片数据时，它无论如何都可以通过 `private_data` 字段访问到：

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

以上是这段代码及其注释的中文翻译。
```chip = card->private_data;
          ...
}

// 如果你需要空间来保存寄存器，请在这里分配缓冲区，
// 因为如果你在挂起阶段无法分配内存，那将是致命的。
// 分配的缓冲区应在相应的析构函数中释放。

// 接下来，在pci_driver中设置挂起/恢复回调：

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
========

对于ALSA来说有标准的模块选项。至少，每个模块都应该有`index`、`id`和`enable`选项。
如果模块支持多张声卡（通常最多8张 = `SNDRV_CARDS`声卡），它们应该作为数组存在。默认初始值已经定义为常量以便于编程：

  static int index[SNDRV_CARDS] = SNDRV_DEFAULT_IDX;
  static char *id[SNDRV_CARDS] = SNDRV_DEFAULT_STR;
  static int enable[SNDRV_CARDS] = SNDRV_DEFAULT_ENABLE_PNP;

如果模块只支持一张声卡，它们可以是单个变量。在这种情况下`enable`选项并非总是必需的，但是为了兼容性最好还是有一个占位符选项。
模块参数必须使用标准的`module_param()`、`module_param_array()`和`:c:func:`MODULE_PARM_DESC()`宏声明。
典型的代码如下所示：

  #define CARD_NAME "My Chip"

  module_param_array(index, int, NULL, 0444);
  MODULE_PARM_DESC(index, "Index value for " CARD_NAME " soundcard.");
  module_param_array(id, charp, NULL, 0444);
  MODULE_PARM_DESC(id, "ID string for " CARD_NAME " soundcard.");
  module_param_array(enable, bool, NULL, 0444);
  MODULE_PARM_DESC(enable, "Enable " CARD_NAME " soundcard.");

同时不要忘记定义模块描述和许可证。
特别是，最近版本的modprobe要求定义模块许可证为GPL等，否则系统将显示为“被污染”。

设备管理资源
=============

在上述示例中，所有资源都是手动分配和释放的。但人性本懒，尤其是开发者更懒。
因此有一些方法可以自动化释放部分；这就是所谓的设备管理资源（devres或devm家族）。
例如，通过`:c:func:`devm_kmalloc()`分配的对象将在解绑设备时自动释放。
ALSA核心还提供了一个设备管理辅助函数，即`:c:func:`snd_devm_card_new()`用于创建声卡对象。
调用这个函数代替正常的`:c:func:`snd_card_new()`，你就可以忘记显式的`:c:func:`snd_card_free()`调用，
因为它会在错误和移除路径上自动调用。
需要注意的是，只有在调用`:c:func:`snd_card_register()`之后，`:c:func:`snd_card_free()`的调用才会放在调用链的最开始位置。
```
此外，“private_free”回调总是在声卡释放时被调用，
因此请务必在“private_free”回调中放入硬件清理程序。它甚至可能在你实际设置之前，在早期的错误路径中就被调用。为了避免这种无效初始化，你可以在 :c:func:`snd_card_register()` 调用成功后设置“private_free”回调。
另一个需要注意的是，一旦你以这种方式管理声卡，你应该尽可能多地为每个组件使用设备管理助手。混合使用正常和受管理资源可能会搞乱释放顺序。

如何将你的驱动程序加入ALSA树
=====================================

概述
-------

到目前为止，你已经学会了如何编写驱动程序代码。现在你可能有一个问题：如何将自己的驱动程序放入ALSA驱动程序树中？在这里（终于 :)），简要描述了标准流程。
假设你为名为“xyz”的声卡创建了一个新的PCI驱动程序。该声卡模块名称将是 snd-xyz。新驱动程序通常会放入 alsa-driver 树中，对于 PCI 声卡来说是 `sound/pci` 目录。
在以下各节中，假定驱动程序代码将放入 Linux 内核树中。这里涵盖两种情况：一个由单个源文件组成的驱动程序和一个由多个源文件组成的驱动程序。

单个源文件的驱动程序
--------------------------------

1. 修改 sound/pci/Makefile

   假设你有一个名为 xyz.c 的文件。添加如下两行代码：

     ```
     snd-xyz-y := xyz.o
     obj-$(CONFIG_SND_XYZ) += snd-xyz.o
     ```

2. 创建 Kconfig 入口

   为你的 xyz 驱动程序添加新的 Kconfig 条目：

   ```
   config SND_XYZ
     tristate "Foobar XYZ"
     depends on SND
     select SND_PCM
     help
       如果选择 Y，则包含对 Foobar XYZ 声卡的支持
       若要将此驱动程序编译为模块，请在此处选择 M：
       模块将被命名为 snd-xyz
     ```

`select SND_PCM` 这一行指定了 xyz 驱动支持 PCM 功能。
除了 SND_PCM 外，还支持以下组件用于 select 命令：SND_RAWMIDI, SND_TIMER, SND_HWDEP, SND_MPU401_UART, SND_OPL3_LIB, SND_OPL4_LIB, SND_VX_LIB, SND_AC97_CODEC。
为每个支持的组件添加 select 命令。
请注意，某些选择隐含了低级的选择。例如，
PCM 包含了 TIMER，MPU401_UART 包含了 RAWMIDI，AC97_CODEC 包含了 PCM，而 OPL3_LIB 包含了 HWDEP。您无需再次指定这些低级的选择。
有关 Kconfig 脚本的详细信息，请参阅 kbuild 文档。
具有多个源文件的驱动程序
----------------------------

假设驱动程序 snd-xyz 有多个源文件。它们位于新的子目录 sound/pci/xyz 中。

1. 在 `sound/pci/Makefile` 中添加一个新的目录 (`sound/pci/xyz`)，如下所示：

       ```
       obj-$(CONFIG_SND) += sound/pci/xyz/
       ```

2. 在目录 `sound/pci/xyz` 下创建一个 Makefile ：

       ```
       snd-xyz-y := xyz.o abc.o def.o
       obj-$(CONFIG_SND_XYZ) += snd-xyz.o
       ```

3. 创建 Kconfig 条目

   这个过程与上一节相同。

有用的函数
============

`snd_printk()` 及其相关函数
----------------------------------

.. note:: 本小节描述了一些用于增强标准 `printk()` 及其相关函数的辅助函数，
   然而，通常来说，使用这样的辅助函数不再被推荐。
   如果可能的话，尽量坚持使用像 `dev_err()` 或 `pr_err()` 这样的标准函数。

ALSA 提供了一个详细的 `printk()` 函数版本。
如果内核配置 `CONFIG_SND_VERBOSE_PRINTK` 被设置，则此函数会打印给定的消息以及调用者的文件名和行号。`KERN_XXX` 前缀也会被处理，就像原始的 `printk()` 函数那样，因此建议添加这个前缀，例如：`snd_printk(KERN_ERR "Oh my, sorry, it's extremely bad!\\n");`

还有用于调试的 `printk()`：
`snd_printd()` 可以用于一般的调试目的。
如果设置了`CONFIG_SND_DEBUG`，此函数将被编译，并且其工作方式与:c:func:`snd_printk()`相同。如果没有设置ALSA的调试标志，则该函数将被忽略。
:c:func:`snd_printdd()`仅在设置了`CONFIG_SND_DEBUG_VERBOSE`时才会被编译。
:c:func:`snd_BUG()`
-------------------

它会在当前点显示`BUG?`消息和堆栈跟踪，就像:c:func:`snd_BUG_ON()`一样。这对于显示致命错误发生在那里非常有用。
如果没有设置任何调试标志，此宏将被忽略。
:c:func:`snd_BUG_ON()`
----------------------

:c:func:`snd_BUG_ON()` 宏类似于:c:func:`WARN_ON()`宏。例如，可以使用`snd_BUG_ON(!pointer);`或者作为条件使用，如：如果 `(snd_BUG_ON(non_zero_is_bug))` 则返回 `-EINVAL`。

该宏接受一个条件表达式进行评估。当设置了 `CONFIG_SND_DEBUG` 时，如果表达式的值非零，它会显示警告消息（如 `BUG? (xxx)`），通常还会显示堆栈跟踪。在这两种情况下，它都会返回评估后的值。
致谢
=====

我要感谢Phil Kerr对改进和修正本文档的帮助。
Kevin Conder将原始纯文本格式转换为DocBook格式。
Giuliano Pochini纠正了拼写错误，并为硬件约束部分提供了示例代码。
