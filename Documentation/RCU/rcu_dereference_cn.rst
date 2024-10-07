```
RCU_DEREFERENCE() 返回值的正确使用和维护
===============================================================

正确地处理地址和数据依赖性对于正确使用诸如 RCU 等技术至关重要。为此，从 rcu_dereference() 家族函数返回的指针携带地址和数据依赖性。这些依赖性从 rcu_dereference() 宏加载指针一直延伸到后续使用该指针来计算后续内存访问的地址（表示地址依赖性）或由后续内存访问写入的值（表示数据依赖性）。

大多数情况下，这些依赖性会被保留下来，使您能够自由地使用来自 rcu_dereference() 的值。例如，解引用（前缀 "*"）、字段选择（"->"）、赋值（"="）、取地址（"&"）、类型转换以及常量加减运算都可以自然且安全地工作。然而，由于当前编译器不考虑地址或数据依赖性，因此仍然有可能出现问题。

遵循以下规则以保持从 rcu_dereference() 及其相关函数调用中发出的地址和数据依赖性，从而确保您的 RCU 读取器正常工作：

- 您必须使用 rcu_dereference() 家族中的一个原语来加载一个受 RCU 保护的指针，否则 CONFIG_PROVE_RCU 将会抱怨。更糟糕的是，您的代码可能会出现随机内存损坏的错误，因为编译器和 DEC Alpha 可能会玩一些游戏。
  - 如果没有 rcu_dereference() 原语，编译器可能会重新加载值，这会让您的代码在同一个指针上有两个不同的值！没有 rcu_dereference()，DEC Alpha 可能会加载一个指针，解引用该指针，并返回先于指针存储之前的数据。（如后文所述，在最近的内核版本中，READ_ONCE() 同样可以防止 DEC Alpha 进行这些操作。）
  - 此外，rcu_dereference() 中的 volatile 类型转换阻止了编译器推断结果指针值。请参阅“编译器知道太多”的示例部分，了解编译器确实可以推断出指针的确切值，从而导致乱序问题。

- 在特殊情况下，如果数据被添加但从未在读者访问结构时被移除，则可以使用 READ_ONCE() 而不是 rcu_dereference()。在这种情况下，使用 READ_ONCE() 扮演了在 v4.15 版本中被移除的 lockless_dereference() 原语的角色。

- 您只允许对指针值使用 rcu_dereference()。
  编译器对整数值了解得太多，无法信任它通过整数操作传递依赖性。
  有极少数例外情况，即您可以暂时将指针转换为 uintptr_t，以便：
    - 设置或清除该指针低阶必须为零位上的位。这显然意味着指针必须有对齐约束，例如，这通常不适用于 char* 指针。
    - 使用 XOR 位来转换指针，如某些经典伙伴分配算法中所做的那样。
  在对其执行其他任何操作之前，重要的是要将值转换回指针类型。
```
- 避免在使用 "+" 和 "-" 内置算术运算符时引发取消操作。例如，对于给定的变量 "x"，避免使用 "(x - (uintptr_t)x)" 来处理 `char*` 类型的指针。编译器有权将此类表达式替换为零，从而使后续访问不再依赖于 `rcu_dereference()`，这可能导致由于重排序错误而产生的bug。

当然，如果 "p" 是从 `rcu_dereference()` 获取的指针，并且 "a" 和 "b" 是恰好相等的整数，则表达式 "p + a - b" 是安全的，因为其值仍然必然依赖于 `rcu_dereference()`，从而保持正确的顺序。

- 如果您使用 RCU 保护即时编译（JIT）的函数，使得 "()" 函数调用运算符应用于从 `rcu_dereference()`（直接或间接地）获取的值，您可能需要直接与硬件交互以刷新指令缓存。这个问题出现在某些系统中，当一个新的 JIT 编译函数使用了之前 JIT 编译函数使用的相同内存时。

- 在进行指针解引用时，不要使用关系运算符（如 "==", "!=", ">", ">=", "<", 或 "<="）的结果。例如，以下代码（非常奇怪）是错误的：

```c
int *p;
int *q;

...
p = rcu_dereference(gp);
q = &global_q;
q += p > &oom_p;
r1 = *q;  /* 错误！*/
```

原因和之前一样，关系运算符通常通过分支进行编译。尽管像 ARM 或 PowerPC 这样的弱内存模型机器会按照这样的分支对存储进行排序，但它们可能会推测加载，这再次可能导致重排序错误。

