SPDX 许可证标识符: (LGPL-2.1 或 BSD-2-Clause)

==============
BPF drgn 工具
==============

drgn 脚本是一种方便且易于使用的机制，用于检索任意的内核数据结构。drgn 并不依赖于内核用户空间 API 来读取数据；相反，它直接从 `/proc/kcore` 或 vmcore 读取，并根据 vmlinux 中的 DWARF 调试信息美化输出数据。
本文档描述了与 BPF 相关的 drgn 工具。
请参阅 `drgn/tools`_ 以获取当前可用的所有工具，以及 `drgn/doc`_ 以了解更多有关 drgn 的详细信息。

bpf_inspect.py
--------------

### 描述

`bpf_inspect.py`_ 是一个用于检查 BPF 程序和映射的工具。它可以遍历系统中的所有程序和映射，并打印这些对象的基本信息，包括 ID、类型和名称。
`bpf_inspect.py`_ 的主要用途是显示通过 `freplace`/`fentry`/`fexit` 机制附加到其他 BPF 程序的类型为 `BPF_PROG_TYPE_EXT` 和 `BPF_PROG_TYPE_TRACING` 的 BPF 程序，因为没有用户空间 API 可以获取这些信息。

### 开始使用

列出 BPF 程序（全名从 BTF 获取）：

```bash
% sudo bpf_inspect.py prog
    27: BPF_PROG_TYPE_TRACEPOINT         tracepoint__tcp__tcp_send_reset
  4632: BPF_PROG_TYPE_CGROUP_SOCK_ADDR   tw_ipt_bind
 49464: BPF_PROG_TYPE_RAW_TRACEPOINT     raw_tracepoint__sched_process_exit
```

列出 BPF 映射：

```bash
% sudo bpf_inspect.py map
   2577: BPF_MAP_TYPE_HASH                tw_ipt_vips
   4050: BPF_MAP_TYPE_STACK_TRACE         stack_traces
   4069: BPF_MAP_TYPE_PERCPU_ARRAY        ned_dctcp_cntr
```

查找附加到 BPF 程序 `test_pkt_access` 的 BPF 程序：

```bash
% sudo bpf_inspect.py p | grep test_pkt_access
   650: BPF_PROG_TYPE_SCHED_CLS          test_pkt_access
   654: BPF_PROG_TYPE_TRACING            test_main                        linked:[650->25: BPF_TRAMP_FEXIT test_pkt_access->test_pkt_access()]
   655: BPF_PROG_TYPE_TRACING            test_subprog1                    linked:[650->29: BPF_TRAMP_FEXIT test_pkt_access->test_pkt_access_subprog1()]
   656: BPF_PROG_TYPE_TRACING            test_subprog2                    linked:[650->31: BPF_TRAMP_FEXIT test_pkt_access->test_pkt_access_subprog2()]
   657: BPF_PROG_TYPE_TRACING            test_subprog3                    linked:[650->21: BPF_TRAMP_FEXIT test_pkt_access->test_pkt_access_subprog3()]
   658: BPF_PROG_TYPE_EXT                new_get_skb_len                  linked:[650->16: BPF_TRAMP_REPLACE test_pkt_access->get_skb_len()]
   659: BPF_PROG_TYPE_EXT                new_get_skb_ifindex              linked:[650->23: BPF_TRAMP_REPLACE test_pkt_access->get_skb_ifindex()]
   660: BPF_PROG_TYPE_EXT                new_get_constant                 linked:[650->19: BPF_TRAMP_REPLACE test_pkt_access->get_constant()]
```

可以看到有一个名为 `test_pkt_access` 的程序，ID 为 650，还有多个其他类型的追踪和扩展程序附加到该程序中的函数。
例如：

```bash
   658: BPF_PROG_TYPE_EXT                new_get_skb_len                  linked:[650->16: BPF_TRAMP_REPLACE test_pkt_access->get_skb_len()]
```

意味着 BPF 程序 ID 658，类型为 `BPF_PROG_TYPE_EXT`，名称为 `new_get_skb_len` 替换（`BPF_TRAMP_REPLACE`）了 BPF 程序 ID 650 名称为 `test_pkt_access` 中的函数 `get_skb_len()`，该函数的 BTF ID 为 16。

### 获取帮助

```bash
% sudo bpf_inspect.py
usage: bpf_inspect.py [-h] {prog,p,map,m} ...
drgn 脚本用于列出 BPF 程序或映射及其属性，这些属性无法通过内核 API 获取。
```
查看 https://github.com/osandov/drgn/ 获取更多关于 drgn 的详情。

可选参数：
      -h, --help      显示此帮助信息并退出

子命令：
      {prog,p,map,m}
        prog (p)      列出 BPF 程序
        map (m)       列出 BPF 映射

自定义
=============

该脚本旨在由开发者进行定制，以打印有关 BPF 程序、映射和其他对象的相关信息。
例如，为了打印 BPF 程序 ID 为 53077 的 `struct bpf_prog_aux`：

