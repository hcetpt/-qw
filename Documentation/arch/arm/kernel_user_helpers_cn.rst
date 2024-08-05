============================
内核提供的用户辅助程序
============================

这些是在内核内存固定地址处可从用户空间访问的、由内核提供的用户代码段。这用于向用户空间提供一些操作，因为许多ARM CPU上某些原生特性及/或指令未实现而需要内核的帮助。设想是这段代码直接在用户模式下执行以获得最佳效率，但又与内核部分过于紧密而不能留给用户库处理。实际上，这段代码可能会根据可用的指令集或者是否为SMP系统从一个CPU到另一个CPU有所不同。换句话说，内核有权在不事先通知的情况下按需更改此代码。只有此处文档中描述的入口点及其结果保证稳定。
这不同于（但不排除）完整的VDSO实现，然而VDSO会阻止一些常量的汇编技巧，这些技巧允许高效地分支到那些代码段。由于这些代码段仅使用几个周期就返回用户代码，因此通过VDSO间接远调用产生的开销将对这些极简操作产生可测量的开销。
当针对足够新的处理器优化时，用户空间应该绕过这些辅助程序并将这些功能内联实现（无论是直接由编译器生成的代码还是库调用实现的一部分），前提是生成的二进制文件已经由于使用类似的原生指令进行其他操作而不兼容早期的ARM处理器。换句话说，不要仅仅为了不使用这些内核辅助程序而使二进制文件无法在早期处理器上运行，除非你的编译代码不会为其他目的使用新指令。
随着时间推移可能会添加新的辅助程序，因此较旧的内核可能缺少较新内核中的一些辅助程序。出于这个原因，程序必须检查__kuser_helper_version的值（见下文），然后才能假定安全调用任何特定的辅助程序。理想情况下，此检查应在进程启动时仅执行一次，并且如果所运行进程的内核版本没有提供所需的辅助程序，则应提前终止执行。

kuser_helper_version
--------------------

位置：0xffff0ffc

参考声明：

  extern int32_t __kuser_helper_version;

定义：

  此字段包含运行内核实现的辅助程序数量。用户空间可以读取此值来确定某个特定辅助程序的可用性。
使用示例：

  #define __kuser_helper_version (*(int32_t *)0xffff0ffc)

  void check_kuser_version(void)
  {
	if (__kuser_helper_version < 2) {
		fprintf(stderr, "无法执行原子操作，内核版本太旧\n");
		abort();
	}
  }

注释：

  用户空间可以假设此字段的值在整个单一进程生命周期中从不改变。这意味着此字段可以在库初始化或程序启动阶段只读取一次。

kuser_get_tls
-------------

位置：0xffff0fe0

参考原型：

  void * __kuser_get_tls(void);

输入：

  lr = 返回地址

输出：

  r0 = TLS 值

被破坏寄存器：

  无

定义：

  获取之前通过__ARM_NR_set_tls系统调用设置的TLS值
使用示例：

  typedef void * (__kuser_get_tls_t)(void);
  #define __kuser_get_tls (*(__kuser_get_tls_t *)0xffff0fe0)

  void foo()
  {
	void *tls = __kuser_get_tls();
	printf("TLS = %p\n", tls);
  }

注释：

  - 仅当__kuser_helper_version >= 1时有效（自内核版本2.6.12起）

kuser_cmpxchg
-------------

位置：0xffff0fc0

参考原型：

  int __kuser_cmpxchg(int32_t oldval, int32_t newval, volatile int32_t *ptr);

输入：

  r0 = oldval
  r1 = newval
  r2 = ptr
  lr = 返回地址

输出：

  r0 = 成功代码（零或非零）
  C 标志位 = 设置如果r0 == 0，清除如果r0 != 0

被破坏寄存器：

  r3, ip, 标志位

定义：

  如果`*ptr`等于oldval，则仅原子地在`*ptr`中存储newval
### Translation into Simplified Chinese:

#### `__kuser_cmpxchg`:
如果 `*ptr` 被更改，则返回零；如果没有发生交换，则返回非零值。
C 标志也会在 `*ptr` 被更改时设置，以便调用代码中的汇编优化。

**使用示例**:

```c
typedef int (__kuser_cmpxchg_t)(int oldval, int newval, volatile int *ptr);
#define __kuser_cmpxchg (*(__kuser_cmpxchg_t *)0xffff0fc0)

int atomic_add(volatile int *ptr, int val)
{
   int old, new;

   do {
      old = *ptr;
      new = old + val;
   } while (__kuser_cmpxchg(old, new, ptr));

   return new;
}
```

**注释**:
- 该例程已经包含了所需的内存屏障。
- 只有当 `__kuser_helper_version` 大于等于 2 时有效（从内核版本 2.6.12 开始）。

#### `kuser_memory_barrier`:
**位置**: 0xffff0fa0

**参考原型**:

```c
void __kuser_memory_barrier(void);
```

**输入**:
- lr = 返回地址

**输出**:
- 无

**破坏的寄存器**:
- 无

**定义**:
应用任何所需的内存屏障以保持与手动修改的数据和 `__kuser_cmpxchg` 使用情况的一致性。

**使用示例**:

```c
typedef void (__kuser_dmb_t)(void);
#define __kuser_dmb (*(__kuser_dmb_t *)0xffff0fa0)
```

**注释**:
- 只有当 `__kuser_helper_version` 大于等于 3 时有效（从内核版本 2.6.15 开始）。

#### `kuser_cmpxchg64`:
**位置**: 0xffff0f60

**参考原型**:

```c
int __kuser_cmpxchg64(const int64_t *oldval,
                      const int64_t *newval,
                      volatile int64_t *ptr);
```

**输入**:
- r0 = 指向旧值的指针
- r1 = 指向新值的指针
- r2 = 指向目标值的指针
- lr = 返回地址

**输出**:
- r0 = 成功码（零或非零）
- C 标志 = 如果 r0 == 0 则设置，否则清除

**破坏的寄存器**:
- r3, lr, 标志

**定义**:
仅当 `*ptr` 等于由 `*oldval` 指向的 64 位值时，原子地将由 `*newval` 指向的 64 位值存储到 `*ptr` 中。如果 `*ptr` 被更改，则返回零；如果没有发生交换，则返回非零值。
C 标志也会在 `*ptr` 被更改时设置，以便调用代码中的汇编优化。

**使用示例**:

```c
typedef int (__kuser_cmpxchg64_t)(const int64_t *oldval,
                                  const int64_t *newval,
                                  volatile int64_t *ptr);
#define __kuser_cmpxchg64 (*(__kuser_cmpxchg64_t *)0xffff0f60)

int64_t atomic_add64(volatile int64_t *ptr, int64_t val)
{
   int64_t old, new;

   do {
      old = *ptr;
      new = old + val;
   } while (__kuser_cmpxchg64(&old, &new, ptr));

   return new;
}
```

**注释**:
- 该例程已经包含了所需的内存屏障。
- 由于这个序列较长，它跨越了两个传统的 kuser “槽”，因此 0xffff0f80 不被用作有效的入口点。
仅在 __kuser_helper_version >= 5 时有效（从内核版本 3.1 开始）
