静态键
======

.. 警告::

   已弃用的API：

   直接使用 'struct static_key' 现在已被弃用。此外，static_key_{true,false}() 也被弃用。即不要使用以下代码::

    struct static_key false = STATIC_KEY_INIT_FALSE;
    struct static_key true = STATIC_KEY_INIT_TRUE;
    static_key_true()
    static_key_false()

   更新的API替代方案是::

    DEFINE_STATIC_KEY_TRUE(key);
    DEFINE_STATIC_KEY_FALSE(key);
    DEFINE_STATIC_KEY_ARRAY_TRUE(keys, count);
    DEFINE_STATIC_KEY_ARRAY_FALSE(keys, count);
    static_branch_likely()
    static_branch_unlikely()

摘要
====

静态键通过GCC特性及代码修补技术，允许将较少使用的功能包含到性能敏感的快速路径内核代码中。一个快速示例::

    DEFINE_STATIC_KEY_FALSE(key);

    ..
    if (static_branch_unlikely(&key))
            执行不常执行的代码
    else
            执行常执行的代码

    ..
    static_branch_enable(&key);
    ..
    static_branch_disable(&key);
    ..

   static_branch_unlikely() 分支将以对常执行代码路径影响最小的方式生成到代码中。
动机
====

目前，跟踪点（tracepoints）实现时使用了条件分支。条件检查需要为每个跟踪点检查一个全局变量。尽管这种检查的开销很小，但在内存缓存压力增加时（这些全局变量的内存缓存行可能与其他内存访问共享），开销会增大。随着内核中跟踪点数量的增加，这种开销可能会成为一个更大的问题。此外，跟踪点通常处于休眠状态（已禁用），并不提供直接的内核功能。因此，尽可能减少其影响是非常必要的。虽然跟踪点是这项工作的原始动机，但其他内核代码路径也应能够利用静态键机制。
解决方案
========

GCC (v4.5) 添加了一个新的 'asm goto' 语句，允许分支到标签：

https://gcc.gnu.org/ml/gcc-patches/2009-07/msg01556.html

使用 'asm goto'，我们可以创建默认情况下要么被采用、要么不被采用的分支，而无需检查内存。然后，在运行时，我们可以修补分支点以改变分支方向。例如，如果有一个简单的默认情况下被禁用的分支::

    if (static_branch_unlikely(&key))
        printk("I am the true branch\n");

这样，默认情况下不会发出 'printk'。生成的代码将仅由一个原子 'no-op' 指令（在x86上为5字节）组成，在直线代码路径中。当分支被“翻转”时，我们将直线代码路径中的 'no-op' 指令修补为指向非直线真分支的 'jump' 指令。因此，改变分支方向的成本较高，但分支选择基本上是“免费”的。这就是此优化的基本权衡。

这种低级别的修补机制被称为“跳转标签修补”，它构成了静态键设施的基础。
静态键标签API、用法和示例
========================================

为了利用这种优化，您必须首先定义一个键：

```c
DEFINE_STATIC_KEY_TRUE(key);
```

或者：

```c
DEFINE_STATIC_KEY_FALSE(key);
```

该键必须是全局的，也就是说，它不能在栈上分配或在运行时动态分配。然后，在代码中使用该键如下：

```c
if (static_branch_unlikely(&key))
        执行不太可能的代码
else
        执行很可能的代码
```

或者：

```c
if (static_branch_likely(&key))
        执行很可能的代码
else
        执行不太可能的代码
```

通过 `DEFINE_STATIC_KEY_TRUE()` 或 `DEFINE_STATIC_KEY_FALSE` 定义的键可以在 `static_branch_likely()` 或 `static_branch_unlikely()` 语句中使用。

分支可以通过以下方式设置为真：

```c
static_branch_enable(&key);
```

或者设置为假：

```c
static_branch_disable(&key);
```

然后可以通过引用计数切换分支：

```c
static_branch_inc(&key);
...
static_branch_dec(&key);
```

因此，`static_branch_inc()` 表示“使分支变为真”，而 `static_branch_dec()` 表示“使分支变为假”，并进行适当的引用计数。例如，如果键初始化为真，那么 `static_branch_dec()` 将使分支变为假。随后的 `static_branch_inc()` 将使分支重新变为真。同样，如果键初始化为假，`static_branch_inc()` 将使分支变为真。接着的 `static_branch_dec()` 将再次使分支变为假。

