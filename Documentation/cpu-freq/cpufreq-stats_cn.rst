### SPDX 许可证标识符: GPL-2.0

==========================================
sysfs CPUFreq 统计信息的一般描述
==========================================

用户信息


作者: Venkatesh Pallipadi <venkatesh.pallipadi@intel.com>

.. 目录

   1. 简介
   2. 提供的统计信息（附带示例）
   3. 配置 cpufreq-stats


1. 简介
===============

cpufreq-stats 是一个为每个 CPU 提供 CPU 频率统计信息的驱动程序。
这些统计信息在 /sysfs 中作为一组只读接口提供。当配置了这个接口时，它会以独立目录的形式出现在每个 CPU 的 /sysfs 的 cpufreq 下（<sysfs 根>/devices/system/cpu/cpuX/cpufreq/stats/）。
各种统计信息将形成该目录下的只读文件。
此驱动程序设计为独立于可能正在您的 CPU 上运行的任何特定 cpufreq_driver。因此，它可以与任何 cpufreq_driver 一起工作。

2. 提供的统计信息（附带示例）
=====================================

cpufreq stats 提供以下统计信息（如下详细解释）：
-  time_in_state
-  total_trans
-  trans_table

所有统计信息都是从统计驱动程序被插入的时间（或统计信息重置的时间）到特定统计信息被读取的时间。显然，在统计驱动程序插入之前，该驱动程序不会有关于频率转换的任何信息。
::

    <mysystem>:/sys/devices/system/cpu/cpu0/cpufreq/stats # ls -l
    总计 0
    drwxr-xr-x  2 root root    0 2021-05-14 16:06
    drwxr-xr-x  3 root root    0 2021-05-14 15:58 .
    --w-------  1 root root 4096 2021-05-14 16:06 reset
    -r--r--r--  1 root root 4096 2021-05-14 16:06 time_in_state
    -r--r--r--  1 root root 4096 2021-05-14 16:06 total_trans
    -r--r--r--  1 root root 4096 2021-05-14 16:06 trans_table

- **reset**

这是一个只写属性，可用于重置统计计数器。这有助于在无需重新启动的情况下评估系统在不同管理器下的行为。
- **time_in_state**

这给出了 CPU 在其支持的各个频率上花费的时间。输出中的每一行包含 "<频率> <时间>" 对，表示此 CPU 在 <频率> 上花费了 <时间> 用户时间单位。输出中每种支持的频率都有一行。这里的用户时间单位是 10 毫秒（类似于 /proc 中导出的其他时间）。
### `time_in_state` 的内容

```
<mysystem>:/sys/devices/system/cpu/cpu0/cpufreq/stats # cat time_in_state
3600000 2089
3400000 136
3200000 34
3000000 67
2800000 172488
```

- **total_trans**

这个值给出了该 CPU 上的总频率转换次数。`cat` 命令的输出将包含一个计数，即总的频率转换次数：
```
<mysystem>:/sys/devices/system/cpu/cpu0/cpufreq/stats # cat total_trans
20
```

- **trans_table**

这将提供关于所有 CPU 频率转换的详细信息。`cat` 命令的输出是一个二维矩阵，其中条目 `<i,j>`（第 i 行，第 j 列）表示从 `Freq_i` 到 `Freq_j` 的转换次数。`Freq_i` 行和 `Freq_j` 列遵循驱动程序最初向 cpufreq 核心提供的频率表中的排序顺序（升序或降序），因此可以是排序或未排序的。这里的输出还包含了每行和每列的实际频率值以提高可读性。
如果转换表的大小大于 `PAGE_SIZE`，读取它将返回 `-EFBIG` 错误：
```
<mysystem>:/sys/devices/system/cpu/cpu0/cpufreq/stats # cat trans_table
From  :    To
	    :   3600000   3400000   3200000   3000000   2800000
3600000:         0         5         0         0         0
3400000:         4         0         2         0         0
3200000:         0         1         0         2         0
3000000:         0         0         1         0         3
2800000:         0         0         0         2         0
```

### 配置 cpufreq-stats

要配置内核中的 cpufreq-stats：

```
配置主菜单
    功耗管理选项 (ACPI, APM) ---
        CPU 频率缩放 ---
            [√] CPU 频率缩放
            [√]   CPU 频率转换统计
```

要配置 cpufreq-stats，“CPU 频率缩放” (`CONFIG_CPU_FREQ`) 应该被启用。
“CPU 频率转换统计” (`CONFIG_CPU_FREQ_STAT`) 提供了包括 `time_in_state`、`total_trans` 和 `trans_table` 在内的统计数据。
一旦启用此选项，并且你的 CPU 支持 cpufreq，你将能够在 `/sysfs` 中看到 CPU 频率统计数据。