.. code-block:: none

    % git diff
    diff --git a/tools/bpf_inspect.py b/tools/bpf_inspect.py
    index 650e228..aea2357 100755
    --- a/tools/bpf_inspect.py
    +++ b/tools/bpf_inspect.py
    @@ -112,7 +112,9 @@ def list_bpf_progs(args):
             if linked:
                 linked = f" linked:[{linked}]"

    -        print(f"{id_:>6}: {type_:32} {name:32} {linked}")
    +        if id_ == 53077:
    +            print(f"{id_:>6}: {type_:32} {name:32}")
    +            print(f"{bpf_prog.aux}")


     def list_bpf_maps(args):

它产生的输出如下：

    % sudo bpf_inspect.py p
     53077: BPF_PROG_TYPE_XDP                tw_xdp_policer
    *(struct bpf_prog_aux *)0xffff8893fad4b400 = {
            .refcnt = (atomic64_t){
                    .counter = (long)58,
            },
            .used_map_cnt = (u32)1,
            .max_ctx_offset = (u32)8,
            .max_pkt_offset = (u32)15,
            .max_tp_access = (u32)0,
            .stack_depth = (u32)8,
            .id = (u32)53077,
            .func_cnt = (u32)0,
            .func_idx = (u32)0,
            .attach_btf_id = (u32)0,
            .linked_prog = (struct bpf_prog *)0x0,
            .verifier_zext = (bool)0,
            .offload_requested = (bool)0,
            .attach_btf_trace = (bool)0,
            .func_proto_unreliable = (bool)0,
            .trampoline_prog_type = (enum bpf_tramp_prog_type)BPF_TRAMP_FENTRY,
            .trampoline = (struct bpf_trampoline *)0x0,
            .tramp_hlist = (struct hlist_node){
                    .next = (struct hlist_node *)0x0,
                    .pprev = (struct hlist_node **)0x0,
            },
            .attach_func_proto = (const struct btf_type *)0x0,
            .attach_func_name = (const char *)0x0,
            .func = (struct bpf_prog **)0x0,
            .jit_data = (void *)0x0,
            .poke_tab = (struct bpf_jit_poke_descriptor *)0x0,
            .size_poke_tab = (u32)0,
            .ksym_tnode = (struct latch_tree_node){
                    .node = (struct rb_node [2]){
                            {
                                    .__rb_parent_color = (unsigned long)18446612956263126665,
                                    .rb_right = (struct rb_node *)0x0,
                                    .rb_left = (struct rb_node *)0xffff88a0be3d0088,
                            },
                            {
                                    .__rb_parent_color = (unsigned long)18446612956263126689,
                                    .rb_right = (struct rb_node *)0x0,
                                    .rb_left = (struct rb_node *)0xffff88a0be3d00a0,
                            },
                    },
            },
            .ksym_lnode = (struct list_head){
                    .next = (struct list_head *)0xffff88bf481830b8,
                    .prev = (struct list_head *)0xffff888309f536b8,
            },
            .ops = (const struct bpf_prog_ops *)xdp_prog_ops+0x0 = 0xffffffff820fa350,
            .used_maps = (struct bpf_map **)0xffff889ff795de98,
            .prog = (struct bpf_prog *)0xffffc9000cf2d000,
            .user = (struct user_struct *)root_user+0x0 = 0xffffffff82444820,
            .load_time = (u64)2408348759285319,
            .cgroup_storage = (struct bpf_map *[2]){},
            .name = (char [16])"tw_xdp_policer",
            .security = (void *)0xffff889ff795d548,
            .offload = (struct bpf_prog_offload *)0x0,
            .btf = (struct btf *)0xffff8890ce6d0580,
            .func_info = (struct bpf_func_info *)0xffff889ff795d240,
            .func_info_aux = (struct bpf_func_info_aux *)0xffff889ff795de20,
            .linfo = (struct bpf_line_info *)0xffff888a707afc00,
            .jited_linfo = (void **)0xffff8893fad48600,
            .func_info_cnt = (u32)1,
            .nr_linfo = (u32)37,
            .linfo_idx = (u32)0,
            .num_exentries = (u32)0,
            .extable = (struct exception_table_entry *)0xffffffffa032d950,
            .stats = (struct bpf_prog_stats *)0x603fe3a1f6d0,
            .work = (struct work_struct){
                    .data = (atomic_long_t){
                            .counter = (long)0,
                    },
                    .entry = (struct list_head){
                            .next = (struct list_head *)0x0,
                            .prev = (struct list_head *)0x0,
                    },
                    .func = (work_func_t)0x0,
            },
            .rcu = (struct callback_head){
                    .next = (struct callback_head *)0x0,
                    .func = (void (*)(struct callback_head *))0x0,
            },
    }

.. 链接
.. _drgn/doc: https://drgn.readthedocs.io/en/latest/
.. _drgn/tools: https://github.com/osandov/drgn/tree/master/tools
.. _bpf_inspect.py:
   https://github.com/osandov/drgn/blob/master/tools/bpf_inspect.py