- 在比较从 `rcu_dereference()` 获取的指针与非空值时要非常小心。正如 Linus Torvalds 所解释的，如果两个指针相等，编译器可以将比较的指针替换为从 `rcu_dereference()` 获取的指针。例如：

```c
p = rcu_dereference(gp);
if (p == &default_struct)
    do_default(p->a);
```

因为编译器现在知道 "p" 的值正好是 "default_struct" 变量的地址，所以它可以将这段代码转换为如下形式：

```c
p = rcu_dereference(gp);
if (p == &default_struct)
    do_default(default_struct.a);
```

在 ARM 和 Power 硬件上，从 "default_struct.a" 的加载现在可以被推测出来，以至于它可能会在 `rcu_dereference()` 之前发生，这可能导致由于重排序错误而产生的bug。

然而，在以下情况下比较是安全的：

- 比较的对象是指向 `NULL` 的指针。如果编译器知道指针是 `NULL`，那么您最好不要去解引用它。如果比较结果不相等，编译器也不会知道更多信息。因此，将 `rcu_dereference()` 获取的指针与 `NULL` 指针进行比较是安全的。
- 比较之后不再对该指针进行解引用
由于没有后续的解引用操作，编译器无法利用从比较中学到的信息来重新排序不存在的后续解引用操作。
这种比较在扫描RCU保护的循环链表时经常发生。

注意，如果指针比较是在RCU读端临界区之外进行的，并且该指针从未被解引用，则应使用`rcu_access_pointer()`代替`rcu_dereference()`。在大多数情况下，最好通过直接测试`rcu_access_pointer()`的返回值来避免意外解引用，而不要将返回值赋给一个变量。

在RCU读端临界区内，几乎没有理由使用`rcu_access_pointer()`。

- 比较的对象是一个指向“很久以前”初始化的内存的指针。之所以这样做是安全的，是因为即使发生了乱序，乱序也不会影响后续的访问。那么，“很久以前”具体是指多久呢？以下是一些可能性：

- 编译时间
- 启动时间
- 对于模块代码，在模块初始化时
- 对于内核线程代码，在kthread创建之前
- 在当前持有的锁之前的某次获取过程中
- 对于定时器处理程序，在调用`mod_timer()`之前

还有许多其他可能性，涉及Linux内核广泛使用的各种会在稍后时间调用代码的原语。
- 被比较的指针也来自 `rcu_dereference()`。在这种情况下，两个指针都依赖于一个或另一个 `rcu_dereference()`，因此无论哪种方式都会得到正确的排序。
也就是说，这种情况可能会使某些 RCU 使用错误更容易发生。这在某种程度上可能是一件好事，至少在测试期间发生时是这样。一个这样的 RCU 使用错误示例将在标题为“放大了的 RCU 使用错误示例”部分中展示。
- 所有比较之后的访问都是存储操作，因此控制依赖性会保持所需的顺序。但请注意，很容易把控制依赖性搞错。请参阅 `Documentation/memory-barriers.txt` 中的“控制依赖性”部分以获取更多详细信息。
- 指针不相等，并且编译器没有足够的信息来推断指针的值。请注意，`rcu_dereference()` 中的 `volatile` 铸造通常会阻止编译器了解太多信息。然而，请注意，如果编译器知道指针只取两个值中的一个，那么不等比较将提供编译器所需的信息来推断指针的值。
- 禁用编译器提供的任何值推测优化，特别是如果您正在使用基于反馈的优化，这些优化会利用先前运行中收集的数据。这种值推测优化按设计重新排序操作。这里有一个例外：在强序系统（如 x86）上，利用分支预测硬件的值推测优化是安全的，但在弱序系统（如 ARM 或 Power）上则不是。明智地选择您的编译器命令行选项！

**放大了的 RCU 使用错误示例**
----------------------------------

由于更新者可以与 RCU 读取者并发运行，RCU 读取者可能会看到过时和/或不一致的值。如果 RCU 读取者需要新鲜或一致的值，有时确实如此，他们需要采取适当的预防措施。为了理解这一点，考虑以下代码片段：

