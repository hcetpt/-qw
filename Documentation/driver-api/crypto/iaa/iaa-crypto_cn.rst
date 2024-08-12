SPDX 许可证标识符: GPL-2.0

==============================
IAA 压缩加速器加密驱动程序
==============================

汤姆·扎努西 <tom.zanussi@linux.intel.com>

IAA 加密驱动程序支持与 RFC 1951 中描述的 DEFLATE 压缩标准兼容的压缩/解压缩。该模块导出的压缩/解压缩算法即为此标准。IAA 硬件规范可在以下位置找到：

  https://cdrdv2.intel.com/v1/dl/getContent/721858

iaa_crypto 驱动程序被设计为在如 zswap 这样的高级压缩设备之下的一个层级工作。
用户可以通过指定受支持的 IAA 压缩算法之一来选择 IAA 的压缩/解压缩加速功能，这些算法允许用户选择压缩算法。例如，zswap 设备可以选择 IAA 的 'fixed' 模式，即通过选择 'deflate-iaa' 加密压缩算法实现：

  # echo deflate-iaa > /sys/module/zswap/parameters/compressor

这将告诉 zswap 使用 IAA 的 'fixed' 压缩模式进行所有压缩和解压缩操作。
目前仅有一种压缩模式可用，即 'fixed' 模式。
'fixed' 压缩模式实现了 RFC 1951 规定的压缩方案，并赋予了 'deflate-iaa' 的加密算法名称。（由于 IAA 硬件具有 4K 历史窗口限制，只有 ≤4K 的缓冲区或使用 ≤4K 历史窗口压缩的缓冲区才符合 deflate 规范中允许的最高 32K 窗口大小。正因为此限制，IAA 的固定模式 deflate 算法被赋予了一个独立的算法名称，而不是简单的 'deflate'。）

配置选项和其他设置
==================

IAA 加密驱动程序可通过 menuconfig 在以下路径中找到：

  加密 API -> 硬件加密设备 -> 支持 Intel® IAA 压缩加速器

在配置文件中的选项为 CONFIG_CRYPTO_DEV_IAA_CRYPTO。

IAA 加密驱动程序还支持统计信息，这些统计信息也可通过 menuconfig 在以下路径中找到：

  加密 API -> 硬件加密设备 -> 支持 Intel® IAA 压缩 -> 启用 Intel® IAA 压缩加速器统计信息

在配置文件中的选项为 CONFIG_CRYPTO_DEV_IAA_CRYPTO_STATS。

以下配置选项也应被启用：

  CONFIG_IRQ_REMAP=y
  CONFIG_INTEL_IOMMU=y
  CONFIG_INTEL_IOMMU_SVM=y
  CONFIG_PCI_ATS=y
  CONFIG_PCI_PRI=y
  CONFIG_PCI_PASID=y
  CONFIG_INTEL_IDXD=m
  CONFIG_INTEL_IDXD_SVM=y

IAA 是首批可以与 Intel IOMMU 协同工作的 Intel 加速器 IP 之一。存在多种测试模式。基于 IOMMU 配置，有 3 种模式：

  - 可扩展模式
  - 传统模式
  - 无 IOMMU 模式


可扩展模式
-----------

可扩展模式支持共享虚拟内存（SVM 或 SVA）。当在内核引导命令行中使用：

  intel_iommu=on,sm_on

并确保在 BIOS 中启用了 VT-d 时进入此模式。
在可扩展模式下，既提供共享又提供专用的工作队列以供使用。
对于可扩展模式，应启用以下BIOS设置：

  * 插槽配置 > IIO 配置 > Intel VT for Directed I/O (VT-d) > Intel VT for Directed I/O
  * 插槽配置 > IIO 配置 > PCIe ENQCMD > ENQCMDS

传统模式
--------

当使用内核启动命令行时进入传统模式：

  * intel_iommu=off

或者在BIOS中未开启VT-d。
如果你已经启动到Linux并且不确定VT-d是否已开启，请执行 "dmesg | grep -i dmar"。如果你没有看到列出的多个DMAR设备，则很可能VT-d未开启。
在传统模式下，仅可使用专用工作队列。
无IOMMU模式
------------