状态和引用计数可以通过 `static_key_enabled()` 和 `static_key_count()` 获取。通常，如果您使用这些函数，它们应该通过与使能/禁用或增加/减少功能相同的互斥锁保护。

注意，切换分支会导致某些锁被获取，特别是CPU热插拔锁（为了避免在内核修补期间CPU被引入内核时发生竞争）。因此，在热插拔通知器内部调用静态键API将导致死锁。为了仍然允许使用此功能，提供了以下函数：

```c
static_key_enable_cpuslocked()
static_key_disable_cpuslocked()
static_branch_enable_cpuslocked()
static_branch_disable_cpuslocked()
```

这些函数不是通用的，只有在确实知道处于上述上下文并且没有其他情况下才能使用。

当需要一组键时，可以定义为：

```c
DEFINE_STATIC_KEY_ARRAY_TRUE(keys, count);
```

或者：

```c
DEFINE_STATIC_KEY_ARRAY_FALSE(keys, count);
```

### 架构级代码修补接口：跳转标签

为了利用这种优化，架构必须实现一些函数和宏。如果没有架构支持，则会退回到传统的加载、测试和跳转序列。此外，`struct jump_entry` 表必须至少对齐4字节，因为 `static_key->entry` 字段使用了最低两位。

* 选择 `HAVE_ARCH_JUMP_LABEL`，见：`arch/x86/Kconfig`
* 定义 `JUMP_LABEL_NOP_SIZE`，见：`arch/x86/include/asm/jump_label.h`
* `__always_inline bool arch_static_branch(struct static_key *key, bool branch)`，见：`arch/x86/include/asm/jump_label.h`
* `__always_inline bool arch_static_branch_jump(struct static_key *key, bool branch)`，见：`arch/x86/include/asm/jump_label.h`
* `void arch_jump_label_transform(struct jump_entry *entry, enum jump_label_type type)`，见：`arch/x86/kernel/jump_label.c`
* `struct jump_entry`，见：`arch/x86/include/asm/jump_label.h`

### 静态键/跳转标签分析结果（x86_64）

作为示例，让我们向 `getppid()` 添加以下分支，使得系统调用现在看起来像这样：

```c
SYSCALL_DEFINE0(getppid)
{
        int pid;

        if (static_branch_unlikely(&key))
                printk("I am the true branch\n");

        rcu_read_lock();
        pid = task_tgid_vnr(rcu_dereference(current->real_parent));
        rcu_read_unlock();

        return pid;
}
```

生成的GCC指令带有跳转标签如下：

```assembly
fffffff81044290 <sys_getppid>:
fffffff81044290:       55                      push   %rbp
fffffff81044291:       48 89 e5                mov    %rsp,%rbp
fffffff81044294:       e9 00 00 00 00          jmpq   ffffffff81044299 <sys_getppid+0x9>
fffffff81044299:       65 48 8b 04 25 c0 b6    mov    %gs:0xb6c0,%rax
fffffff810442a0:       00 00
fffffff810442a2:       48 8b 80 80 02 00 00    mov    0x280(%rax),%rax
fffffff810442a9:       48 8b 80 b0 02 00 00    mov    0x2b0(%rax),%rax
fffffff810442b0:       48 8b b8 e8 02 00 00    mov    0x2e8(%rax),%rdi
fffffff810442b7:       e8 f4 d9 00 00          callq  ffffffff81051cb0 <pid_vnr>
fffffff810442bc:       5d                      pop    %rbp
fffffff810442bd:       48 98                   cltq
fffffff810442bf:       c3                      retq
fffffff810442c0:       48 c7 c7 e3 54 98 81    mov    $0xffffffff819854e3,%rdi
fffffff810442c7:       31 c0                   xor    %eax,%eax
fffffff810442c9:       e8 71 13 6d 00          callq  ffffffff8171563f <printk>
fffffff810442ce:       eb c9                   jmp    ffffffff81044299 <sys_getppid+0x9>
```

不使用跳转标签优化的情况如下：

