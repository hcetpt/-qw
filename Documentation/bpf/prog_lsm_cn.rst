### SPDX 许可证标识符: GPL-2.0+
### 版权所有 (C) 2020 Google LLC

======================
LSM BPF 程序
======================

这些 BPF 程序允许特权用户在运行时对 LSM 钩子进行仪器化，以使用 eBPF 实现系统范围的强制访问控制 (MAC) 和审计策略。

#### 结构

示例展示了一个可以附加到 `file_mprotect` LSM 钩子上的 eBPF 程序：

```c
int file_mprotect(struct vm_area_struct *vma, unsigned long reqprot, unsigned long prot);
```

可以在 `security/security.c` 中找到其他可以被仪器化的 LSM 钩子。使用 [Documentation/bpf/btf.rst](Documentation/bpf/btf.rst) 的 eBPF 程序不需要包含内核头文件来从附加的 eBPF 程序上下文中访问信息。它们只需在 eBPF 程序中声明结构体并仅指定需要访问的字段即可。

```c
struct mm_struct {
    unsigned long start_brk, brk, start_stack;
} __attribute__((preserve_access_index));

struct vm_area_struct {
    unsigned long start_brk, brk, start_stack;
    unsigned long vm_start, vm_end;
    struct mm_struct *vm_mm;
} __attribute__((preserve_access_index));
```

**注意：** 字段的顺序无关紧要。

如果在构建时有访问 BTF 信息的权限，则可以通过以下方式进一步简化：

```console
# bpftool btf dump file <path-to-btf-vmlinux> format c > vmlinux.h
```

**注意：** `<path-to-btf-vmlinux>` 可能是 `/sys/kernel/btf/vmlinux`，如果构建环境与部署 BPF 程序的环境相匹配的话。

然后可以直接在 BPF 程序中包含 `vmlinux.h` 而无需定义类型。使用在 `tools/lib/bpf/bpf_tracing.h` 定义的 `BPF_PROG` 宏声明 eBPF 程序。例如：

- `"lsm/file_mprotect"` 指示程序必须附加到的 LSM 钩子。
- `mprotect_audit` 是 eBPF 程序的名称。

```c
SEC("lsm/file_mprotect")
int BPF_PROG(mprotect_audit, struct vm_area_struct *vma,
             unsigned long reqprot, unsigned long prot, int ret)
{
    /* ret 是来自上一个 BPF 程序的返回值
       或者如果是第一个钩子则为 0 */
    if (ret != 0)
        return ret;

    int is_heap;

    is_heap = (vma->vm_start >= vma->vm_mm->start_brk &&
               vma->vm_end <= vma->vm_mm->brk);

    /* 返回 -EPERM 或将信息写入 perf 事件缓冲区以供审计 */
    if (is_heap)
        return -EPERM;
}
```

`__attribute__((preserve_access_index))` 是 Clang 的特性，它允许 BPF 验证器使用 [Documentation/bpf/btf.rst](Documentation/bpf/btf.rst) 信息在运行时更新访问偏移量。由于 BPF 验证器了解类型，因此它也会验证 eBPF 程序中对各种类型的访问。
加载
-------

eBPF 程序可以通过 `bpf(2)` 系统调用的 `BPF_PROG_LOAD` 操作进行加载：

.. code-block:: c

    struct bpf_object *obj;

    obj = bpf_object__open("./my_prog.o");
    bpf_object__load(obj);

这一步骤可以通过使用由 `bpftool` 生成的骨架头文件来简化：

.. code-block:: console

    # bpftool gen skeleton my_prog.o > my_prog.skel.h

通过包含 `my_prog.skel.h` 并使用生成的帮助函数 `my_prog__open_and_load`，可以加载程序。

附着到 LSM 钩子
-------------------

LSM 允许通过 `bpf(2)` 系统调用的 `BPF_RAW_TRACEPOINT_OPEN` 操作或更简单地使用 libbpf 辅助函数 `bpf_program__attach_lsm` 将 eBPF 程序作为 LSM 钩子进行附着。
可以通过 *销毁* 由 `bpf_program__attach_lsm` 返回的 `link` 来从 LSM 钩子中分离程序，使用 `bpf_link__destroy` 函数。
也可以使用在 `my_prog.skel.h` 中生成的帮助函数，例如 `my_prog__attach` 用于附着，`my_prog__destroy` 用于清理。

示例
--------

一个 eBPF 示例程序可以在 `tools/testing/selftests/bpf/progs/lsm.c`_ 找到，相应的用户空间代码位于 `tools/testing/selftests/bpf/prog_tests/test_lsm.c`_。

.. Links
.. _tools/lib/bpf/bpf_tracing.h:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/lib/bpf/bpf_tracing.h
.. _tools/testing/selftests/bpf/progs/lsm.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/progs/lsm.c
.. _tools/testing/selftests/bpf/prog_tests/test_lsm.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/prog_tests/test_lsm.c