通过使用内核启动命令行进入无IOMMU模式：

  * iommu=off

在无IOMMU模式下，仅可使用专用工作队列。

使用方法
=====

accel-config
------------

加载iaa_crypto驱动程序后，会自动创建一个默认配置并启用它，并分配默认的驱动程序属性。
如果需要不同的配置或一组驱动程序属性，用户必须首先禁用IAA设备和工作队列，重置配置，然后通过卸载并重新插入iaa_crypto模块来重新向加密子系统注册deflate-iaa算法。
下面“使用案例”部分中的 :ref:`iaa_disable_script` 可用于禁用默认配置。
有关默认配置的详细信息，请参阅下面的 :ref:`iaa_default_config`。
然而，由于加速器设备的复杂性和可配置性，用户很可能希望手动配置设备并启用所需的设备和工作队列。
用户空间工具 `accel-config` 用于帮助完成这些配置。强烈推荐使用 `accel-config` 来配置设备或加载之前保存的配置。虽然也可以直接通过 sysfs 控制设备，但请注意这仅适用于完全清楚自己在做什么的情况。以下各节将不涵盖 sysfs 接口，而是假设您将使用 `accel-config`。如果您对 sysfs 接口感兴趣，可以参考附录中的 :ref:`iaa_sysfs_config` 部分了解详细信息。`accel-config` 工具及其构建说明可以在以下位置找到：

  https://github.com/intel/idxd-config/#readme

典型用法
---------

为了让 iaa_crypto 模块真正代表设施执行压缩/解压缩工作，需要绑定一个或多个 IAA 工作队列到 iaa_crypto 驱动程序。例如，下面是配置一个 IAA 工作队列并将其绑定到 iaa_crypto 驱动程序的例子（注意：设备名称被指定为 'iax' 而不是 'iaa' — 这是因为上游仍然使用旧的 'iax' 设备命名）：

```shell
# 配置 wq1.0

accel-config config-wq --group-id=0 --mode=dedicated --type=kernel --priority=10 --name="iaa_crypto" --driver-name="crypto" iax1/wq1.0

accel-config config-engine iax1/engine1.0 --group-id=0

# 启用 IAA 设备 iax1

accel-config enable-device iax1

# 在 IAX 设备 iax1 上启用 wq1.0

accel-config enable-wq iax1/wq1.0
```

每当新的工作队列与 iaa_crypto 驱动程序绑定或解除绑定时，可用的工作队列会进行“再平衡”，以便来自特定 CPU 的工作提交给最合适的可用工作队列。目前的最佳做法是为每个 IAA 设备配置并绑定至少一个工作队列，但只要系统中有至少一个工作队列被配置并与任何 IAA 设备绑定，iaa_crypto 驱动程序就能工作，尽管可能不会那么高效。
在成功将第一个 IAA 工作队列绑定到 iaa_crypto 驱动程序之后，IAA 加密算法便处于运行状态，并且压缩和解压缩操作完全启用。
同样，在最后一个 IAA 工作队列从 iaa_crypto 驱动程序解除绑定后，IAA 加密算法不再运行，压缩和解压缩操作被禁用。
因此，只有当有一个或多个工作队列绑定到 iaa_crypto 驱动程序时，IAA 加密算法及 IAA 硬件才可用。
当没有任何 IAA 工作队列绑定到驱动程序时，可以通过卸载模块来取消注册 IAA 加密算法。

驱动属性
---------

有几个用户可配置的驱动属性可用于配置不同的运行模式。它们列于下文，并附有默认值。要设置这些属性中的任何一个，请将相应的值写入位于 `/sys/bus/dsa/drivers/crypto/` 下的属性文件中。
当 IAA 算法注册时，每个算法的 `crypto_ctx` 中都会捕获属性设置，并用于所有使用该算法的压缩和解压缩操作。
可用的属性包括：

  - `verify_compress`

    切换压缩验证功能。如果设置，每次压缩都会内部解压缩并验证内容，若不成功则返回错误码。此选项可通过 0/1 切换：

      ```shell
      echo 0 > /sys/bus/dsa/drivers/crypto/verify_compress
      ```

    默认设置为 '1' — 验证所有压缩操作。
