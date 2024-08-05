### SPDX 许可证标识符：GPL-2.0

=================================
内核级异常处理
=================================

评论者：Joerg Pommnitz <joerg@raleigh.ibm.com>

当一个进程在内核模式下运行时，它经常需要访问由不受信任的程序传递地址的用户模式内存。为了自我保护，内核必须验证这个地址。在较旧版本的 Linux 中，这是通过 `int verify_area(int type, const void * addr, unsigned long size)` 函数完成的（该函数后来被 `access_ok()` 替代）。此函数验证从地址 `'addr'` 开始且大小为 `'size'` 的内存区域是否可以执行类型参数中指定的操作（读或写）。为此，`verify_read` 必须查找包含地址 `addr` 的虚拟内存区域 (vma)。在正常情况下（正确工作的程序），这种测试是成功的；只有少数有问题的程序会导致测试失败。在某些内核性能分析测试中，这种通常不需要的验证占用了大量时间。

为了解决这种情况，Linus 决定让存在于每个支持 Linux 的 CPU 中的虚拟内存硬件来处理这种测试。这如何工作？

每当内核尝试访问当前不可访问的地址时，CPU 会生成一个页面错误异常并调用页面故障处理器：

```c
void exc_page_fault(struct pt_regs *regs, unsigned long error_code)
```

位于 `arch/x86/mm/fault.c` 中。栈上的参数由 `arch/x86/entry/entry_32.S` 中的低级汇编粘合代码设置。参数 `regs` 是指向栈上保存的寄存器的指针，`error_code` 包含异常的原因代码。
`exc_page_fault()` 首先从 CPU 控制寄存器 CR2 获取不可访问的地址。如果地址位于进程的虚拟地址空间内，则可能是因为页面未交换入、写保护等原因导致了故障。然而，我们感兴趣的是另一种情况：地址无效，没有包含该地址的 vma。在这种情况下，内核跳转到 `bad_area` 标签处。

在那里，它使用导致异常的指令的地址（即 `regs->eip`）来找到可以继续执行的地址（修复点 `fixup`）。如果这个搜索成功，故障处理器会修改返回地址（再次是 `regs->eip`）并返回。执行将继续在 `fixup` 指向的地址处进行。

`fixup` 指向哪里？

因为我们跳转到 `fixup` 的内容，显然 `fixup` 指向可执行代码。这段代码隐藏在用户访问宏内部。
我选择了在 `arch/x86/include/asm/uaccess.h` 中定义的 `get_user()` 宏作为示例。它的定义有些难以理解，因此让我们来看看预处理器和编译器生成的代码。我在 `drivers/char/sysrq.c` 中选择了 `get_user()` 调用进行详细分析。

原始 `sysrq.c` 第 587 行的代码如下：

        get_user(c, buf);

预处理器输出（为了便于阅读进行了编辑）如下：

  (
    {
      long __gu_err = - 14 , __gu_val = 0;
      const __typeof__(*( (  buf ) )) *__gu_addr = ((buf));
      if (((((0 + current_set[0])->tss.segment) == 0x18 )  ||
        (((sizeof(*(buf))) <= 0xC0000000UL) &&
        ((unsigned long)(__gu_addr ) <= 0xC0000000UL - (sizeof(*(buf)))))))
        do {
          __gu_err  = 0;
          switch ((sizeof(*(buf)))) {
            case 1:
              __asm__ __volatile__(
                "1:      mov" "b" " %2,%" "b" "1\n"
                "2:\n"
                ".section .fixup,\"ax\"\n"
                "3:      movl %3,%0\n"
                "        xor" "b" " %" "b" "1,%" "b" "1\n"
                "        jmp 2b\n"
                ".section __ex_table,\"a\"\n"
                "        .align 4\n"
                "        .long 1b,3b\n"
                ".text"        : "=r"(__gu_err), "=q" (__gu_val): "m"((*(struct __large_struct *)
                              (   __gu_addr   )) ), "i"(- 14 ), "0"(  __gu_err  )) ;
                break;
            case 2:
              __asm__ __volatile__(
                "1:      mov" "w" " %2,%" "w" "1\n"
                "2:\n"
                ".section .fixup,\"ax\"\n"
                "3:      movl %3,%0\n"
                "        xor" "w" " %" "w" "1,%" "w" "1\n"
                "        jmp 2b\n"
                ".section __ex_table,\"a\"\n"
                "        .align 4\n"
                "        .long 1b,3b\n"
                ".text"        : "=r"(__gu_err), "=r" (__gu_val) : "m"((*(struct __large_struct *)
                              (   __gu_addr   )) ), "i"(- 14 ), "0"(  __gu_err  ));
                break;
            case 4:
              __asm__ __volatile__(
                "1:      mov" "l" " %2,%" "" "1\n"
                "2:\n"
                ".section .fixup,\"ax\"\n"
                "3:      movl %3,%0\n"
                "        xor" "l" " %" "" "1,%" "" "1\n"
                "        jmp 2b\n"
                ".section __ex_table,\"a\"\n"
                "        .align 4\n"        "        .long 1b,3b\n"
                ".text"        : "=r"(__gu_err), "=r" (__gu_val) : "m"((*(struct __large_struct *)
                              (   __gu_addr   )) ), "i"(- 14 ), "0"(__gu_err));
                break;
            default:
              (__gu_val) = __get_user_bad();
          }
        } while (0) ;
      ((c)) = (__typeof__(*((buf))))__gu_val;
      __gu_err;
    }
  );