```c
struct foo {
    int a;
    int b;
    int c;
};
struct foo *gp1;
struct foo *gp2;

void updater(void)
{
    struct foo *p;

    p = kmalloc(...);
    if (p == NULL)
        deal_with_it();
    p->a = 42;  /* 每个字段都在自己的缓存行中。 */
    p->b = 43;
    p->c = 44;
    rcu_assign_pointer(gp1, p);
    p->b = 143;
    p->c = 144;
    rcu_assign_pointer(gp2, p);
}

void reader(void)
{
    struct foo *p;
    struct foo *q;
    int r1, r2;

    rcu_read_lock();
    p = rcu_dereference(gp2);
    if (p == NULL)
        return;
    r1 = p->b;  /* 保证获取到 143。 */
    q = rcu_dereference(gp1);  /* 保证非空。 */
    if (p == q) {
        /* 编译器决定 q->c 与 p->c 相同。 */
        r2 = p->c; /* 在弱序系统上可能会获取到 44。 */
    } else {
        r2 = p->c - r1; /* 无条件访问 p->c。 */
    }
    rcu_read_unlock();
    do_something_with(r1, r2);
}
```

您可能会惊讶于结果（r1 == 143 && r2 == 44）是可能的，但您不应该感到惊讶。毕竟，更新者可能在 `reader()` 加载到 `r1` 和加载到 `r2` 之间被调用了一次。即使由于编译器和 CPU 的重新排序导致相同的结果发生也是次要的。但如果读取者需要一致视图怎么办？

一种方法是使用锁定，例如如下所示：

```c
struct foo {
    int a;
    int b;
    int c;
    spinlock_t lock;
};
struct foo *gp1;
struct foo *gp2;

void updater(void)
{
    struct foo *p;

    p = kmalloc(...);
    if (p == NULL)
        deal_with_it();
    spin_lock(&p->lock);
    p->a = 42;  /* 每个字段都在自己的缓存行中。 */
    p->b = 43;
    p->c = 44;
    spin_unlock(&p->lock);
    rcu_assign_pointer(gp1, p);
    spin_lock(&p->lock);
    p->b = 143;
    p->c = 144;
    spin_unlock(&p->lock);
    rcu_assign_pointer(gp2, p);
}

void reader(void)
{
    struct foo *p;
    struct foo *q;
    int r1, r2;

    rcu_read_lock();
    p = rcu_dereference(gp2);
    if (p == NULL)
        return;
    spin_lock(&p->lock);
    r1 = p->b;  /* 保证获取到 143。 */
    q = rcu_dereference(gp1);  /* 保证非空。 */
    if (p == q) {
        /* 编译器决定 q->c 与 p->c 相同。 */
        r2 = p->c; /* 锁定保证 r2 == 144。 */
    } else {
        spin_lock(&q->lock);
        r2 = q->c - r1;
        spin_unlock(&q->lock);
    }
    rcu_read_unlock();
    spin_unlock(&p->lock);
    do_something_with(r1, r2);
}
```

始终使用合适的工具来做这项工作！

**编译器了解过多的情况示例**
-----------------------------------------

如果从 `rcu_dereference()` 获取的指针与另一个指针进行不等比较，编译器通常不知道第一个指针的值。这种缺乏知识阻止了编译器执行可能破坏 RCU 依赖的排序保证的优化。而 `rcu_dereference()` 中的 `volatile` 铸造应该防止编译器猜测指针的值。
但是没有使用 `rcu_dereference()`，编译器知道的可能比你预期的要多。考虑以下代码片段：

```c
struct foo {
    int a;
    int b;
};
static struct foo variable1;
static struct foo variable2;
static struct foo *gp = &variable1;

void updater(void)
{
    initialize_foo(&variable2);
    rcu_assign_pointer(gp, &variable2);
    /*
     * 上面是对 gp 的唯一一次赋值，在这个翻译单元中，并且 gp 的地址以任何方式都没有被导出。
     */
}

int reader(void)
{
    struct foo *p;

    p = gp;
    barrier();
    if (p == &variable1)
        return p->a; /* 必须是 variable1.a。 */
    else
        return p->b; /* 必须是 variable2.b。 */
}
```

由于编译器可以看到所有对 "gp" 的赋值，它知道 "gp" 的唯一可能值要么是 "variable1"，要么是 "variable2"。因此，`reader()` 中的比较告诉编译器即使在不等的情况下 "p" 的确切值。这使得编译器能够使返回值独立于从 "gp" 的加载，进而破坏了这个加载和返回值加载之间的顺序。这可能导致在弱序系统上返回 `p->b` 的初始化前的垃圾值。

简而言之，当你打算解引用结果指针时，`rcu_dereference()` 是 *不可选的*。