### 同步模式

选择用于等待每次压缩和解压缩操作完成的模式。
`iaa_crypto` 实现的加密异步接口提供了一个满足接口要求但以同步方式进行的操作——它填写并提交 IDXD 描述符，然后循环等待其完成再返回。这目前不是问题，因为所有现有调用者（例如 zswap）都已通过同步包装器封装了任何异步子程序。

然而，`iaa_crypto` 驱动确实为能够利用它的调用者提供了真正的异步支持。在这种模式下，它填写并提交 IDXD 描述符，然后立即返回 `-EINPROGRESS`。调用者可以自行轮询检查完成情况，但这需要调用者中的特定代码实现，当前内核中尚无此类实现；或者休眠并等待完成信号的中断。后一种模式通过同步包装器被当前内核用户如 zswap 所支持。尽管此模式得到支持，但它比前面提到的在 `iaa_crypto` 驱动内部进行轮询的同步模式要慢得多。

可以通过向 `sync_mode` 属性写入 `'async_irq'` 来启用此模式：

```shell
echo async_irq > /sys/bus/dsa/drivers/crypto/sync_mode
```

不使用中断的异步模式（调用者必须自己轮询）可以通过写入 `'async'` 来启用：

```shell
echo async > /sys/bus/dsa/drivers/crypto/sync_mode
```

在 `iaa_crypto` 驱动内部进行轮询的模式可以通过写入 `'sync'` 来启用：

```shell
echo sync > /sys/bus/dsa/drivers/crypto/sync_mode
```

默认模式是 `'sync'`。

### IAA 默认配置

当加载 `iaa_crypto` 驱动时，每个 IAA 设备都有一个为其配置的工作队列，具有以下属性：

- 模式："专用"
- 阈值：0
- 大小：WQCAP 中的总工作队列大小
- 优先级：10
- 类型：IDXD_WQT_KERNEL
- 组：0
- 名称："iaa_crypto"
- 驱动名称："crypto"

设备和工作队列也被启用，因此驱动可以在无需额外配置的情况下直接使用。

加载驱动时默认生效的驱动属性有：

- `sync_mode`："sync"
- `verify_compress`：1

为了更改设备/工作队列或驱动属性，首先必须禁用启用的设备和工作队列。为了使新配置应用于 deflate-iaa 加密算法，需要通过卸载和重新插入 `iaa_crypto` 模块来重新注册该算法。下面“使用案例”部分中的 :ref:`iaa_disable_script` 可用于禁用默认配置。

### 统计信息

如果启用了可选的 debugfs 统计信息支持，则 IAA 加密驱动将生成统计信息，这些统计信息可以在 debugfs 中访问：

```shell
# ls -al /sys/kernel/debug/iaa-crypto/
total 0
drwxr-xr-x  2 root root 0 Mar  3 07:55
drwx------ 53 root root 0 Mar  3 07:55 .
-rw-r--r--  1 root root 0 Mar  3 07:55 global_stats
-rw-r--r--  1 root root 0 Mar  3 07:55 stats_reset
-rw-r--r--  1 root root 0 Mar  3 07:55 wq_stats
```

`global_stats` 文件显示自驱动加载或重置以来收集的一组全局统计信息：

```shell
# cat global_stats
global stats:
  total_comp_calls: 4300
  total_decomp_calls: 4164
  total_sw_decomp_calls: 0
  total_comp_bytes_out: 5993989
  total_decomp_bytes_in: 5993989
  total_completion_einval_errors: 0
  total_completion_timeout_errors: 0
  total_completion_comp_buf_overflow_errors: 136
```

`wq_stats` 文件显示每个 IAA 设备和工作队列的统计信息，以及一些全局统计信息：

