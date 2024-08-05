### SPDX 许可证标识符: GPL-2.0-or-later

==========================================
DEXCR（动态执行控制寄存器）
==========================================

概述
========

DEXCR 是在 PowerPC ISA 3.1B（Power10）中引入的一个特权专用寄存器 (SPR)，它允许每个 CPU 控制多种动态执行行为。这些行为包括推测（例如，间接分支目标预测）和启用返回导向编程 (ROP) 保护指令。硬件中的 DEXCR 通过最多 32 位（称为“方面”）来暴露执行控制。每个方面控制某种特定的行为，并且可以通过设置或清除来启用或禁用该方面。DEXCR 有几种不同的变体用于不同的目的：

- DEXCR
  一个特权 SPR，可以控制用户空间和内核空间的方面。
- HDEXCR
  一个虚拟机监视器特权 SPR，可以控制虚拟机监视器的方面，并强制内核和用户空间执行方面。
- UDEXCR
  一个可选的超监视器特权 SPR，可以控制超监视器的方面。
用户空间可以使用一个专用 SPR 来检查当前 DEXCR 的状态，该 SPR 提供了用户空间 DEXCR 方面的非特权只读视图。还有一个 SPR 提供了只读视图，显示虚拟机监视器强制执行的方面；将这些方面与用户空间 DEXCR 视图进行逻辑或运算，可以得出进程的有效 DEXCR 状态。

配置
=============

prctl
-----

进程可以使用 `prctl(2)` 命令中的 `PR_PPC_GET_DEXCR` 和 `PR_PPC_SET_DEXCR` 对来控制其自身的用户空间 DEXCR 值。这些调用的形式如下所示：

    prctl(PR_PPC_GET_DEXCR, unsigned long which, 0, 0, 0);
    prctl(PR_PPC_SET_DEXCR, unsigned long which, unsigned long ctrl, 0, 0);

可能的 'which' 和 'ctrl' 值如下所示。需要注意的是，'which' 值与 DEXCR 方面的索引之间没有关联。
.. flat-table::
   :header-rows: 1
   :widths: 2 7 1

   * - ``prctl()`` which
     - 方面名称
     - 方面索引

   * - ``PR_PPC_DEXCR_SBHE``
     - 投机分支提示启用 (SBHE)
     - 0

   * - ``PR_PPC_DEXCR_IBRTPD``
     - 间接分支循环目标预测禁用 (IBRTPD)
     - 3

   * - ``PR_PPC_DEXCR_SRAPD``
     - 子程序返回地址预测禁用 (SRAPD)
     - 4

   * - ``PR_PPC_DEXCR_NPHIE``
     - 非特权哈希指令启用 (NPHIE)
     - 5

.. flat-table::
   :header-rows: 1
   :widths: 2 8

   * - ``prctl()`` ctrl
     - 含义

   * - ``PR_PPC_DEXCR_CTRL_EDITABLE``
     - 可以使用 PR_PPC_SET_DEXCR 配置此方面（仅获取）

   * - ``PR_PPC_DEXCR_CTRL_SET``
     - 此方面已设置 / 设置此方面

   * - ``PR_PPC_DEXCR_CTRL_CLEAR``
     - 此方面未设置 / 清除此方面

   * - ``PR_PPC_DEXCR_CTRL_SET_ONEXEC``
     - 执行后此方面将被设置 / 执行后设置此方面

   * - ``PR_PPC_DEXCR_CTRL_CLEAR_ONEXEC``
     - 执行后此方面将被清除 / 执行后清除此方面

需要注意的是：

