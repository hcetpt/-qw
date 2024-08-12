MTD NAND驱动编程接口
=====================

:作者: Thomas Gleixner

简介
============

通用NAND驱动几乎支持所有基于NAND和AG-AND的芯片，并将它们连接到Linux内核的Memory Technology Devices (MTD)子系统。
本文档是为希望实现适用于NAND设备的板级驱动或文件系统驱动的开发者提供的。

已知缺陷与假设
==========================

无

文档提示
===================

函数和结构体文档是自动生成的。每个函数和结构体成员都有一个用[XXX]标识符标记的简短描述。以下章节解释了这些标识符的意义。

函数标识符 [XXX]
--------------------------

函数在简短注释中被[XXX]标识符标记。这些标识符解释了函数的用途和范围。使用的标识符如下：

-  [MTD Interface]

   这些函数提供了与MTD内核API的接口。它们不可替换，提供完全与硬件无关的功能。
-  [NAND Interface]

   这些函数被导出并提供了与NAND内核API的接口。
-  [GENERIC]

   通用函数不可替换，提供完全与硬件无关的功能。
-  [DEFAULT]

   默认函数提供了适用于大多数实现的与硬件相关的功能。如果需要，板级驱动可以通过指针替换这些函数。这些函数通过NAND芯片描述结构中的指针调用。板级驱动可以在调用nand_scan()之前设置应由板级特定函数替换的函数。如果在进入nand_scan()时函数指针为NULL，则将其设置为适用于检测到的芯片类型的默认函数。

结构体成员标识符 [XXX]
-------------------------------

结构体成员在注释中标记有[XXX]标识符。这些标识符解释了成员的用途和范围。使用的标识符如下：

-  [INTERN]

   这些成员仅供NAND驱动内部使用，不得修改。这些值大多是从在nand_scan()期间评估的芯片几何信息计算得出的。
- [可替换]

   可替换成员包含与硬件相关的功能，这些功能可以由板级驱动程序提供。在调用 `nand_scan()` 之前，板级驱动程序可以设置需要通过板级特定函数来替代的功能。如果在进入 `nand_scan()` 时函数指针为 NULL，则该指针将被设置为适用于检测到的芯片类型的默认函数。

- [板级特定]

   板级特定成员包含必须由板级驱动程序提供的与硬件相关的信息。在调用 `nand_scan()` 之前，板级驱动程序必须设置函数指针和数据字段。

- [可选]

   可选成员可以保存对板级驱动程序有用的信息。通用 NAND 驱动代码不会使用这些信息。

基础板级驱动程序
==================

对于大多数板卡而言，仅仅提供基础功能并在 NAND 芯片描述结构中填充一些真正依赖于板卡的成员就足够了。

基础定义
--------------

至少，您需要提供一个 `nand_chip` 结构体以及用于存储 I/O 映射芯片地址的空间。您可以使用 `kmalloc` 分配 `nand_chip` 结构体，也可以静态分配它。NAND 芯片结构体嵌入了一个 MTD 结构体，该结构体会注册到 MTD 子系统。您可以使用 `nand_to_mtd()` 辅助函数从 NAND 芯片指针中提取 MTD 结构体的指针。

基于 `kmalloc` 的示例

::

    static struct mtd_info *board_mtd;
    static void __iomem *baseaddr;

静态示例

::

    static struct nand_chip board_chip;
    static void __iomem *baseaddr;

分区定义
-----------------

如果您希望将设备划分为多个分区，请定义适合您板卡的分区方案。
::

    #define NUM_PARTITIONS 2
    static struct mtd_partition partition_info[] = {
        { .name = "Flash partition 1",
          .offset =  0,
          .size =    8 * 1024 * 1024 },
        { .name = "Flash partition 2",
          .offset =  MTDPART_OFS_NEXT,
          .size =    MTDPART_SIZ_FULL },
    };

硬件控制函数
------------------------

硬件控制函数提供了对 NAND 芯片控制引脚的访问途径。可以通过 GPIO 引脚或地址线进行访问。如果您使用地址线，请确保满足定时要求。
### 基于GPIO的示例