```shell
# cat wq_stats
iaa device:
  id: 1
  n_wqs: 1
  comp_calls: 0
  comp_bytes: 0
  decomp_calls: 0
  decomp_bytes: 0
  wqs:
    name: iaa_crypto
    comp_calls: 0
    comp_bytes: 0
    decomp_calls: 0
    decomp_bytes: 0

iaa device:
  id: 3
  n_wqs: 1
  comp_calls: 0
  comp_bytes: 0
  decomp_calls: 0
  decomp_bytes: 0
  wqs:
    name: iaa_crypto
    comp_calls: 0
    comp_bytes: 0
    decomp_calls: 0
    decomp_bytes: 0

iaa device:
  id: 5
  n_wqs: 1
  comp_calls: 1360
  comp_bytes: 1999776
  decomp_calls: 0
  decomp_bytes: 0
  wqs:
    name: iaa_crypto
    comp_calls: 1360
    comp_bytes: 1999776
    decomp_calls: 0
    decomp_bytes: 0

iaa device:
  id: 7
  n_wqs: 1
  comp_calls: 2940
  comp_bytes: 3994213
  decomp_calls: 4164
  decomp_bytes: 5993989
  wqs:
    name: iaa_crypto
    comp_calls: 2940
    comp_bytes: 3994213
    decomp_calls: 4164
    decomp_bytes: 5993989
...
```

向 `stats_reset` 写入内容会重置所有统计信息，包括每个设备和每个工作队列的统计信息：

```shell
# echo 1 > stats_reset
# cat wq_stats
global stats:
  total_comp_calls: 0
  total_decomp_calls: 0
  total_comp_bytes_out: 0
  total_decomp_bytes_in: 0
  total_completion_einval_errors: 0
  total_completion_timeout_errors: 0
  total_completion_comp_buf_overflow_errors: 0
...
```
用例
=========

简单的 zswap 测试
-----------------

在这个示例中，内核应该按照上述专用模式选项进行配置，并且需要启用 zswap ：

  CONFIG_ZSWAP=y

这是一个简单的测试，使用 iaa_compress 作为交换（zswap）设备的压缩器。它设置 zswap 设备，然后使用下面列出的 memory_memadvise 程序强制交换出和交换入指定数量的页面，演示压缩和解压缩的过程。zswap 测试期望系统上的每个 IAA 设备的工作队列被正确配置为内核工作队列，具有名为 "crypto" 的工作队列驱动程序名。

第一步是确保加载了 iaa_crypto 模块：

  modprobe iaa_crypto

如果 IAA 设备和工作队列之前没有被禁用并重新配置，则默认配置应该已经到位，不需要进一步的 IAA 配置。请参阅下面的 :ref:`iaa_default_config` 以了解默认配置的详细信息。

如果默认配置已经就位，你应该能看到 iaa 设备和 wq0s 被启用：

  # cat /sys/bus/dsa/devices/iax1/state
  enabled
  # cat /sys/bus/dsa/devices/iax1/wq1.0/state
  enabled

为了证明以下步骤如预期那样工作，可以使用这些命令来启用调试输出：

  # echo -n 'module iaa_crypto +p' > /sys/kernel/debug/dynamic_debug/control
  # echo -n 'module idxd +p' > /sys/kernel/debug/dynamic_debug/control

使用以下命令来启用 zswap：

  # echo 0 > /sys/module/zswap/parameters/enabled
  # echo 50 > /sys/module/zswap/parameters/max_pool_percent
  # echo deflate-iaa > /sys/module/zswap/parameters/compressor
  # echo zsmalloc > /sys/module/zswap/parameters/zpool
  # echo 1 > /sys/module/zswap/parameters/enabled
  # echo 100 > /proc/sys/vm/swappiness
  # echo never > /sys/kernel/mm/transparent_hugepage/enabled
  # echo 1 > /proc/sys/vm/overcommit_memory

现在你可以运行你想要衡量的 zswap 工作负载。例如，使用下面的 memory_memadvise 代码，以下命令将会交换出和交换入 100 个页面：

  ./memory_madvise 100

  分配 100 个页面用于交换出/入
  交换出 100 个页面
  交换入 100 个页面
  交换出和交换入 100 个页面