- which 是一个普通的值，而不是位掩码。必须单独处理各个方面。
- ctrl 是一个位掩码。`PR_PPC_GET_DEXCR` 返回当前配置和执行时配置。例如，`PR_PPC_GET_DEXCR` 可能返回 `PR_PPC_DEXCR_CTRL_EDITABLE | PR_PPC_DEXCR_CTRL_SET | PR_PPC_DEXCR_CTRL_CLEAR_ONEXEC`。这表明该方面目前处于设置状态，在执行时会被清除，并且您可以使用 `PR_PPC_SET_DEXCR` 的 `prctl` 来更改这一点。
- “设置/清除”术语指的是在 DEXCR 中设置/清除位。
例如：

      prctl(PR_PPC_SET_DEXCR, PR_PPC_DEXCR_IBRTPD, PR_PPC_DEXCR_CTRL_SET, 0, 0);

将会在 DEXCR 中设置 IBRTPD 方面位，导致禁用间接分支预测。
* `PR_PPC_GET_DEXCR` 返回的状态代表进程希望应用的值。它不包括任何替代性的覆盖，例如，如果虚拟机监视器强制设置某个特性。为了查看真实的 DEXCR 状态，软件应该直接读取相应的 SPRs。
* 在启动进程时的特性状态是从父进程在 `fork`(2) 时的状态复制过来的。该状态会在 `execve`(2) 时重置为一个固定的值。`PR_PPC_SET_DEXCR` 的 `prctl()` 可以控制这两个值。
* `*_ONEXEC` 控制不会改变当前进程的 DEXCR。使用 `PR_PPC_SET_DEXCR` 并结合 `PR_PPC_DEXCR_CTRL_SET` 或 `PR_PPC_DEXCR_CTRL_CLEAR` 来编辑给定的特性。
* 获取和设置 DEXCR 时常见的错误代码如下：

  .. flat-table::
     :header-rows: 1
     :widths: 2 8

     * - 错误
       - 含义

     * - ``EINVAL``
       - 内核不支持 DEXCR

     * - ``ENODEV``
       - 内核不识别或硬件不支持该特性

`PR_PPC_SET_DEXCR` 还可能报告以下错误代码：

  .. flat-table::
     :header-rows: 1
     :widths: 2 8

     * - 错误
       - 含义

     * - ``EINVAL``
       - ctrl 值包含未识别的标志

     * - ``EINVAL``
       - ctrl 值包含相互冲突的标志（例如，`PR_PPC_DEXCR_CTRL_SET | PR_PPC_DEXCR_CTRL_CLEAR`）

     * - ``EPERM``
       - 无法通过 `prctl()` 修改此特性（使用 `PR_PPC_GET_DEXCR` 检查 `PR_PPC_DEXCR_CTRL_EDITABLE` 标志）

     * - ``EPERM``
       - 进程没有足够的权限执行该操作
例如，清除 exec 时的 NPHIE 是一个需要特权的操作（进程仍然可以在没有特权的情况下清除自己的 NPHIE 特性）
此接口允许一个进程控制其自身的 DEXCR 方面，并且还可以为其进程树中的任何子进程（直到下一个使用“*_ONEXEC”控制的子进程）设置初始 DEXCR 值。这使得能够对 DEXCR 的默认值进行精细的控制，例如，允许容器以不同的默认值运行 coredump 和 ptrace。

------

用户空间中的 DEXCR 和 HDEXCR 值（按此顺序）通过 `NT_PPC_DEXCR` 暴露。这些值各为 64 位且只读，旨在帮助处理核心转储。未来可能会使 DEXCR 可写。两个寄存器的高 32 位（对应非用户空间部分）被屏蔽掉。

如果启用了内核配置 `CONFIG_CHECKPOINT_RESTORE`，那么 `NT_PPC_HASHKEYR` 就可用，并且可以暴露进程的 HASHKEYR 值用于读取和写入。这是一个安全性和检查点/恢复支持之间的权衡：一个进程通常不需要知道自己的密钥，但恢复一个进程需要设置其原始密钥。因此，密钥会出现在核心转储中，攻击者可能从核心转储中检索到它，并有效地绕过所有共享此密钥的线程（可能是来自同一父进程且未运行 `exec()` 的所有线程）上的 ROP 保护。