```c
static void board_hwcontrol(struct mtd_info *mtd, int cmd)
{
    switch(cmd){
        case NAND_CTL_SETCLE: /* 将 CLE 引脚置高 */ break;
        case NAND_CTL_CLRCLE: /* 将 CLE 引脚置低 */ break;
        case NAND_CTL_SETALE: /* 将 ALE 引脚置高 */ break;
        case NAND_CTL_CLRALE: /* 将 ALE 引脚置低 */ break;
        case NAND_CTL_SETNCE: /* 将 nCE 引脚置低 */ break;
        case NAND_CTL_CLRNCE: /* 将 nCE 引脚置高 */ break;
    }
}
```

### 基于地址线的示例。假设 nCE 引脚由芯片选择解码器驱动

```c
static void board_hwcontrol(struct mtd_info *mtd, int cmd)
{
    struct nand_chip *this = mtd_to_nand(mtd);
    switch(cmd){
        case NAND_CTL_SETCLE: this->legacy.IO_ADDR_W |= CLE_ADRR_BIT;  break;
        case NAND_CTL_CLRCLE: this->legacy.IO_ADDR_W &= ~CLE_ADRR_BIT; break;
        case NAND_CTL_SETALE: this->legacy.IO_ADDR_W |= ALE_ADRR_BIT;  break;
        case NAND_CTL_CLRALE: this->legacy.IO_ADDR_W &= ~ALE_ADRR_BIT; break;
    }
}
```

### 设备就绪函数

如果硬件接口将NAND芯片的就绪/忙引脚连接到了GPIO或其它可访问的I/O引脚，此函数用于读取该引脚的状态。该函数没有参数，并且当设备处于忙状态（R/B引脚为低）时应返回0，当设备准备好（R/B引脚为高）时返回1。如果硬件接口无法访问就绪/忙引脚，则不应定义此函数，并将函数指针 `this->legacy.dev_ready` 设置为NULL。

### 初始化函数

初始化函数分配内存并设置所有特定于板卡的参数和函数指针。当一切都设置完毕后调用 `nand_scan()` 函数。该函数尝试检测并识别芯片。如果找到一个芯片，则根据情况初始化所有内部数据字段。结构体需要先清零，然后填充必要的设备信息。

```c
static int __init board_init (void)
{
    struct nand_chip *this;
    int err = 0;

    /* 分配 MTD 设备结构和私有数据的内存 */
    this = kzalloc(sizeof(struct nand_chip), GFP_KERNEL);
    if (!this) {
        printk ("无法分配 NAND MTD 设备结构。\n");
        err = -ENOMEM;
        goto out;
    }

    board_mtd = nand_to_mtd(this);

    /* 映射物理地址 */
    baseaddr = ioremap(CHIP_PHYSICAL_ADDRESS, 1024);
    if (!baseaddr) {
        printk("ioremap 访问 NAND 芯片失败\n");
        err = -EIO;
        goto out_mtd;
    }

    /* 设置 NAND IO 线的地址 */
    this->legacy.IO_ADDR_R = baseaddr;
    this->legacy.IO_ADDR_W = baseaddr;
    /* 引用硬件控制函数 */
    this->hwcontrol = board_hwcontrol;
    /* 设置命令延迟时间，参见数据手册获取正确值 */
    this->legacy.chip_delay = CHIP_DEPENDEND_COMMAND_DELAY;
    /* 如果可用，指定设备就绪函数 */
    this->legacy.dev_ready = board_dev_ready;
    this->eccmode = NAND_ECC_SOFT;

    /* 扫描以查找设备的存在 */
    if (nand_scan (this, 1)) {
        err = -ENXIO;
        goto out_ior;
    }

    add_mtd_partitions(board_mtd, partition_info, NUM_PARTITIONS);
    goto out;

out_ior:
    iounmap(baseaddr);
out_mtd:
    kfree (this);
out:
    return err;
}
module_init(board_init);
```

### 退出函数

如果驱动程序作为模块编译，则需要退出函数。它释放芯片驱动程序持有的所有资源，并在MTD层中取消注册分区。