在 dmesg 输出中，你应该看到类似以下内容：

  [  404.202972] idxd 0000:e7:02.0: iaa_comp_acompress: dma_map_sg, src_addr 223925c000, nr_sgs 1, req->src 00000000ee7cb5e6, req->slen 4096, sg_dma_len(sg) 4096
  [  404.202973] idxd 0000:e7:02.0: iaa_comp_acompress: dma_map_sg, dst_addr 21dadf8000, nr_sgs 1, req->dst 000000008d6acea8, req->dlen 4096, sg_dma_len(sg) 8192
  [  404.202975] idxd 0000:e7:02.0: iaa_compress: desc->src1_addr 223925c000, desc->src1_size 4096, desc->dst_addr 21dadf8000, desc->max_dst_size 4096, desc->src2_addr 2203543000, desc->src2_size 1568
  [  404.202981] idxd 0000:e7:02.0: iaa_compress_verify: (verify) desc->src1_addr 21dadf8000, desc->src1_size 228, desc->dst_addr 223925c000, desc->max_dst_size 4096, desc->src2_addr 0, desc->src2_size 0
  ...

现在基本功能已经被演示，可以擦除默认配置并替换为不同的配置。要做到这一点，首先禁用 zswap：

  # echo lzo > /sys/module/zswap/parameters/compressor
  # swapoff -a
  # echo 0 > /sys/module/zswap/parameters/accept_threshold_percent
  # echo 0 > /sys/module/zswap/parameters/max_pool_percent
  # echo 0 > /sys/module/zswap/parameters/enabled
  # echo 0 > /sys/module/zswap/parameters/enabled

然后运行下面“用例”部分中的 :ref:`iaa_disable_script` 来禁用默认配置。
最后重新开启交换：

  # swapon -a

完成所有这些之后，现在可以根据需要重新配置和启用 IAA 设备进行进一步的测试。下面是一个示例。

zswap 测试期望系统上的每个 IAA 设备的工作队列被正确配置为内核工作队列，具有名为 "crypto" 的工作队列驱动程序名。

下面的脚本自动完成了这一点：

  #!/bin/bash

  echo "IAA 设备："
  lspci -d:0cfe
  echo "# IAA 设备："
  lspci -d:0cfe | wc -l

  #
  # 计数 iaa 实例
  #
  iaa_dev_id="0cfe"
  num_iaa=$(lspci -d:${iaa_dev_id} | wc -l)
  echo "找到 ${num_iaa} 个 IAA 实例"

  #
  # 禁用 iaa 工作队列和设备
  #
  echo "禁用 IAA"

  for ((i = 1; i < ${num_iaa} * 2; i += 2)); do
      echo 禁用 wq iax${i}/wq${i}.0
      accel-config disable-wq iax${i}/wq${i}.0
      echo 禁用 iaa iax${i}
      accel-config disable-device iax${i}
  done

  echo "结束禁用 IAA"

  echo "重新加载 iaa_crypto 模块"

  rmmod iaa_crypto
  modprobe iaa_crypto

  echo "结束重新加载 iaa_crypto 模块"

  #
  # 配置 iaa 工作队列和设备
  #
  echo "配置 IAA"
  for ((i = 1; i < ${num_iaa} * 2; i += 2)); do
      accel-config config-wq --group-id=0 --mode=dedicated --wq-size=128 --priority=10 --type=kernel --name="iaa_crypto" --driver-name="crypto" iax${i}/wq${i}.0
      accel-config config-engine iax${i}/engine${i}.0 --group-id=0
  done

  echo "结束配置 IAA"

  #
  # 启用 iaa 工作队列和设备
  #
  echo "启用 IAA"

  for ((i = 1; i < ${num_iaa} * 2; i += 2)); do
      echo 启用 iaa iax${i}
      accel-config enable-device iax${i}
      echo 启用 wq iax${i}/wq${i}.0
      accel-config enable-wq iax${i}/wq${i}.0
  done

  echo "结束启用 IAA"

