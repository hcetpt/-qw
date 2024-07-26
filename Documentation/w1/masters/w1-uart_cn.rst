SPDX 许可证标识符: GPL-2.0 或更高版本

=====================
内核驱动程序 w1-uart
=====================

作者: Christoph Winklhofer <cj.winklhofer@gmail.com>

---

描述
---

这是一个 UART 1-Wire 总线驱动程序。该驱动程序通过串行设备总线利用 UART 接口来创建文档 `"使用 UART 实现 1-Wire 主机"`_ 中所描述的 1-Wire 定时模式。
.. _"使用 UART 实现 1-Wire 主机": https://www.analog.com/en/technical-articles/using-a-uart-to-implement-a-1wire-bus-master.html

简而言之，UART 外设必须支持全双工并以开漏模式运行。定时模式由特定的波特率和发送字节组合生成，这些组合对应于 1-Wire 读取位、写入位或复位脉冲。例如，1-Wire 复位和存在检测的定时模式使用波特率 9600（即每比特 104.2 微秒）。通过 UART 发送字节 0xf0（从最低有效位开始，起始位为低电平）将 1-Wire 的复位低时间设置为 521 微秒。如果存在 1-Wire 设备，它会拉低线路从而改变接收到的字节，驱动程序利用这一点来评估 1-Wire 操作的结果。
对于 1-Wire 读取位或写入位操作，使用波特率 115200（即每比特 8.7 微秒）。发送字节 0x80 用于执行 Write-0 操作（低电平时间为 69.6 微秒），而字节 0xff 用于 Read-0、Read-1 和 Write-1 操作（低电平时间为 8.7 微秒）。
默认情况下，复位和存在检测的波特率为 9600，1-Wire 读取或写入操作的波特率为 115200。如果实际波特率与请求的不同，则调整发送的字节以生成 1-Wire 定时模式。

---

使用方法
---

在设备树中指定 UART 1-Wire 总线，方法是在串行节点（例如 uart0）下添加单个子节点 onewire。例如：
::

  @uart0 {
    ..
    onewire {
      compatible = "w1-uart";
    };
  };
