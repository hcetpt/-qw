SPDX 许可证标识符: GPL-2.0

DAMON 维护者条目简介
==============================

DAMON 子系统涵盖了在 'MAINTAINERS' 文件的 'DATA ACCESS MONITOR' 部分中列出的文件。该子系统的邮件列表是 damon@lists.linux.dev 和 linux-mm@kvack.org。尽可能地，补丁应针对 mm-unstable 树[1]_制作，并发送到这些邮件列表。

SCM 树
-------

有多个用于 DAMON 开发的 Linux 树。正在开发或测试中的补丁由 DAMON 维护者排队在 damon/next [2]_ 中。经过充分审查的补丁将由内存管理子系统维护者排队在 mm-unstable [1]_ 中。经过更多充分测试后，补丁将被排队在 mm-stable [3]_ 中，并最终由内存管理子系统维护者向主线发出拉取请求。

请注意，mm-unstable 树 [1]_ 的补丁是由内存管理子系统维护者排队的。如果补丁需要 damon/next 树 [2]_ 中尚未合并到 mm-unstable 的某些补丁，请确保明确说明此要求。

提交检查清单补充
-------------------------

当进行 DAMON 更改时，你应该执行以下操作：
- 构建相关的输出，包括内核和文档。
- 确保构建不会引入新的错误或警告。
- 运行并确保 DAMON 自测 [4]_ 和 kunittests [5]_ 没有新的失败。
进一步完成以下操作并将结果附上将会有所帮助。
- 对于常规更改，运行 damon-tests/corr [6]_
- 对于性能更改，运行 damon-tests/perf [7]_

关键周期日期
------------

补丁可以随时发送。mm-unstable [1]_ 和 mm-stable [3]_ 树的关键周期日期取决于内存管理子系统维护者的审核节奏。

审核周期
------------

DAMON 维护者通常在太平洋时间（PT）的工作时间（周一至周五，09:00 至 17:00）进行工作。对补丁的响应可能会偶尔变慢。如果您在一星期内没有收到回复，请不要犹豫发送一个提醒（ping）。

.. [1] https://git.kernel.org/akpm/mm/h/mm-unstable
.. [2] https://git.kernel.org/sj/h/damon/next
.. [3] https://git.kernel.org/akpm/mm/h/mm-stable
.. [4] https://github.com/awslabs/damon-tests/blob/master/corr/run.sh#L49
.. [5] https://github.com/awslabs/damon-tests/blob/master/corr/tests/kunit.sh
.. [6] https://github.com/awslabs/damon-tests/tree/master/corr
.. [7] https://github.com/awslabs/damon-tests/tree/master/perf
