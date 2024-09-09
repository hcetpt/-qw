```spdx
许可协议标识符: GPL-2.0

=====================
Chrome OS ACPI 设备
=====================

Chrome OS 的特定硬件功能通过 Chrome OS ACPI 设备暴露出来。
Chrome OS ACPI 设备的即插即用 ID 是 GGL0001，硬件 ID 是 GOOG0016。以下为支持的 ACPI 对象：

.. flat-table:: 支持的 ACPI 对象
   :widths: 1 2
   :header-rows: 1

   * - 对象
     - 描述

   * - CHSW
     - Chrome OS 开关位置

   * - HWID
     - Chrome OS 硬件 ID

   * - FWID
     - Chrome OS 固件版本

   * - FRID
     - Chrome OS 只读固件版本

   * - BINF
     - Chrome OS 引导信息

   * - GPIO
     - Chrome OS GPIO 分配

   * - VBNV
     - Chrome OS NVRAM 位置

   * - VDTA
     - Chrome OS 验证引导数据

   * - FMAP
     - Chrome OS 闪存映射基地址

   * - MLST
     - Chrome OS 方法列表

CHSW（Chrome OS 开关位置）
=================================
此控制方法返回 Chrome OS 特定硬件开关的位置。
参数：
----------
无

结果代码：
------------
一个整数，包含以位字段形式表示的开关位置：

.. flat-table::
   :widths: 1 2

   * - 0x00000002
     - x86 固件启动时按下了恢复按钮
* - 0x00000004
     - EC 固件启动时按下了恢复按钮。（如果 EC EEPROM 可重写，则必须；否则可选）

   * - 0x00000020
     - x86 固件启动时启用了开发者开关
* - 0x00000200
     - x86 固件启动时禁用了固件写保护。（如果固件写保护由 x86 BIOS 控制，则必须；否则可选）

所有其他位保留，并应设置为 0。

HWID（Chrome OS 硬件 ID）
============================
此控制方法返回 Chromebook 的硬件 ID。
参数：
----------
无

结果代码：
------------
一个空终止的 ASCII 字符串，包含 EEPROM 模型特定数据区域中的硬件 ID。
请注意，硬件 ID 最长可以达到 256 个字符，包括终止的空字符。

FWID（Chrome OS 固件版本）
=================================
此控制方法返回主处理器固件可重写部分的固件版本。
参数：
----------
无

结果代码：
------------
一个空终止的 ASCII 字符串，包含主处理器固件可重写部分的完整固件版本。
```
FRID（Chrome OS 只读固件版本）
===========================================
此控制方法返回主处理器固件只读部分的固件版本。
参数：
----------
无

结果代码：
------------
一个以空字符终止的 ASCII 字符串，包含主处理器固件只读部分（引导 + 恢复）的完整固件版本。

BINF（Chrome OS 引导信息）
=================================
此控制方法返回当前引导的信息。
参数：
----------
无

结果代码：
------------

.. code-block::

   Package {
           Reserved1
           Reserved2
           Active EC Firmware
           Active Main Firmware Type
           Reserved5
   }

.. flat-table::
   :widths: 1 1 2
   :header-rows: 1

   * - 字段
     - 格式
     - 描述

   * - Reserved1
     - DWORD
     - 设置为 256 (0x100)。这表示该字段不再使用。
   * - Reserved2
     - DWORD
     - 设置为 256 (0x100)。这表示该字段不再使用。
   * - Active EC Firmware
     - DWORD
     - 引导过程中使用的 EC 固件
- 0 - 只读（恢复）固件
- 1 - 可重写固件
如果 EC 固件始终为只读，则设置为 0。
   * - Active Main Firmware Type
     - DWORD
     - 引导过程中使用的主固件类型
- 0 - 恢复
- 1 - 正常
- 2 - 开发者
- 3 - netboot（仅限工厂安装）

其他值保留。
* - Reserved5
     - DWORD
     - 设置为 256 (0x100)。这表示该字段不再使用
GPIO (Chrome OS GPIO 分配)
=================================
此控制方法返回有关 Chrome OS 硬件特定的 GPIO 分配信息，以便内核可以直接控制该硬件
参数:
----------
无