```c
#ifdef MODULE
static void __exit board_cleanup (void)
{
    /* 取消注册设备 */
    WARN_ON(mtd_device_unregister(board_mtd));
    /* 释放资源 */
    nand_cleanup(mtd_to_nand(board_mtd));

    /* 取消映射物理地址 */
    iounmap(baseaddr);

    /* 释放 MTD 设备结构 */
    kfree (mtd_to_nand(board_mtd));
}
module_exit(board_cleanup);
#endif
```

### 高级板卡驱动功能

本章描述了NAND驱动程序的高级功能。有关可以被板卡驱动覆盖的函数列表，请参阅 `nand_chip` 结构的文档。
#### 多芯片控制

NAND驱动程序可以控制芯片阵列。因此，板卡驱动必须提供自己的 `select_chip` 函数。该函数必须（取消）选择请求的芯片。在调用 `nand_scan()` 之前，`nand_chip` 结构中的函数指针必须被设置。`nand_scan()` 的 `maxchip` 参数定义了要扫描的最大芯片数。确保 `select_chip` 函数能够处理请求的芯片数量。

NAND驱动程序将这些芯片串联成一个虚拟芯片，并向MTD层提供这个虚拟芯片。
**注意：驱动程序只能处理相同大小的线性芯片阵列。不支持扩展总线宽度的并行阵列。**

### 基于GPIO的示例

```c
static void board_select_chip (struct mtd_info *mtd, int chip)
{
    /* 取消选择所有芯片，将所有 nCE 引脚置高 */
    GPIO(BOARD_NAND_NCE) |= 0xff;
    if (chip >= 0)
        GPIO(BOARD_NAND_NCE) &= ~ (1 << chip);
}
```

### 基于地址线的示例。假设 nCE 引脚连接到地址解码器
```c
static void board_select_chip(struct mtd_info *mtd, int chip)
{
    struct nand_chip *this = mtd_to_nand(mtd);

    /* 取消选择所有芯片 */
    this->legacy.IO_ADDR_R &= ~BOARD_NAND_ADDR_MASK;
    this->legacy.IO_ADDR_W &= ~BOARD_NAND_ADDR_MASK;
    switch (chip) {
    case 0:
        this->legacy.IO_ADDR_R |= BOARD_NAND_ADDR_CHIP0;
        this->legacy.IO_ADDR_W |= BOARD_NAND_ADDR_CHIP0;
        break;
    ...
    case n:
        this->legacy.IO_ADDR_R |= BOARD_NAND_ADDR_CHIPn;
        this->legacy.IO_ADDR_W |= BOARD_NAND_ADDR_CHIPn;
        break;
    }
}
```

硬件ECC支持
------------

函数和常量
~~~~~~~~~~~

NAND驱动程序支持以下三种类型的硬件ECC：
- `NAND_ECC_HW3_256`

  提供每256字节3字节ECC的硬件ECC生成器。
- `NAND_ECC_HW3_512`

  提供每512字节3字节ECC的硬件ECC生成器。
- `NAND_ECC_HW6_512`

  提供每512字节6字节ECC的硬件ECC生成器。
- `NAND_ECC_HW8_512`

  提供每512字节8字节ECC的硬件ECC生成器。

如果您的硬件生成器具有不同的功能，请在`nand_base.c`中适当的位置添加它。

板级驱动程序必须提供以下函数：

- `enable_hwecc`

  此函数在读取/写入芯片之前被调用。在此函数中重置或初始化硬件生成器。该函数带有一个参数，可让您区分读取和写入操作。
- `calculate_ecc`

  此函数在从/向芯片读取/写入后被调用。将ECC从硬件转移到缓冲区。如果设置了`NAND_HWECC_SYNDROME`选项，则此函数仅在写入时被调用。请参阅下面的内容。
