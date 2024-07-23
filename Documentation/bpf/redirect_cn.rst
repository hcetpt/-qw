SPDX 许可证标识符：仅限 GPL-2.0
版权 (C) 2022 Red Hat, Inc.

======
重定向
======

XDP_REDIRECT
############

支持的映射
--------------

XDP_REDIRECT 支持以下映射类型：

- ``BPF_MAP_TYPE_DEVMAP``
- ``BPF_MAP_TYPE_DEVMAP_HASH``
- ``BPF_MAP_TYPE_CPUMAP``
- ``BPF_MAP_TYPE_XSKMAP``

关于这些映射的更多信息，请参阅特定映射的文档。

过程
------

.. kernel-doc:: net/core/filter.c
   :doc: xdp 重定向

.. note::
    并非所有驱动程序都支持重定向后的帧传输，而对于那些支持的驱动程序，并非所有驱动程序都支持非线性帧。非线性的 xdp bufs/frames 是包含一个以上片段的 bufs/frames。

调试丢包问题
----------------------
XDP_REDIRECT 的静默丢包可以使用以下工具进行调试：

- bpf_trace
- perf_record

bpf_trace
^^^^^^^^^
以下 bpftrace 命令可用于捕获并计算所有 XDP 跟踪点：

.. code-block:: none

    sudo bpftrace -e 'tracepoint:xdp:* { @cnt[probe] = count(); }'
    Attaching 12 probes..
^C

    @cnt[tracepoint:xdp:mem_connect]: 18
    @cnt[tracepoint:xdp:mem_disconnect]: 18
    @cnt[tracepoint:xdp:xdp_exception]: 19605
    @cnt[tracepoint:xdp:xdp_devmap_xmit]: 1393604
    @cnt[tracepoint:xdp:xdp_redirect]: 22292200

.. note::
    各种 xdp 跟踪点可以在 ``source/include/trace/events/xdp.h`` 中找到。

以下 bpftrace 命令可用于提取作为 err 参数返回的 ``ERRNO``：

.. code-block:: none

    sudo bpftrace -e \
    'tracepoint:xdp:xdp_redirect*_err {@redir_errno[-args->err] = count();}
    tracepoint:xdp:xdp_devmap_xmit {@devmap_errno[-args->err] = count();}'

perf record
^^^^^^^^^^^
perf 工具也支持记录跟踪点：

.. code-block:: none

    perf record -a -e xdp:xdp_redirect_err \
        -e xdp:xdp_redirect_map_err \
        -e xdp:xdp_exception \
        -e xdp:xdp_devmap_xmit

参考资料
===========

- https://github.com/xdp-project/xdp-tutorial/tree/master/tracing02-xdp-monitor