哇！这是GCC/汇编的黑色魔法。这太难理解了，所以我们来看看GCC生成的代码：

 >         xorl %edx,%edx
 >         movl current_set,%eax
 >         cmpl $24,788(%eax)
 >         je .L1424
 >         cmpl $-1073741825,64(%esp)
 >         ja .L1423
 > .L1424:
 >         movl %edx,%eax
 >         movl 64(%esp),%ebx
 > #APP
 > 1:      movb (%ebx),%dl                /* 这是实际的用户访问 */
 > 2:
 > .section .fixup,"ax"
 > 3:      movl $-14,%eax
 >         xorb %dl,%dl
 >         jmp 2b
 > .section __ex_table,"a"
 >         .align 4
 >         .long 1b,3b
 > .text
 > #NO_APP
 > .L1423:
 >         movzbl %dl,%esi

优化器做得很好，给出了我们实际上可以理解的东西。我们可以吗？实际的用户访问非常显眼。多亏了统一地址空间，我们能够直接访问用户内存中的地址。但是那些 `.section` 语句到底做了什么？

要理解这些，我们需要查看最终的内核：

 > objdump --section-headers vmlinux
 >
 > vmlinux:     文件格式 elf32-i386
 >
 > Section:
 > Idx Name          Size      VMA       LMA       File off  Algn
 >   0 .text         00098f40  c0100000  c0100000  00001000  2**4
 >                   内容, 分配, 加载, 只读, 代码
 >   1 .fixup        000016bc  c0198f40  c0198f40  00099f40  2**0
 >                   内容, 分配, 加载, 只读, 代码
 >   2 .rodata       0000f127  c019a5fc  c019a5fc  0009b5fc  2**2
 >                   内容, 分配, 加载, 只读, 数据
 >   3 __ex_table    000015c0  c01a9724  c01a9724  000aa724  2**2
 >                   内容, 分配, 加载, 只读, 数据
 >   4 .data         0000ea58  c01abcf0  c01abcf0  000abcf0  2**4
 >                   内容, 分配, 加载, 数据
 >   5 .bss          00018e21  c01ba748  c01ba748  000ba748  2**2
 >                   分配
 >   6 .comment      00000ec4  00000000  00000000  000ba748  2**0
 >                   内容, 只读
 >   7 .note         00001068  00000ec4  00000ec4  000bb60c  2**0
 >                   内容, 只读

显然，在生成的目标文件中有两个非标准的 ELF 区段。但首先，我们想要找出我们的代码在最终内核可执行文件中发生了什么变化：

 > objdump --disassemble --section=.text vmlinux
 >
 > c017e785 <do_con_write+c1> xorl   %edx,%edx
 > c017e787 <do_con_write+c3> movl   0xc01c7bec,%eax
 > c017e78c <do_con_write+c8> cmpl   $0x18,0x314(%eax)
 > c017e793 <do_con_write+cf> je     c017e79f <do_con_write+db>
 > c017e795 <do_con_write+d1> cmpl   $0xbfffffff,0x40(%esp,1)
 > c017e79d <do_con_write+d9> ja     c017e7a7 <do_con_write+e3>
 > c017e79f <do_con_write+db> movl   %edx,%eax
 > c017e7a1 <do_con_write+dd> movl   0x40(%esp,1),%ebx
 > c017e7a5 <do_con_write+e1> movb   (%ebx),%dl
 > c017e7a7 <do_con_write+e3> movzbl %dl,%esi

整个用户内存访问被减少到 10 条 x86 机器指令。指令之间被`.section`指令括起来的部分已经不再处于正常的执行路径中。它们位于可执行文件的不同区段中：

 > objdump --disassemble --section=.fixup vmlinux
 >
 > c0199ff5 <.fixup+10b5> movl   $0xfffffff2,%eax
 > c0199ffa <.fixup+10ba> xorb   %dl,%dl
 > c0199ffc <.fixup+10bc> jmp    c017e7a7 <do_con_write+e3>

最后：

 > objdump --full-contents --section=__ex_table vmlinux
 >
 >  c01aa7c4 93c017c0 e09f19c0 97c017c0 99c017c0  ...............
>  c01aa7d4 f6c217c0 e99f19c0 a5e717c0 f59f19c0  ...............
>  c01aa7e4 080a18c0 01a019c0 0a0a18c0 04a019c0  ...............
或者按人类可读的字节顺序显示为：

 >  c01aa7c4 c017c093 c0199fe0 c017c097 c017c099  ...............
>  c01aa7d4 c017c2f6 c0199fe9 c017e7a5 c0199ff5  ...............
^^^^^^^^^^^^^^^^^
                               这是有趣的部分！
 >  c01aa7e4 c0180a08 c019a001 c0180a0a c019a004  ...............