- `correct_data`

  在发生ECC错误的情况下，此函数被调用进行错误检测和校正。如果可以纠正错误，则返回1或2。如果错误无法纠正，则返回-1。如果您的硬件生成器与NAND_ECC软件生成器默认算法匹配，则使用NAND_ECC提供的校正函数，而不是实现重复代码。```
硬件ECC与校验和计算
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

许多硬件ECC实现提供了Reed-Solomon编码，并在读取时计算错误校验和。校验和必须转换为标准的Reed-Solomon校验和，然后才能调用通用Reed-Solomon库中的错误校正码。
ECC字节必须立即放置在数据字节之后，以便使校验和生成器正常工作。这与软件ECC通常使用的布局相反。数据和带外区域之间的分离不再可能。NAND驱动程序代码处理这种布局，而带外区域中剩余的空闲字节由自动放置代码管理。在这种情况下提供一个匹配的带外布局。参见rts_from4.c和diskonchip.c以获取实现参考。在这种情况下，我们还必须在FLASH上使用坏块表，因为ECC布局会干扰坏块标记的位置。有关详细信息，请参阅坏块表支持。
坏块表支持
-----------------------

大多数NAND芯片在带外区域的固定位置标记坏块。这些块在任何情况下都不能被擦除，否则坏块信息将会丢失。每次访问块时，可以通过读取块中第一页的带外区域来检查坏块标记。这很耗时，因此使用了坏块表。
NAND驱动程序支持多种类型的坏块表：
- 每设备

   坏块表包含了设备的所有坏块信息，该设备可能包含多个芯片。
- 每芯片

   每个芯片使用一个坏块表，并包含了特定芯片的坏块信息。
- 固定偏移

   坏块表位于芯片（或设备）的固定偏移处。这适用于各种DiskOnChip设备。
- 自动放置

   坏块表自动放置并检测到芯片（或设备）的末尾或开始位置。
- 镜像表

   坏块表在芯片（或设备）上镜像，以允许在不丢失数据的情况下更新坏块表。

`nand_scan()`调用函数`nand_default_bbt()`。
`nand_default_bbt()`根据`nand_scan()`检索的芯片信息选择适当的默认坏块表描述符。
标准策略是扫描设备以查找坏块，并构建基于RAM的坏块表，这允许比始终在闪存芯片上检查坏块信息更快的访问。
基于闪存的表格
~~~~~~~~~~~~~~~~~~

可能需要或将坏块表保存在闪存中。对于AG-AND芯片而言，这是强制性的，因为它们没有工厂标记的坏块。它们有工厂标记的良好块。当块被擦除以便重用时，标记模式会被清除。因此，在将该模式写回芯片之前发生电源丢失的情况下，此块将丢失并被添加到坏块列表中。因此，当我们首次检测到芯片时，我们会对其进行良好块的扫描，并在擦除任何块之前将这些信息存储在坏块表中。
存储表格的块通过在内存坏块表中标记为坏块来防止意外访问。坏块表管理功能可以绕过这种保护。
激活基于闪存的坏块表支持的最简单方法是在调用`nand_scan()`之前设置nand芯片结构中的`bbt_option`字段中的`NAND_BBT_USE_FLASH`选项。对于AG-AND芯片，默认情况下会执行此操作。这激活了NAND驱动程序默认的基于闪存的坏块表功能。默认的坏块表选项包括：

-  每个芯片存储一个坏块表

-  每个块使用2位

-  自动放置于芯片末尾

-  使用带有版本号的镜像表格

-  在芯片末尾预留4个块

用户定义的表格
~~~~~~~~~~~~~~~~~~~

用户定义的表格是通过填写`nand_bbt_descr`结构并在调用`nand_scan()`之前将其指针存储在nand_chip结构成员`bbt_td`中创建的。如果需要镜像表格，则必须创建第二个结构，并且必须将指向该结构的指针存储在nand_chip结构中的`bbt_md`内。如果将`bbt_md`成员设置为NULL，则仅使用主表，并且不会进行镜像表扫描。
`nand_bbt_descr`结构中最重要的字段是`options`字段。这些选项定义了大多数表格属性。使用来自`rawand.h`的预定义常量来定义选项。

-  每个块的位数

   支持的位数是1、2、4、8
-  每芯片一张表

   设置常量`NAND_BBT_PERCHIP`选择为芯片数组中的每个芯片管理一个坏块表。如果不设置此选项，则使用每设备的坏块表
-  表位置是绝对的

   使用常量`NAND_BBT_ABSPAGE`并定义坏块表开始的绝对页号在`pages`字段中。如果您选择了每个芯片的坏块表并且您有一个多芯片数组，则必须为该数组中的每个芯片给出起始页。注意：不会执行表标识模式扫描，因此`pattern`、`veroffs`、`offs`和`len`字段可以保持未初始化状态

-  表位置自动检测

   表格可以位于芯片（设备）的第一个或最后一个良好块中。设置`NAND_BBT_LASTBLOCK`将坏块表置于芯片（设备）的末尾。坏块表通过存储在包含坏块表的块的第一页备用区域中的模式进行标记和识别。在`pattern`字段中存储指向该模式的指针。此外，必须在`nand_bbt_descr`结构的`len`中存储模式的长度，并在`offs`成员中给出备用区域中的偏移量
对于镜像的坏块表，需要不同的模式
-  表格创建

   设置`NAND_BBT_CREATE`选项以启用在扫描过程中找不到表格时的表格创建。通常，这仅在发现新芯片时执行一次。
- 表写入支持

   设置NAND_BBT_WRITE选项以启用表写入支持。
   这允许在因磨损需要标记坏块时更新坏块表。
   MTD接口函数block_markbad会调用坏块表的更新函数。
   如果启用了写入支持，则会在FLASH上更新表。
   注意：写入支持仅应为带有版本控制的镜像表启用。

- 表版本控制

   设置NAND_BBT_VERSION选项以启用表版本控制。
   对于带有写入支持的镜像表，强烈建议启用此功能。
   它确保了丢失坏块表信息的风险降低到仅丢失一个应该被标记为坏块的磨损块的信息。版本号存储在设备空闲区域中的连续4个字节中。版本号的位置由坏块表描述符中的成员veroffs定义。

- 在写入时保存块内容

   如果包含坏块表的块还包含其他有用信息，请设置NAND_BBT_SAVECONTENT选项。
   当写入坏块表时，整个块将被读取，坏块表会被更新，然后块被擦除，所有内容都会被重新写回。
   如果未设置此选项，则仅写入坏块表，块中的其他内容将被忽略并擦除。

- 预留块的数量

   为了自动放置，必须预留一些块用于坏块表存储。
   预留块的数量在坏块表描述结构的maxblocks成员中定义。
   为镜像表预留4个块应该是一个合理的数量。
   这也限制了扫描坏块表标识模式的块数。

自动（空闲区）放置
----------------------

NAND驱动程序实现了多种可能性来在空闲区放置文件系统数据，

- 由文件系统驱动程序定义的放置

- 自动放置

默认放置函数是自动放置。NAND驱动程序为各种芯片类型内置了默认的放置方案。
如果由于硬件ECC功能导致默认放置不适合，则板级驱动程序可以提供自己的放置方案。
文件系统驱动程序可以提供自己的布局方案，该方案用于替代默认的布局方案。布局方案由 `nand_oobinfo` 结构体定义：

```c
struct nand_oobinfo {
    int useecc;       // 控制ECC和布局功能
    int eccbytes;     // 每页的ECC字节数
    int eccpos[24];   // ECC码放置的备用区域中的字节偏移量
    int oobfree[8][2];// 可用于自动布局的备用区域中的区域
};
```

- `useecc`

   `useecc` 成员控制ECC和布局功能。头文件 `include/mtd/mtd-abi.h` 包含选择ECC和布局的常量。`MTD_NANDECC_OFF` 完全关闭ECC，这不建议使用，仅用于测试和诊断。`MTD_NANDECC_PLACE` 选择调用者定义的布局，而 `MTD_NANDECC_AUTOPLACE` 选择自动布局。

- `eccbytes`

   `eccbytes` 成员定义每页的ECC字节数。

- `eccpos`

   `eccpos` 数组保存备用区域中ECC码放置的字节偏移量。

- `oobfree`

   `oobfree` 数组定义了可以在备用区域中使用的区域。信息以 `{offset, size}` 的格式给出。`offset` 定义可用区域的起始位置，`size` 定义长度（字节数）。可以定义多个区域。列表以 `{0, 0}` 结束。

由文件系统驱动程序定义的布局
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

调用函数提供一个指向 `nand_oobinfo` 结构体的指针，该结构体定义了ECC的布局。对于写操作，调用者必须提供一个备用区域缓冲区以及数据缓冲区。备用区域缓冲区的大小为（页数）*（备用区域的大小）。对于读操作，缓冲区大小为（页数）*（备用区域的大小 + 每页ECC步骤数 * `sizeof(int)`）。驱动程序将每个元组的ECC检查结果存储在备用缓冲区中。存储顺序如下：

```
<备用数据页0><ECC结果0>...<ECC结果n>
...
<备用数据页n><ECC结果0>...<ECC结果n>
```

这是YAFFS1使用的遗留模式。
如果备用区域缓冲区为NULL，则仅根据 `nand_oobinfo` 结构体中给定的方案进行ECC布局。

自动布局
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

自动布局使用内置默认值将ECC字节放置在备用区域中。如果需要将文件系统数据存储/读取到备用区域中，则调用函数必须提供一个缓冲区。每页的缓冲区大小由 `nand_oobinfo` 结构体中的 `oobfree` 数组确定。
如果备用区域缓冲区为NULL，则仅根据默认内置方案放置ECC。

备用区域自动放置的默认方案
----------------------------------------

256字节页面大小
~~~~~~~~~~~~~~~~~

======== ================== ===================================================
偏移量   内容              注释
======== ================== ===================================================
0x00     ECC字0             错误校正码字0
0x01     ECC字1             错误校正码字1
0x02     ECC字2             错误校正码字2
0x03     自动放置0
0x04     自动放置1
0x05     坏块标记           如果该字节中的任何位为零，则表示该块是坏块。这仅适用于一个块中的第一页，在其余页中，该字节保留
0x06     自动放置2
0x07     自动放置3
======== ================== ===================================================

512字节页面大小
~~~~~~~~~~~~~~~~~

============= ================== ==============================================
偏移量        内容              注释
============= ================== ==============================================
0x00          ECC字0             本页下256字节数据的错误校正码字0
0x01          ECC字1             本页下256字节数据的错误校正码字1
0x02          ECC字2             本页下256字节数据的错误校正码字2
0x03          ECC字3             本页上256字节数据的错误校正码字0
0x04          保留               保留
0x05          坏块标记           如果该字节中的任何位为零，则表示该块是坏块。这仅适用于一个块中的第一页，在其余页中，该字节保留
0x06          ECC字4             本页上256字节数据的错误校正码字1
0x07          ECC字5             本页上256字节数据的错误校正码字2
0x08 - 0x0F   自动放置0 - 7
============= ================== ==============================================

2048字节页面大小
~~~~~~~~~~~~~~~~~~

=========== ================== ================================================
偏移量      内容              注释
=========== ================== ================================================
0x00        坏块标记           如果该字节中的任何位为零，则表示该块是坏块。这仅适用于一个块中的第一页，在其余页中，该字节保留
0x01        保留               保留
0x02-0x27   自动放置0 - 37
0x28        ECC字0             本页前256字节数据的错误校正码字0
0x29        ECC字1             本页前256字节数据的错误校正码字1
0x2A        ECC字2             本页前256字节数据的错误校正码字2
0x2B        ECC字3             本页第二256字节数据的错误校正码字0
0x2C        ECC字4             本页第二256字节数据的错误校正码字1
0x2D        ECC字5             本页第二256字节数据的错误校正码字2
0x2E        ECC字6             本页第三256字节数据的错误校正码字0
0x2F        ECC字7             本页第三256字节数据的错误校正码字1
0x30        ECC字8             本页第三256字节数据的错误校正码字2
0x31        ECC字9             本页第四256字节数据的错误校正码字0
0x32        ECC字10            本页第四256字节数据的错误校正码字1
0x33        ECC字11            本页第四256字节数据的错误校正码字2
0x34        ECC字12            本页第五256字节数据的错误校正码字0
0x35        ECC字13            本页第五256字节数据的错误校正码字1
0x36        ECC字14            本页第五256字节数据的错误校正码字2
0x37        ECC字15            本页第六256字节数据的错误校正码字0
0x38        ECC字16            本页第六256字节数据的错误校正码字1
0x39        ECC字17            本页第六256字节数据的错误校正码字2
0x3A        ECC字18            本页第七256字节数据的错误校正码字0
0x3B        ECC字19            本页第七256字节数据的错误校正码字1
0x3C        ECC字20            本页第七256字节数据的错误校正码字2
0x3D        ECC字21            本页第八256字节数据的错误校正码字0
0x3E        ECC字22            本页第八256字节数据的错误校正码字1
0x3F        ECC字23            本页第八256字节数据的错误校正码字2
=========== ================== ================================================

文件系统支持
==================

NAND驱动程序通过MTD接口提供了所有必要的功能给文件系统。
文件系统必须意识到NAND的特点和限制。
NAND Flash的一个主要限制是，你不能想写多少次就写多少次到一个页面。在重新擦除之前对一个页面的连续写入次数被限制在1到3次，具体取决于制造商的规格。这对备用区域同样适用。
因此，支持NAND的文件系统必须以页面大小的块进行写入或保持一个写缓冲区来收集较小的写操作直到它们累加到页面大小。可用的支持NAND的文件系统：JFFS2、YAFFS。
使用备用区域来存储文件系统数据由前面章节描述的备用区域放置功能控制。

工具
=====

MTD项目提供了一些有用的工具来处理NAND Flash：
-  flasherase, flasheraseall: 擦除和格式化FLASH分区
-  nandwrite: 将文件系统映像写入NAND FLASH
-  nanddump: 转储NAND FLASH分区的内容

这些工具意识到了NAND的限制。请使用这些工具，而不是抱怨由于非NAND感知访问方法导致的错误。

常量
=========

这一章描述了可能对驱动开发者相关的常量。

芯片选项常量
---------------------

芯片ID表中的常量
~~~~~~~~~~~~~~~~~~~~~~~~~~~

这些常量定义在rawnand.h中。它们被一起使用来描述芯片的功能：

    /* 总线宽度为16位 */
    #define NAND_BUSWIDTH_16    0x00000002
    /* 设备支持无填充的部分编程 */
    #define NAND_NO_PADDING     0x00000004
    /* 芯片具有缓存编程功能 */
    #define NAND_CACHEPRG       0x00000008
    /* 芯片具有回拷功能 */
    #define NAND_COPYBACK       0x00000010
    /* AND型芯片，有4个库和混乱的页/块分配。请参阅Renesas的数据手册获取更多信息 */
    #define NAND_IS_AND     0x00000020
    /* 芯片有一个可以无需额外的就绪/忙等待就可以读取的4页数组 */
    #define NAND_4PAGE_ARRAY    0x00000040

运行时选项的常量
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

这些常量定义在rawnand.h中。它们被一起使用来描述功能：

    /* 硬件ECC生成器在读取时提供的是综合症而不是ECC值
     * 这只在我们有ECC字节直接位于数据字节后面的情况下有效。适用于DOC和AG-AND Renesas硬件Reed Solomon生成器 */
    #define NAND_HWECC_SYNDROME 0x00020000

ECC选择常量
-----------------------

使用这些常量来选择ECC算法：

    /* 没有ECC。不建议使用！ */
    #define NAND_ECC_NONE       0
    /* 软件ECC 3字节ECC每256字节数据 */
    #define NAND_ECC_SOFT       1
    /* 硬件ECC 3字节ECC每256字节数据 */
    #define NAND_ECC_HW3_256    2
    /* 硬件ECC 3字节ECC每512字节数据 */
    #define NAND_ECC_HW3_512    3
    /* 硬件ECC 6字节ECC每512字节数据 */
    #define NAND_ECC_HW6_512    4
    /* 硬件ECC 8字节ECC每512字节数据 */
    #define NAND_ECC_HW8_512    6

与硬件控制相关的常量
----------------------------------

这些常量描述了当调用特定于板卡的硬件控制函数时请求的硬件访问功能：

    /* 通过将nCE设为低电平来选择芯片 */
    #define NAND_CTL_SETNCE     1
    /* 通过将nCE设为高电平来取消选择芯片 */
    #define NAND_CTL_CLRNCE     2
    /* 通过将CLE设为高电平来选择命令锁存器 */
    #define NAND_CTL_SETCLE     3
    /* 通过将CLE设为低电平来取消选择命令锁存器 */
    #define NAND_CTL_CLRCLE     4
    /* 通过将ALE设为高电平来选择地址锁存器 */
    #define NAND_CTL_SETALE     5
    /* 通过将ALE设为低电平来取消选择地址锁存器 */
    #define NAND_CTL_CLRALE     6
    /* 通过将WP设为高电平来设置写保护。未使用！ */
    #define NAND_CTL_SETWP      7
    /* 通过将WP设为低电平来清除写保护。未使用！ */
    #define NAND_CTL_CLRWP      8

与坏块表相关的常量
---------------------------------

这些常量描述了用于坏块表描述符的选项：

    /* 用于设备上的坏块表描述符中每个块使用的位数 */
    #define NAND_BBT_NRBITS_MSK 0x0000000F
    #define NAND_BBT_1BIT       0x00000001
    #define NAND_BBT_2BIT       0x00000002
    #define NAND_BBT_4BIT       0x00000004
    #define NAND_BBT_8BIT       0x00000008
    /* 坏块表位于设备的最后一个好块 */
    #define NAND_BBT_LASTBLOCK  0x00000010
    /* 坏块表位于给定页，否则我们必须扫描坏块表 */
    #define NAND_BBT_ABSPAGE    0x00000020
    /* 在多芯片设备上，坏块表按芯片存储 */
    #define NAND_BBT_PERCHIP    0x00000080
    /* 坏块表在偏移量veroffs处有一个版本计数器 */
    #define NAND_BBT_VERSION    0x00000100
    /* 如果不存在坏块表，则创建一个 */
    #define NAND_BBT_CREATE     0x00000200
    /* 必要时写入坏块表 */
    #define NAND_BBT_WRITE      0x00001000
    /* 在写入坏块表时读取并写回块内容 */
    #define NAND_BBT_SAVECONTENT    0x00002000

结构体
==========

这一章包含了NAND驱动程序中使用的结构体自动生成的文档，这些结构体可能对驱动开发者相关。每个结构体成员都有一个带有[XXX]标识符的简短描述。请参阅“文档提示”章节以了解解释。
### 内核文档说明：include/linux/mtd/rawnand.h
   ：内部：

#### 提供的公共函数
=========================

本章包含NAND内核API函数自动生成的文档，这些函数是公开导出的。每个函数都有一个带有[XXX]标识符的简短描述。请参阅“文档提示”章节以获取解释。
.. kernel-doc:: drivers/mtd/nand/raw/nand_base.c
   ：导出：

#### 提供的内部函数
===========================

本章包含NAND驱动程序内部函数自动生成的文档。每个函数都有一个带有[XXX]标识符的简短描述。请参阅“文档提示”章节以获取解释。标记为[DEFAULT]的函数可能对板级驱动开发者来说很重要。
.. kernel-doc:: drivers/mtd/nand/raw/nand_base.c
   ：内部：

.. kernel-doc:: drivers/mtd/nand/raw/nand_bbt.c
   ：内部：

#### 致谢
=======

以下人员为NAND驱动程序做出了贡献：

1. Steven J. Hill\ sjhill@realitydiluted.com

2. David Woodhouse\ dwmw2@infradead.org

3. Thomas Gleixner\ tglx@linutronix.de

许多用户提供了错误修复、改进和帮助测试。非常感谢！

以下人员为本文档做出了贡献：

1. Thomas Gleixner\ tglx@linutronix.de