当工作队列绑定到 iaa_crypto 驱动时，如果你启用了调试输出（echo -n 'module iaa_crypto +p' > /sys/kernel/debug/dynamic_debug/control），你应该能在 dmesg 输出中看到类似以下内容：

  [   60.752344] idxd 0000:f6:02.0: add_iaa_wq: 将 wq 000000004068d14d 添加到 iaa 00000000c9585ba2, n_wq 1
  [   60.752346] iaa_crypto: rebalance_wq_table: nr_nodes=2, nr_cpus 160, nr_iaa 8, cpus_per_iaa 20
  [   60.752347] iaa_crypto: rebalance_wq_table: iaa=0
  [   60.752349] idxd 0000:6a:02.0: request_iaa_wq: 从 iaa_device 0000000042d7bc52 (0) 获取 wq
  [   60.752350] idxd 0000:6a:02.0: request_iaa_wq: 从 iaa 设备 0000000042d7bc52 (0) 返回未使用的 wq 00000000c8bb4452 (0)
  [   60.752352] iaa_crypto: rebalance_wq_table: 为 cpu=0, node=0 分配 wq 00000000c8bb4452
  [   60.752354] iaa_crypto: rebalance_wq_table: iaa=0
  [   60.752355] idxd 0000:6a:02.0: request_iaa_wq: 从 iaa_device 0000000042d7bc52 (0) 获取 wq
  [   60.752356] idxd 0000:6a:02.0: request_iaa_wq: 从 iaa 设备 0000000042d7bc52 (0) 返回未使用的 wq 00000000c8bb4452 (0)
  [   60.752358] iaa_crypto: rebalance_wq_table: 为 cpu=1, node=0 分配 wq 00000000c8bb4452
  [   60.752359] iaa_crypto: rebalance_wq_table: iaa=0
  [   60.752360] idxd 0000:6a:02.0: request_iaa_wq: 从 iaa_device 0000000042d7bc52 (0) 获取 wq
  [   60.752361] idxd 0000:6a:02.0: request_iaa_wq: 从 iaa 设备 0000000042d7bc52 (0) 返回未使用的 wq 00000000c8bb4452 (0)
  [   60.752362] iaa_crypto: rebalance_wq_table: 为 cpu=2, node=0 分配 wq 00000000c8bb4452
  [   60.752364] iaa_crypto: rebalance_wq_table: iaa=0
一旦工作队列和设备被启用，IAA 加密算法也会被启用并变得可用。当 IAA 加密算法成功启用后，你应该能在 dmesg 输出中看到以下内容：

  [   64.893759] iaa_crypto: iaa_crypto_enable: iaa_crypto 现已启用

现在运行以下特定于 zswap 的设置命令，让 zswap 使用“固定”压缩模式：

  echo 0 > /sys/module/zswap/parameters/enabled
  echo 50 > /sys/module/zswap/parameters/max_pool_percent
  echo deflate-iaa > /sys/module/zswap/parameters/compressor
  echo zsmalloc > /sys/module/zswap/parameters/zpool
  echo 1 > /sys/module/zswap/parameters/enabled

  echo 100 > /proc/sys/vm/swappiness
  echo never > /sys/kernel/mm/transparent_hugepage/enabled
  echo 1 > /proc/sys/vm/overcommit_memory

最后，你现在可以运行想要测量的 zswap 工作负载了。例如，使用下面的代码，以下命令将会交换入和交换出 100 页：

  ./memory_madvise 100

  分配 100 页以进行交换
  正在交换出 100 页
  正在交换入 100 页
  已交换出和交换入 100 页

