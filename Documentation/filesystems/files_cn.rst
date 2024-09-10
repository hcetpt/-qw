SPDX 许可证标识符: GPL-2.0

===================================
Linux 内核中的文件管理
===================================

本文档描述了文件（struct file）和文件描述符表（struct files）的锁定机制。
直到 2.6.12 版本，文件描述符表一直由一个锁（files->file_lock）和一个引用计数（files->count）保护。`file_lock` 保护对表中所有与文件相关的字段的访问。`count` 用于在使用 CLONE_FILES 标志克隆的任务之间共享文件描述符表。通常情况下，这适用于 POSIX 线程。与内核中常见的引用计数模型一样，最后一个执行 `put_files_struct()` 的任务会释放文件描述符（fd）表。文件（struct file）本身通过引用计数（->f_count）进行保护。

在新的无锁文件描述符管理模型中，引用计数类似，但锁定基于 RCU（Read-Copy-Update）。文件描述符表包含多个元素——文件描述符集（open_fds 和 close_on_exec）、文件指针数组、集合和数组的大小等。为了使更新对无锁读取器看起来是原子的，文件描述符表的所有元素都位于一个单独的结构体中——`struct fdtable`。`files_struct` 通过一个指向 `struct fdtable` 的指针来访问实际的文件描述符表。最初，`fdtable` 是嵌入在 `files_struct` 中的。在随后扩展 `fdtable` 时，会分配一个新的 `fdtable` 结构，并且 `files->fdtab` 指向新结构。`fdtable` 结构通过 RCU 进行释放，无锁读取器要么看到旧的 `fdtable`，要么看到新的 `fdtable`，从而使更新看起来是原子的。以下是 `fdtable` 结构的锁定规则：

1. 所有对 `fdtable` 的引用必须通过 `files_fdtable()` 宏进行：
   
   ```c
   struct fdtable *fdt;

   rcu_read_lock();

   fdt = files_fdtable(files);
   ...
   if (n <= fdt->max_fds)
       ...
   ..
   rcu_read_unlock();
   ```

   `files_fdtable()` 使用 `rcu_dereference()` 宏，该宏处理无锁引用所需的内存屏障要求。
   `fdtable` 指针必须在读取侧临界区内读取。
2. 如上所述，读取 fdtable 必须通过 rcu_read_lock()/rcu_read_unlock() 进行保护。
3. 对于任何对 fd 表的更新，必须持有 files->file_lock。
4. 要根据文件描述符（fd）查找文件结构，读者必须使用 lookup_fdget_rcu() 或 files_lookup_fdget_rcu() API。这些 API 会处理无锁查找所带来的屏障要求。
示例：

```c
struct file *file;

rcu_read_lock();
file = lookup_fdget_rcu(fd);
rcu_read_unlock();
if (file) {
    ..
    fput(file);
}
...
```
5. 由于 fdtable 和文件结构都可以无锁地查找，因此必须使用 rcu_assign_pointer() API 安装它们。如果无锁地查找它们，则必须使用 rcu_dereference()。然而，建议使用 files_fdtable() 和 lookup_fdget_rcu()/files_lookup_fdget_rcu()，这些 API 会处理这些问题。
6. 在更新时，必须在持有 files->file_lock 的情况下查找 fdtable 指针。如果释放了 ->file_lock，则另一个线程可能会扩展 files，从而创建一个新的 fdtable，并使之前的 fdtable 指针失效。
例如：

```c
spin_lock(&files->file_lock);
fd = locate_fd(files, file, start);
if (fd >= 0) {
    /* locate_fd() 可能会扩展 fdtable，加载指针 */
    fdt = files_fdtable(files);
    __set_open_fd(fd, fdt);
    __clear_close_on_exec(fd, fdt);
    spin_unlock(&files->file_lock);
} ...
```
由于 locate_fd() 可以释放 ->file_lock（并重新获取 ->file_lock），因此必须在调用 locate_fd() 后加载 fdtable 指针（fdt）。

在较新的内核中，基于 RCU 的文件查找已改为依赖 SLAB_TYPESAFE_BY_RCU 而不是 call_rcu()。仅仅通过 atomic_long_inc_not_zero() 在 RCU 下获取对相关文件的引用已经不够了，因为该文件可能已经被回收，其他人可能已经增加了引用计数。换句话说，调用者可能会看到来自新用户的引用计数增加。因此，有必要验证引用计数增加前后指针是否相同。这种模式可以在 get_file_rcu() 和 __files_get_rcu() 中看到。
此外，在没有首先通过 RCU 查找获取引用的情况下，无法访问或检查文件结构中的字段。不这样做一直以来都是很不可靠的，并且仅适用于文件结构中的非指针数据。有了 SLAB_TYPESAFE_BY_RCU 机制，调用者必须要么首先获取一个引用，要么持有 fdtable 的 files_lock。
