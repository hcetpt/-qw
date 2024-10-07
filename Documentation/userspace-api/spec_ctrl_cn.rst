### 投机控制

许多CPU存在与投机相关的缺陷，这些缺陷实际上是漏洞，会导致各种形式的数据泄露，甚至跨越权限域。内核以多种形式提供了对这类漏洞的缓解措施。其中一些缓解措施可以在编译时进行配置，有些则可以通过内核命令行提供。

还有一类非常昂贵的缓解措施，但它们可以限制在受控环境中的某些进程或任务上。控制这些缓解措施的机制是通过 `prctl(2)` 实现的。

有两个与投机控制相关的 `prctl` 选项：

* PR_GET_SPECULATION_CTRL

* PR_SET_SPECULATION_CTRL

#### PR_GET_SPECULATION_CTRL

`PR_GET_SPECULATION_CTRL` 返回由 `prctl(2)` 的 `arg2` 参数选择的投机缺陷的状态。返回值使用位 0-3，其含义如下：

==== ====================== ==================================================
位   定义                   描述
==== ====================== ==================================================
0    PR_SPEC_PRCTL          缓解措施可以由每个任务通过 `PR_SET_SPECULATION_CTRL` 进行控制
1    PR_SPEC_ENABLE         投机功能已启用，缓解措施已禁用
2    PR_SPEC_DISABLE        投机功能已禁用，缓解措施已启用
3    PR_SPEC_FORCE_DISABLE  同 `PR_SPEC_DISABLE`，但无法撤销。后续的 `prctl(..., PR_SPEC_ENABLE)` 将失败
4    PR_SPEC_DISABLE_NOEXEC 同 `PR_SPEC_DISABLE`，但在 `execve(2)` 时状态将被清除
==== ====================== ==================================================

如果所有位都为 0，则表示该 CPU 不受投机缺陷的影响。
如果设置了 `PR_SPEC_PRCTL`，则可以使用每个任务的缓解措施控制。如果没有设置，则针对该投机缺陷的 `prctl(PR_SET_SPECULATION_CTRL)` 调用将失败。
.. _set_spec_ctrl:

PR_SET_SPECULATION_CTRL
-----------------------

`PR_SET_SPECULATION_CTRL` 允许通过 `prctl(2)` 的 arg2 参数按任务控制推测执行缺陷。arg3 用于传递控制值，即 `PR_SPEC_ENABLE`、`PR_SPEC_DISABLE` 或 `PR_SPEC_FORCE_DISABLE`。

常见错误代码
------------------
======= =================================================================
值       含义
======= =================================================================
EINVAL  架构不支持 prctl 或者未使用的 prctl(2) 参数不为 0
ENODEV  arg2 选择了不支持的推测执行缺陷
======= =================================================================

`PR_SET_SPECULATION_CTRL` 错误代码
-----------------------------------
======= =================================================================
值       含义
======= =================================================================
0       成功

ERANGE  arg3 不正确，即不是 `PR_SPEC_ENABLE`、`PR_SPEC_DISABLE` 或 `PR_SPEC_FORCE_DISABLE`
ENXIO   无法控制选定的推测执行缺陷
参见 `PR_GET_SPECULATION_CTRL`
EPERM   推测执行已通过 `PR_SPEC_FORCE_DISABLE` 禁用，并且调用者尝试再次启用
======= =================================================================

推测执行缺陷控制
-------------------
- `PR_SPEC_STORE_BYPASS`: 推测性存储旁路

  调用示例：
   * `prctl(PR_GET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, 0, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_ENABLE, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_DISABLE, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_FORCE_DISABLE, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_DISABLE_NOEXEC, 0, 0);`

- `PR_SPEC_INDIR_BRANCH`: 用户进程中的间接分支推测（缓解针对用户进程的 Spectre V2 风格攻击）

  调用示例：
   * `prctl(PR_GET_SPECULATION_CTRL, PR_SPEC_INDIRECT_BRANCH, 0, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_INDIRECT_BRANCH, PR_SPEC_ENABLE, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_INDIRECT_BRANCH, PR_SPEC_DISABLE, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_INDIRECT_BRANCH, PR_SPEC_FORCE_DISABLE, 0, 0);`

- `PR_SPEC_L1D_FLUSH`: 在任务上下文切换时刷新 L1D 缓存（仅在任务运行于非 SMT 核心时生效）

  调用示例：
   * `prctl(PR_GET_SPECULATION_CTRL, PR_SPEC_L1D_FLUSH, 0, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_L1D_FLUSH, PR_SPEC_ENABLE, 0, 0);`
   * `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_L1D_FLUSH, PR_SPEC_DISABLE, 0, 0);`