如果你启用了调试输出（通过 `echo -n 'module iaa_crypto +p' > /sys/kernel/debug/dynamic_debug/control`），你应该能在 dmesg 输出中看到类似以下的内容：

  [  404.202972] idxd 0000:e7:02.0: iaa_comp_acompress: dma_map_sg, src_addr 223925c000, nr_sgs 1, req->src 00000000ee7cb5e6, req->slen 4096, sg_dma_len(sg) 4096
  [  404.202973] idxd 0000:e7:02.0: iaa_comp_acompress: dma_map_sg, dst_addr 21dadf8000, nr_sgs 1, req->dst 000000008d6acea8, req->dlen 4096, sg_dma_len(sg) 8192
  [  404.202975] idxd 0000:e7:02.0: iaa_compress: desc->src1_addr 223925c000, desc->src1_size 4096, desc->dst_addr 21dadf8000, desc->max_dst_size 4096, desc->src2_addr 2203543000, desc->src2_size 1568
  [  404.202981] idxd 0000:e7:02.0: iaa_compress_verify: (verify) desc->src1_addr 21dadf8000, desc->src1_size 228, desc->dst_addr 223925c000, desc->max_dst_size 4096, desc->src2_addr 0, desc->src2_size 0
  [  409.203227] idxd 0000:e7:02.0: iaa_comp_adecompress: dma_map_sg, src_addr 21ddd8b100, nr_sgs 1, req->src 0000000084adab64, req->slen 228, sg_dma_len(sg) 228
  [  409.203235] idxd 0000:e7:02.0: iaa_comp_adecompress: dma_map_sg, dst_addr 21ee3dc000, nr_sgs 1, req->dst 000000004e2990d0, req->dlen 4096, sg_dma_len(sg) 4096
  [  409.203239] idxd 0000:e7:02.0: iaa_decompress: desc->src1_addr 21ddd8b100, desc->src1_size 228, desc->dst_addr 21ee3dc000, desc->max_dst_size 4096, desc->src2_addr 0, desc->src2_size 0
  [  409.203254] idxd 0000:e7:02.0: iaa_comp_adecompress: dma_map_sg, src_addr 21ddd8b100, nr_sgs 1, req->src 0000000084adab64, req->slen 228, sg_dma_len(sg) 228
  [  409.203256] idxd 0000:e7:02.0: iaa_comp_adecompress: dma_map_sg, dst_addr 21f1551000, nr_sgs 1, req->dst 000000004e2990d0, req->dlen 4096, sg_dma_len(sg) 4096
  [  409.203257] idxd 0000:e7:02.0: iaa_decompress: desc->src1_addr 21ddd8b100, desc->src1_size 228, desc->dst_addr 21f1551000, desc->max_dst_size 4096, desc->src2_addr 0, desc->src2_size 0

为了注销 IAA 加密算法，并使用不同的参数注册新的算法，任何当前算法的用户都应停止，并且需要禁用 IAA 工作队列和设备。在 zswap 的情况下，移除 IAA 加密算法作为压缩器，并关闭交换（以移除所有对 iaa_crypto 的引用）：

  echo lzo > /sys/module/zswap/parameters/compressor
  swapoff -a

  echo 0 > /sys/module/zswap/parameters/accept_threshold_percent
  echo 0 > /sys/module/zswap/parameters/max_pool_percent
  echo 0 > /sys/module/zswap/parameters/enabled

一旦 zswap 被禁用且不再使用 iaa_crypto，就可以禁用 IAA 工作队列和设备。
.. _iaa_disable_script:

IAA 禁用脚本
--------------

下面的脚本自动执行这些操作：

  #!/bin/bash

  echo "IAA 设备:"
  lspci -d:0cfe
  echo "# IAA 设备数量:"
  lspci -d:0cfe | wc -l

  #
  # 统计 IAA 实例数量
  #
  iaa_dev_id="0cfe"
  num_iaa=$(lspci -d:${iaa_dev_id} | wc -l)
  echo "找到 ${num_iaa} 个 IAA 实例"

  #
  # 禁用 IAA 工作队列和设备
  #
  echo "禁用 IAA"

  for ((i = 1; i < ${num_iaa} * 2; i += 2)); do
      echo 禁用工作队列 iax${i}/wq${i}.0
      accel-config disable-wq iax${i}/wq${i}.0
      echo 禁用 IAA iax${i}
      accel-config disable-device iax${i}
  done

  echo "结束禁用 IAA"

最后，在这一点上，可以移除 iaa_crypto 模块，这将注销当前的 IAA 加密算法。

