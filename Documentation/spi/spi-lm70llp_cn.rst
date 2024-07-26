==============================================
spi_lm70llp : LM70-LLP 并口至 SPI 适配器
==============================================

支持的板卡/芯片：

  * National Semiconductor LM70 LLP 评估板

    数据手册: https://www.ti.com/lit/gpn/lm70

作者:
        Kaiwan N Billimoria <kaiwan@designergraphix.com>

描述
-----------
此驱动程序提供了将 National Semiconductor LM70 LLP 温度传感器评估板连接到内核 SPI 核心子系统的粘合代码。
这是一个 SPI 主控制器驱动程序。它可以与 LM70 逻辑驱动程序（一个“SPI 协议驱动程序”）结合使用（层叠在其下）。
实际上，此驱动程序将评估板上的并行接口转换为带有单个设备的 SPI 总线，该设备将由通用 LM70 驱动程序（drivers/hwmon/lm70.c）驱动。
硬件接口
--------------------
此特定板卡（LM70EVAL-LLP）的原理图可以在以下页面找到（第 4 页）：

  https://download.datasheets.com/pdfs/documentation/nat/kit&board/lm70llpevalmanual.pdf

LM70 LLP 评估板上的硬件接口如下所示：

   ======== == =========   ==========
   并行端口                 LM70 LLP
     端口   .  方向   JP2 接头
   ======== == =========   ==========
      D0     2      -         -
      D1     3     -->      V+   5
      D2     4     -->      V+   5
      D3     5     -->      V+   5
      D4     6     -->      V+   5
      D5     7     -->      nCS  8
      D6     8     -->      SCLK 3
      D7     9     -->      SI/O 5
     GND    25      -       GND  7
    Select  13     <--      SI/O 1
   ======== == =========   ==========

请注意，由于 LM70 使用的是 SPI 的“三线”变体，因此 SI/SO 引脚同时连接到了引脚 D7（作为主输出）和 Select（作为主输入），通过一种让并行端口或 LM70 能够拉低该引脚的安排。这不能与真正的 SPI 设备共享，但其他三线设备可能共享相同的 SI/SO 引脚。
此驱动程序中的位敲击例程（lm70_txrx）通过其 sysfs 钩子从绑定的“hwmon/lm70”协议驱动程序调用，使用 spi_write_then_read() 函数调用。它执行模式 0（SPI/Microwire）位敲击。
然后，lm70 驱动程序解析出的结果数字温度值，并通过 sysfs 导出。

一个需要注意的地方：National Semiconductor 的 LM70 LLP 评估板电路原理图显示，来自 LM70 芯片的 SI/O 线连接到了晶体管 Q1 的基极（同时也连接了一个上拉电阻和一个齐纳二极管到 D7）；而集电极则与 VCC 连接。
解释这个电路时，当 LM70 的 SI/O 线处于高电平（或三态且未被主机通过 D7 拉低）时，晶体管导通并使集电极的电压变为零，这反映在 DB25 并行端口连接器的第 13 引脚上。当 SI/O 处于低电平时（由 LM70 或主机驱动），晶体管截止，与其集电极相连的电压则反映在第 13 引脚上作为高电平。
因此：此驱动程序中的 getmiso 内联函数考虑到了这一事实，对读取第 13 引脚的值进行了反转。

致谢
---------

- David Brownell 对 SPI 驱动程序开发的指导
- 霍拉巴赫博士（Dr. Craig Hollabaugh）为早期的“手动”位敲击驱动程序版本
- 纳迪尔·比利莫利亚（Nadir Billimoria）帮助解读电路图