**你应该使用哪个 `rcu_dereference()` 家族成员？**

--------------------------------------

首先，请避免使用 `rcu_dereference_raw()`，同时也请避免使用带有常量值为 1（或 true）的第二个参数的 `rcu_dereference_check()` 和 `rcu_dereference_protected()`。有了这些警告之后，这里有一些指导来决定在不同情况下使用哪个 `rcu_dereference()` 成员：

1. 如果访问需要在 RCU 读侧临界区中进行，则使用 `rcu_dereference()`。使用新的统一的 RCU 版本，进入 RCU 读侧临界区可以使用 `rcu_read_lock()`、任何禁用下半部的操作、任何禁用中断的操作或任何禁用抢占的操作。请注意，即使在使用 CONFIG_PREEMPT_RT=y 编译的内核中，自旋锁临界区也是隐含的 RCU 读侧临界区。
2. 如果访问可能在一个 RCU 读侧临界区内，或者被（例如）my_lock 保护，则使用 `rcu_dereference_check()`，例如：

   ```c
   p1 = rcu_dereference_check(p->rcu_protected_pointer,
                              lockdep_is_held(&my_lock));
   ```

3. 如果访问可能在一个 RCU 读侧临界区内，或者被 my_lock 或 your_lock 保护，则再次使用 `rcu_dereference_check()`，例如：

   ```c
   p1 = rcu_dereference_check(p->rcu_protected_pointer,
                              lockdep_is_held(&my_lock) ||
                              lockdep_is_held(&your_lock));
   ```

4. 如果访问是在更新侧，因此总是被 my_lock 保护，则使用 `rcu_dereference_protected()`，例如：

   ```c
   p1 = rcu_dereference_protected(p->rcu_protected_pointer,
                                  lockdep_is_held(&my_lock));
   ```

   这可以扩展到处理多个锁，如上面的第 3 点，并且两者都可以扩展来检查其他条件。

5. 如果保护由调用者提供，并且因此未知，则这是 `rcu_dereference_raw()` 适用的罕见情况。此外，当锁依赖表达式过于复杂时，`rcu_dereference_raw()` 也可能是合适的，但更好的方法可能是仔细审查你的同步设计。尽管如此，仍然存在大量的锁或引用计数器中的任何一个足以保护指针的情况，所以 `rcu_dereference_raw()` 有其用处。

然而，它的用处可能比当前内核中使用的次数要少得多。

同样适用于其同义词 `rcu_dereference_check(..., 1)` 及其近亲 `rcu_dereference_protected(..., 1)`。

**稀疏检查 RCU 保护的指针**

------------------------------------------

稀疏静态分析工具会检查非 RCU 访问 RCU 保护的指针，这可能会导致由于编译器优化（涉及虚构的加载以及可能的加载撕裂）而产生的“有趣”错误。
例如，假设有人错误地这样做了：

```c
p = q->rcu_protected_pointer;
do_something_with(p->a);
do_something_else_with(p->b);
```

如果寄存器压力很高，编译器可能会优化掉变量 "p"，将代码转换为如下形式：

```c
do_something_with(q->rcu_protected_pointer->a);
do_something_else_with(q->rcu_protected_pointer->b);
```

如果在此期间 `q->rcu_protected_pointer` 发生了变化，这可能会导致你的代码出错。这不是一个理论上的问题：早在20世纪90年代初，正是这种bug让 Paul E. McKenney（以及他的几位无辜同事）度过了一个三天的周末。

加载撕裂当然也可能导致引用两个指针的混合体，这也可能导致你的代码出错。这些问题本可以通过使代码改为以下形式来避免：

```c
p = rcu_dereference(q->rcu_protected_pointer);
do_something_with(p->a);
do_something_else_with(p->b);
```

不幸的是，这类bug在审查时非常难以发现。这就是 sparse 工具和 `"__rcu"` 标记发挥作用的地方。如果你在结构体中或作为形式参数声明一个指针时加上 `"__rcu"` 标记，这会告诉 sparse 在直接访问该指针时发出警告。它还会在使用 `rcu_dereference()` 及其相关函数访问未标记为 `"__rcu"` 的指针时发出警告。例如，`->rcu_protected_pointer` 可能被声明为如下形式：

```c
struct foo __rcu *rcu_protected_pointer;
```

使用 `"__rcu"` 是可选的。如果你选择不使用它，则应忽略 sparse 的警告。