memory_madvise.c (gcc -o memory_madvise memory_madvise.c)：

  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include <unistd.h>
  #include <sys/mman.h>
  #include <linux/mman.h>

  #ifndef MADV_PAGEOUT
  #define MADV_PAGEOUT    21      /* 强制页面立即换出 */
  #endif

  #define PG_SZ           4096

  int main(int argc, char **argv)
  {
        int i, nr_pages = 1;
        int64_t *dump_ptr;
        char *addr, *a;
        int loop = 1;

        if (argc > 1)
                nr_pages = atoi(argv[1]);

        printf("分配 %d 页以进行交换\n", nr_pages);

        /* 分配页面 */
        addr = mmap(NULL, nr_pages * PG_SZ, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
        *addr = 1;

        /* 将页面中的数据初始化为全 '*' 字符 */
        memset(addr, '*', nr_pages * PG_SZ);

        printf("正在交换出 %d 页\n", nr_pages);

        /* 告诉内核将其换出 */
        madvise(addr, nr_pages * PG_SZ, MADV_PAGEOUT);

        while (loop > 0) {
                /* 等待换出完成 */
                sleep(5);

                a = addr;

                printf("正在交换入 %d 页\n", nr_pages);

                /* 访问页面 ... 这将会再次将其换入 */
                for (i = 0; i < nr_pages; i++) {
                        if (a[0] != '*') {
                                printf("从解压得到的数据错误!!!!!\n");

                                dump_ptr = (int64_t *)a;
                                for (int j = 0; j < 100; j++) {
                                        printf("  第 %d 页数据: %#llx\n", i, *dump_ptr);
                                        dump_ptr++;
                                }
                        }

                        a += PG_SZ;
                }

                loop --;
        }

        printf("已交换出和交换入 %d 页\n", nr_pages);
  }

附录
=====

.. _iaa_sysfs_config:

IAA sysfs 配置接口
----------------------

下面是 IAA sysfs 接口的描述，如主文档中所述，该接口仅应在确切知道你正在做什么的情况下使用。即使如此，也没有必要直接使用它，因为 accel-config 可以做 sysfs 接口能做的所有事情，实际上 accel-config 在底层就是基于它的。
'IAA 配置路径' 是 /sys/bus/dsa/devices，包含表示每个 IAA 设备、工作队列、引擎和组的子目录。注意在 sysfs 接口中，IAA 设备实际上是使用 iax 命名的，例如 iax1, iax3 等。（注意 IAA 设备是奇数编号的设备；偶数编号的设备是 DSA 设备，对于 IAA 可以忽略）
'IAA 设备绑定路径' 是 /sys/bus/dsa/drivers/idxd/bind，是用于启用 IAA 设备的文件
'IAA 工作队列绑定路径' 是 /sys/bus/dsa/drivers/crypto/bind，是用于启用 IAA 工作队列的文件
同样，/sys/bus/dsa/drivers/idxd/unbind 和 /sys/bus/dsa/drivers/crypto/unbind 用于禁用 IAA 设备和工作队列
设置 IAA 设备和工作队列所需的基本命令序列如下：

对于每个设备：
  1) 禁用设备上的任何已启用的工作队列。例如，要禁用 IAA 设备 3 上的工作队列 0 和 1：

       # echo wq3.0 > /sys/bus/dsa/drivers/crypto/unbind
       # echo wq3.1 > /sys/bus/dsa/drivers/crypto/unbind

  2) 禁用设备。例如，要禁用 IAA 设备 3：

       # echo iax3 > /sys/bus/dsa/drivers/idxd/unbind

  3) 配置所需的工作队列。例如，要配置 IAA 设备 3 上的工作队列 3：

       # echo dedicated > /sys/bus/dsa/devices/iax3/wq3.3/mode
       # echo 128 > /sys/bus/dsa/devices/iax3/wq3.3/size
       # echo 0 > /sys/bus/dsa/devices/iax3/wq3.3/group_id
       # echo 10 > /sys/bus/dsa/devices/iax3/wq3.3/priority
       # echo "kernel" > /sys/bus/dsa/devices/iax3/wq3.3/type
       # echo "iaa_crypto" > /sys/bus/dsa/devices/iax3/wq3.3/name
       # echo "crypto" > /sys/bus/dsa/devices/iax3/wq3.3/driver_name

  4) 启用设备。例如，要启用 IAA 设备 3：

       # echo iax3 > /sys/bus/dsa/drivers/idxd/bind

  5) 启用设备上的所需工作队列。例如，要启用 IAA 设备 3 上的工作队列 0 和 1：

       # echo wq3.0 > /sys/bus/dsa/drivers/crypto/bind
       # echo wq3.1 > /sys/bus/dsa/drivers/crypto/bind