发生了什么？汇编指令：

  .section .fixup,"ax"
  .section __ex_table,"a"

告诉汇编器将以下代码移动到 ELF 目标文件中指定的区段。因此，指令：

  3:      movl $-14,%eax
          xorb %dl,%dl
          jmp 2b

最终位于对象文件的 `.fixup` 区段中，而地址：

        .long 1b,3b

则位于对象文件的 `__ex_table` 区段中。1b 和 3b 是局部标签。局部标签 1b（1b 代表向后下一个标签 1）是可能引发错误的指令的地址，即在我们的情况下，1 标签的地址为 c017e7a5：
原始汇编代码：> 1:      movb (%ebx),%dl
链接后的 vmlinux：> c017e7a5 <do_con_write+e1> movb   (%ebx),%dl

局部标签 3（再次向后）是处理故障的代码的地址，在我们的情况下实际值为 c0199ff5：
原始汇编代码：> 3:      movl $-14,%eax
链接后的 vmlinux：> c0199ff5 <.fixup+10b5> movl   $0xfffffff2,%eax

如果修复程序能够处理异常，则控制流可以返回到触发故障的指令之后的指令，即局部标签 2b。
这段汇编代码：

```
> .section __ex_table,"a"
>         .align 4
>         .long 1b,3b
```

转换成了值对：

```
>  c01aa7d4 c017c2f6 c0199fe9 c017e7a5 c0199ff5  ...............
^this is ^this is
                               1b       3b

c017e7a5,c0199ff5 在内核异常表中
那么，如果在内核模式下发生故障且没有合适的 vma，实际会发生什么？

1. 访问无效地址：

    ```
    > c017e7a5 <do_con_write+e1> movb   (%ebx),%dl
    ```
2. MMU 生成异常
3. CPU 调用 `exc_page_fault()`
4. `exc_page_fault()` 调用 `do_user_addr_fault()`
5. `do_user_addr_fault()` 调用 `kernelmode_fixup_or_oops()`
6. `kernelmode_fixup_or_oops()` 调用 `fixup_exception()` (`regs->eip == c017e7a5`);
7. `fixup_exception()` 调用 `search_exception_tables()`
8. `search_exception_tables()` 查找地址 c017e7a5 在异常表中的内容（即 ELF 部分 __ex_table 的内容）并返回与之关联的故障处理代码的地址 c0199ff5
9. `fixup_exception()` 修改其返回地址以指向故障处理代码并返回
10. 执行继续在故障处理代码中进行
11. a) EAX 变为 -EFAULT（等于 -14）
    b) DL 变为零（我们从用户空间“读取”的值）
    c) 执行继续在局部标签 2 处（故障用户访问后立即指令的位置）
步骤 a 到 c 在某种程度上模拟了引发故障的指令
大致就是这样。如果你看看我们的例子，你可能会问为什么我们在异常处理代码中将 EAX 设置为 -EFAULT。嗯，`get_user()` 宏实际上返回一个值：如果用户访问成功则返回 0，失败时返回 -EFAULT。我们的原始代码并没有测试这个返回值，但是 `get_user()` 中的内联汇编代码试图返回 -EFAULT。GCC 选择了 EAX 来返回这个值。
**注释**：
由于异常表构建方式及其需要排序的方式，仅对 `.text` 段中的代码使用异常。任何其他段都将导致异常表无法正确排序，并且异常会失败。
当 x86 Linux 添加 64 位支持时情况发生了变化。而不是通过将两个条目的大小从 32 位扩展到 64 位来使异常表大小加倍，而是使用了一个巧妙的方法来将地址存储为相对于表本身的相对偏移量。汇编代码从：

```
    .long 1b,3b
```
变为：
```
          .long (from) -
```
这段代码和描述可以翻译为：

`.long (to)` - C代码使用这些值并将其转换回绝对地址，如下所示：

```c
unsigned long ex_insn_addr(const struct exception_table_entry *x)
{
    return (unsigned long)&x->insn + x->insn;
}
```

在版本4.6中，异常表项被扩展了一个新的字段 "handler"。这个字段同样有32位宽，并包含第三个相对函数指针，指向以下之一：

1) `int ex_handler_default(const struct exception_table_entry *fixup)`
     这是遗留情况，仅仅跳转到修复代码。

2) `int ex_handler_fault(const struct exception_table_entry *fixup)`
     这种情况提供了在`entry->insn`处发生的陷阱的故障编号。它用于区分页面错误与机器检查。
更多的函数可以轻松添加。

`CONFIG_BUILDTIME_TABLE_SORT`允许在内核镜像链接后对`__ex_table`段进行排序，通过主机工具脚本`scripts/sorttable`实现。它会将符号`main_extable_sort_needed`设置为0，避免在启动时对`__ex_table`段进行排序。有了排序后的异常表，在运行时发生异常时，我们可以通过二分查找快速定位`__ex_table`中的条目。
这不仅仅是启动优化，某些架构需要这个表在启动过程较早阶段就能处理异常。例如，i386在启用分页支持之前就利用这种形式的异常处理！
