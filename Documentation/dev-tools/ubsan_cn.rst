### SPDX 许可证标识符：GPL-2.0

未定义行为检测器 - UBSAN
======================

UBSAN 是一个运行时未定义行为检查器。
UBSAN 使用编译时插入代码的方法来捕捉未定义行为（UB）。
编译器在可能会导致未定义行为的操作前插入执行某些类型检查的代码。如果检查失败（即检测到 UB），则调用 `__ubsan_handle_*` 函数来打印错误信息。
自从 GCC 4.9.x 版本起 [1_] （参见 `-fsanitize=undefined` 选项及其子选项），GCC 已经具备这一特性。GCC 5.x 版本实现了更多的检查器 [2_]。

报告示例
--------

```
================================================================================
UBSAN: 未定义行为在 ../include/linux/bitops.h:110:33
移位指数 32 对于 32 位类型 'unsigned int' 来说太大
CPU: 0 PID: 0 进程: swapper 系统未被污染 4.4.0-rc1+ #26
 0000000000000000 ffffffff82403cc8 ffffffff815e6cd6 0000000000000001
 ffffffff82403cf8 ffffffff82403ce0 ffffffff8163a5ed 0000000000000020
 ffffffff82403d78 ffffffff8163ac2b ffffffff815f0001 0000000000000002
调用跟踪：
 [ <ffffffff815e6cd6> ] dump_stack+0x45/0x5f
 [ <ffffffff8163a5ed> ] ubsan_epilogue+0xd/0x40
 [ <ffffffff8163ac2b> ] __ubsan_handle_shift_out_of_bounds+0xeb/0x130
 [ <ffffffff815f0001> ] ? radix_tree_gang_lookup_slot+0x51/0x150
 [ <ffffffff8173c586> ] _mix_pool_bytes+0x1e6/0x480
 [ <ffffffff83105653> ] ? dmi_walk_early+0x48/0x5c
 [ <ffffffff8173c881> ] add_device_randomness+0x61/0x130
 [ <ffffffff83105b35> ] ? dmi_save_one_device+0xaa/0xaa
 [ <ffffffff83105653> ] dmi_walk_early+0x48/0x5c
 [ <ffffffff831066ae> ] dmi_scan_machine+0x278/0x4b4
 [ <ffffffff8111d58a> ] ? vprintk_default+0x1a/0x20
 [ <ffffffff830ad120> ] ? early_idt_handler_array+0x120/0x120
 [ <ffffffff830b2240> ] setup_arch+0x405/0xc2c
 [ <ffffffff830ad120> ] ? early_idt_handler_array+0x120/0x120
 [ <ffffffff830ae053> ] start_kernel+0x83/0x49a
 [ <ffffffff830ad120> ] ? early_idt_handler_array+0x120/0x120
 [ <ffffffff830ad386> ] x86_64_start_reservations+0x2a/0x2c
 [ <ffffffff830ad4f3> ] x86_64_start_kernel+0x16b/0x17a
================================================================================
```

使用方法
-------

为了启用 UBSAN，使用以下配置来配置内核：

```
CONFIG_UBSAN=y
```

为了排除某些文件不进行插入代码处理，可以使用：

```
UBSAN_SANITIZE_main.o := n
```

而为了排除某个目录下的所有目标，可以使用：

```
UBSAN_SANITIZE := n
```

当对所有目标禁用时，可以通过以下方式为特定文件启用：

```
UBSAN_SANITIZE_main.o := y
```

未对齐访问的检测是通过单独的选项控制的 — `CONFIG_UBSAN_ALIGNMENT`。默认情况下，在支持未对齐访问的架构上（`CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS=y`），它是关闭的。你仍然可以在配置中启用它，但请注意这样做会产生大量的 UBSAN 报告。

参考链接
---------

.. _1: https://gcc.gnu.org/onlinedocs/gcc-4.9.0/gcc/Debugging-Options.html
.. _2: https://gcc.gnu.org/onlinedocs/gcc/Debugging-Options.html
.. _3: https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
