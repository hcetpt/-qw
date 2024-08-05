SPDX 许可证标识符: GPL-2.0

============
x86 架构拓扑
============

本文档阐述并澄清了内核中 x86 拓扑建模和表示的主要方面。在对相关代码进行更改时，请相应更新或修改。
架构无关的拓扑定义位于 `Documentation/admin-guide/cputopology.rst`。本文件记录了 x86 特有的差异和特殊性，这些可能不适用于通用定义。因此，了解 x86 上的 Linux 拓扑结构的方法是从通用定义开始，并同时参考本文件以了解 x86 的特定内容。
需要强调的是，代码应当使用通用函数 —— 本文件仅用于记录 x86 拓扑内部运作方式。
由 Thomas Gleixner `<tglx@linutronix.de>` 和 Borislav Petkov `<bp@alien8.de>` 开始编写。

拓扑设施的主要目标是为需要了解、查询或使用与线程、核心、封装等相关的系统结构的代码提供适当的接口。
内核并不关心物理插槽的概念，因为插槽对于软件来说没有意义，它是一个机电部件。过去一个插槽总是包含一个封装（见下文），但随着多芯片模块（MCM）的出现，一个插槽可以容纳多个封装。因此，尽管代码中可能存在对插槽的引用，但这些引用具有历史性质，应该被清理掉。
系统的拓扑结构用以下单位描述：

- 封装（packages）
- 核心（cores）
- 线程（threads）

封装
=====
封装包含一定数量的核心及共享资源，例如 DRAM 控制器、共享缓存等。
现代系统也可能使用“晶片”（Die）来指代封装。
AMD 对封装的命名术语是“节点”（Node）。
内核中的封装相关的拓扑信息包括：

  - `topology_num_threads_per_package()`

    封装中的线程数
### 核心拓扑结构相关函数与属性说明

- `topology_num_cores_per_package()`

    返回一个包（package）中的核心（core）数量。
  
- `topology_max_dies_per_package()`

    返回一个包中最大可能的晶片（die）数量。

- `cpuinfo_x86.topo.die_id:`

    晶片的物理标识符。

- `cpuinfo_x86.topo.pkg_id:`

    包的物理标识符。这些信息是通过CPUID获取，并从包内各核心的APIC标识符推断得出的。
    
    现代系统使用此值来表示插座（socket）。一个插座内部可能存在多个包。该值可能与`topo.die_id`不同。

- `cpuinfo_x86.topo.logical_pkg_id:`

    包的逻辑标识符。由于我们不信任BIOS能以一致的方式枚举包，因此引入了逻辑包标识符的概念，以便能够合理地计算出系统中最大可能的包数量，并使包以线性方式被枚举。

- `topology_max_packages()`

    系统中可能的最大包数量。对于每个包的设施来说，这有助于预分配每个包的信息。

- `cpuinfo_x86.topo.llc_id:`

    - 在Intel平台上，共享末级缓存（Last Level Cache, LLC）的CPU列表中的第一个APIC标识符。
    
    - 在AMD平台上，包含末级缓存的节点标识符或核心复合体标识符。通常，它是在系统上唯一标识LLC的一个数字。

### 核心（Core）

#### 定义

一个核心由一个或多个线程组成。无论这些线程是SMT（同时多线程）还是CMT（集群多线程）类型，这一点都不重要。

在AMD的术语中，一个CMT核心被称为“计算单元”（Compute Unit）。内核始终使用“核心”这一术语。
### 线程

线程是一个单一的调度单位。它相当于一个逻辑的 Linux CPU。
AMD 对于 CMT 线程的命名是“计算单元核心”。内核始终使用“线程”这一术语。

与线程相关的拓扑信息在内核中如下：

- `topology_core_cpumask()`：

  该 cpumask 包含属于一个线程所属包的所有在线线程。
  在 `/proc/cpuinfo` 中打印的“siblings”也表示在线线程的数量。