结果代码:
------------
.. code-block::

        Package {
                Package {
                        // 第一个 GPIO 分配
                        Signal Type        //DWORD
                        Attributes         //DWORD
                        Controller Offset  //DWORD
                        Controller Name    //ASCIIZ
                },
                ..
                Package {
                        // 最后一个 GPIO 分配
                        Signal Type        //DWORD
                        Attributes         //DWORD
                        Controller Offset  //DWORD
                        Controller Name    //ASCIIZ
                }
        }

其中 ASCIIZ 表示以空字符终止的 ASCII 字符串
.. flat-table::
   :widths: 1 1 2
   :header-rows: 1

   * - 字段
     - 格式
     - 描述

   * - Signal Type
     - DWORD
     - GPIO 信号类型

       - 0x00000001 - 恢复按钮
       - 0x00000002 - 开发者模式开关
       - 0x00000003 - 固件写保护开关
       - 0x00000100 - 调试头 GPIO 0
       - ..
       - 0x000001FF - 调试头 GPIO 255

       其他值保留
* - Attributes
     - DWORD
     - 信号属性作为位字段：

       - 0x00000001 - 信号为高电平有效（对于按钮，GPIO 值为 1 表示按钮被按下；对于开关，GPIO 值为 1 表示开关已启用）。如果此位为 0，则信号为低电平有效。调试头 GPIO 设置为 0
* - Controller Offset
     - DWORD
     - 指定控制器上的 GPIO 编号
* - Controller Name
     - ASCIIZ
     - GPIO 的控制器名称
当前支持的名称：
       "NM10" - Intel NM10 芯片

VBNV (Chrome OS NVRAM 位置)
=================================
此控制方法返回有关用于与 BIOS 通信的 NVRAM (CMOS) 位置的信息
### 参数：
----------
无

### 结果代码：
------------
```plaintext
Package {
        NV Storage Block Offset  //DWORD
        NV Storage Block Size    //DWORD
}
```

| 字段                     | 格式 | 描述                                                                 |
|--------------------------|------|----------------------------------------------------------------------|
| NV Storage Block Offset  | DWORD | 验证启动非易失性存储块在CMOS Bank 0中的偏移量，从第一个可写CMOS字节开始计数（即，偏移量为0的字节是14个时钟数据字节之后的一个字节） |
| NV Storage Block Size    | DWORD | 验证启动非易失性存储块的大小（以字节为单位）                          |

### FMAP (Chrome OS flashmap 地址)
=================================
此控制方法返回主处理器固件 flashmap 的物理内存地址。

### 参数：
----------
无

### 结果代码：
----------------
包含主处理器固件 flashmap 起始物理内存地址的 DWORD 值。

### VDTA (Chrome OS 验证启动数据)
===================================
此控制方法返回验证启动过程中固件验证步骤和内核验证步骤之间共享的验证启动数据块。

### 参数：
----------
无

### 结果代码：
------------
包含验证启动数据块的缓冲区。

### MECK (管理引擎校验和)
=================================
此控制方法返回在启动期间从管理引擎扩展寄存器读取的 SHA-1 或 SHA-256 哈希值。该哈希值通过 ACPI 导出，以便操作系统可以验证管理引擎固件是否已更改。如果管理引擎不存在或固件无法读取扩展寄存器，则此缓冲区可以为零。

### 参数：
----------
无

### 结果代码：
------------
包含 ME 哈希值的缓冲区。

### MLST (Chrome OS 方法列表)
============================
此控制方法返回 Chrome OS 硬件设备支持的其他控制方法列表。

### 参数：
----------
无

### 结果代码：
------------
包含一个由空终止的 ASCII 字符串组成的包，每个字符串对应 Chrome OS 硬件设备支持的一个控制方法（不包括 MLST 方法本身）。
对于此版本的规范，结果是：

.. code-block::

    Package {
            "CHSW",
            "FWID",
            "HWID",
            "FRID",
            "BINF",
            "GPIO",
            "VBNV",
            "FMAP",
            "VDTA",
            "MECK"
    } 

（注：这里的代码块展示了一个包含多个字符串的包结构）