```assembly
fffffff810441f0 <sys_getppid>:
fffffff810441f0:       8b 05 8a 52 d8 00       mov    0xd8528a(%rip),%eax        # ffffffff81dc9480 <key>
fffffff810441f6:       55                      push   %rbp
fffffff810441f7:       48 89 e5                mov    %rsp,%rbp
fffffff810441fa:       85 c0                   test   %eax,%eax
fffffff810441fc:       75 27                   jne    ffffffff81044225 <sys_getppid+0x35>
fffffff810441fe:       65 48 8b 04 25 c0 b6    mov    %gs:0xb6c0,%rax
fffffff81044205:       00 00
fffffff81044207:       48 8b 80 80 02 00 00    mov    0x280(%rax),%rax
fffffff8104420e:       48 8b 80 b0 02 00 00    mov    0x2b0(%rax),%rax
fffffff81044215:       48 8b b8 e8 02 00 00    mov    0x2e8(%rax),%rdi
fffffff8104421c:       e8 2f da 00 00          callq  ffffffff81051c50 <pid_vnr>
fffffff81044221:       5d                      pop    %rbp
fffffff81044222:       48 98                   cltq
fffffff81044224:       c3                      retq
fffffff81044225:       48 c7 c7 13 53 98 81    mov    $0xffffffff81985313,%rdi
fffffff8104422c:       31 c0                   xor    %eax,%eax
fffffff8104422e:       e8 60 0f 6d 00          callq  ffffffff81715193 <printk>
fffffff81044233:       eb c9                   jmp    ffffffff810441fe <sys_getppid+0xe>
fffffff81044235:       66 66 2e 0f 1f 84 00    data32 nopw %cs:0x0(%rax,%rax,1)
fffffff8104423c:       00 00 00 00
```

因此，禁用跳转标签的情况增加了 `mov`、`test` 和 `jne` 指令，而跳转标签情况仅有一个 `no-op` 或 `jmp 0`。`jmp 0` 在启动时被修补为5字节的原子 `no-op` 指令。因此，禁用跳转标签的情况增加了：

```c
6 (mov) + 2 (test) + 2 (jne) = 10 - 5 (5字节jmp 0) = 5个额外字节
```

如果包括填充字节，跳转标签代码节省了总共16个字节的指令内存。在这种情况下，非跳转标签函数为80字节长。因此，我们节省了20%的指令占用空间。实际上，我们可以进一步改进这一点，因为5字节的 `no-op` 真正可以是一个2字节的 `no-op`，因为我们可以通过2字节的 `jmp` 到达分支。然而，我们还没有实现最优的 `no-op` 大小（目前是硬编码的）。
由于调度路径中存在多个静态密钥API的使用，`pipe-test`（也称为`perf bench sched pipe`）可以用来展示性能改进。在3.3.0-rc2上进行的测试：

跳转标签禁用的情况下：

```plaintext
Performance counter stats for 'bash -c /tmp/pipe-test' (50次运行)：

        855.700314 任务时钟                # 0.534 CPU利用率               (± 0.11%)
           200,003 上下文切换              # 0.234 M/秒                     (± 0.00%)
                 0 CPU迁移                  # 0.000 M/秒                     (± 39.58%)
               487 页面错误                # 0.001 M/秒                     (± 0.02%)
     1,474,374,262 周期                    # 1.723 GHz                      (± 0.17%)
   <不支持> 前端停滞周期
   <不支持> 后端停滞周期
     1,178,049,567 指令                    # 0.80 每周期指令数              (± 0.06%)
       208,368,926 分支                    # 243.507 M/秒                   (± 0.06%)
         5,569,188 分支错误                # 2.67% 的所有分支               (± 0.54%)

       1.601607384 秒时间流逝                                         (± 0.07%)
```

跳转标签启用的情况下：

```plaintext
Performance counter stats for 'bash -c /tmp/pipe-test' (50次运行)：

        841.043185 任务时钟                # 0.533 CPU利用率               (± 0.12%)
           200,004 上下文切换              # 0.238 M/秒                     (± 0.00%)
                 0 CPU迁移                  # 0.000 M/秒                     (± 40.87%)
               487 页面错误                # 0.001 M/秒                     (± 0.05%)
     1,432,559,428 周期                    # 1.703 GHz                      (± 0.18%)
   <不支持> 前端停滞周期
   <不支持> 后端停滞周期
     1,175,363,994 指令                    # 0.82 每周期指令数              (± 0.04%)
       206,859,359 分支                    # 245.956 M/秒                   (± 0.04%)
         4,884,119 分支错误                # 2.36% 的所有分支               (± 0.85%)

       1.579384366 秒时间流逝
```

分支减少的比例为0.7%，而“分支错误”减少了12%。这是预期中最能节省的部分，因为这种优化是关于减少分支数量的。此外，指令减少了0.2%，周期减少了2.8%，总时间减少了1.4%。