- `topology_sibling_cpumask()`：

  该 cpumask 包含属于一个线程所属核心的所有在线线程。

- `topology_logical_package_id()`：

  线程所属的逻辑包 ID。

- `topology_physical_package_id()`：

  线程所属的物理包 ID。

- `topology_core_id();`：

  线程所属的核心 ID。这也打印在 `/proc/cpuinfo` 的 “core_id” 中。

### 系统拓扑示例

**注：**
Linux CPU 枚举取决于 BIOS 如何枚举线程。许多 BIOS 先枚举所有线程 0，然后是所有线程 1。
这样做的“优点”在于，无论是否启用了线程，线程 0 的逻辑 Linux CPU 编号保持不变。这只是实现细节，并没有实际影响。

1) 单个包、单个核心：

```
[包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
```

2) 单个包、双核心

   a) 每个核心一个线程：

   ```
   [包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
   -> [核心 1] -> [线程 0] -> Linux CPU 1
   ```

   b) 每个核心两个线程：

   ```
   [包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
   -> [线程 1] -> Linux CPU 1
   -> [核心 1] -> [线程 0] -> Linux CPU 2
   -> [线程 1] -> Linux CPU 3
   ```

   另一种枚举方式：

   ```
   [包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
   -> [线程 1] -> Linux CPU 2
   -> [核心 1] -> [线程 0] -> Linux CPU 1
   -> [线程 1] -> Linux CPU 3
   ```

   AMD 对于 CMT 系统的命名：

   ```
   [节点 0] -> [计算单元 0] -> [计算单元核心 0] -> Linux CPU 0
   -> [计算单元核心 1] -> Linux CPU 1
   -> [计算单元 1] -> [计算单元核心 0] -> Linux CPU 2
   -> [计算单元核心 1] -> Linux CPU 3
   ```

4) 双包、双核心

   a) 每个核心一个线程：

   ```
   [包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
   -> [核心 1] -> [线程 0] -> Linux CPU 1

   [包 1] -> [核心 0] -> [线程 0] -> Linux CPU 2
   -> [核心 1] -> [线程 0] -> Linux CPU 3
   ```

   b) 每个核心两个线程：

   ```
   [包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
   -> [线程 1] -> Linux CPU 1
   -> [核心 1] -> [线程 0] -> Linux CPU 2
   -> [线程 1] -> Linux CPU 3

   [包 1] -> [核心 0] -> [线程 0] -> Linux CPU 4
   -> [线程 1] -> Linux CPU 5
   -> [核心 1] -> [线程 0] -> Linux CPU 6
   -> [线程 1] -> Linux CPU 7
   ```

   另一种枚举方式：

   ```
   [包 0] -> [核心 0] -> [线程 0] -> Linux CPU 0
   -> [线程 1] -> Linux CPU 4
   -> [核心 1] -> [线程 0] -> Linux CPU 1
   -> [线程 1] -> Linux CPU 5

   [包 1] -> [核心 0] -> [线程 0] -> Linux CPU 2
   -> [线程 1] -> Linux CPU 6
   -> [核心 1] -> [线程 0] -> Linux CPU 3
   -> [线程 1] -> Linux CPU 7
   ```

   AMD 对于 CMT 系统的命名：

   ```
   [节点 0] -> [计算单元 0] -> [计算单元核心 0] -> Linux CPU 0
   -> [计算单元核心 1] -> Linux CPU 1
   -> [计算单元 1] -> [计算单元核心 0] -> Linux CPU 2
   -> [计算单元核心 1] -> Linux CPU 3

   [节点 1] -> [计算单元 0] -> [计算单元核心 0] -> Linux CPU 4
   -> [计算单元核心 1] -> Linux CPU 5
   -> [计算单元 1] -> [计算单元核心 0] -> Linux CPU 6
   -> [计算单元核心 1] -> Linux CPU 7
   ```
