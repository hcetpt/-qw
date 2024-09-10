```
SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

=======
DebugFS
=======

版权所有 |copy| 2009 Jonathan Corbet <corbet@lwn.net>

Debugfs 存在的目的是为内核开发者提供一种简单的方法，使信息能够传递到用户空间。与 /proc（仅用于进程信息）或 sysfs（具有严格的每文件一个值的规定）不同，debugfs 没有任何规则。开发者可以将他们想要的任何信息放在这里。debugfs 文件系统也不打算作为用户空间的稳定 ABI；理论上，在这里导出的文件没有任何稳定性约束。然而，在现实世界中情况并不总是那么简单[1]_，即使是 debugfs 接口也最好设计成需要永久维护的形式。
debugfs 通常通过如下命令进行挂载：

    mount -t debugfs none /sys/kernel/debug

（或者等效的 /etc/fstab 配置行）
默认情况下，只有 root 用户可以访问 debugfs 的根目录。要更改对该树的访问权限，可以使用 "uid"、"gid" 和 "mode" 挂载选项。
请注意，debugfs API 只对模块开放 GPL 许可证。
使用 debugfs 的代码应该包含 <linux/debugfs.h>。然后，首先需要创建至少一个目录来存放一组 debugfs 文件：

    struct dentry *debugfs_create_dir(const char *name, struct dentry *parent);

如果成功，此调用将在指定父目录下创建一个名为 name 的目录。如果 parent 是 NULL，则该目录将在 debugfs 根目录下创建。成功时返回值是一个指向创建目录的 dentry 结构体指针，可以用它来在目录中创建文件（以及最后清理）。如果返回值是 ERR_PTR(-ERROR)，则表示出现了问题。如果返回值是 ERR_PTR(-ENODEV)，则表明内核没有支持 debugfs，下面描述的所有函数都不会工作。
在 debugfs 目录中创建文件最通用的方式是使用：

    struct dentry *debugfs_create_file(const char *name, umode_t mode,
				       struct dentry *parent, void *data,
				       const struct file_operations *fops);

这里的 name 是要创建的文件名，mode 描述了文件应具有的访问权限，parent 表示持有该文件的目录，data 将被存储在生成的 inode 结构体的 i_private 字段中，而 fops 是实现文件行为的一组文件操作。至少应该提供 read() 和/或 write() 操作；其他操作可以根据需要包括。再次强调，返回值将是创建文件的 dentry 指针，错误时返回 ERR_PTR(-ERROR)，如果缺少 debugfs 支持则返回 ERR_PTR(-ENODEV)。
若要创建具有初始大小的文件，可以使用以下函数：

    void debugfs_create_file_size(const char *name, umode_t mode,
				  struct dentry *parent, void *data,
				  const struct file_operations *fops,
				  loff_t file_size);

file_size 是文件的初始大小。其他参数与 debugfs_create_file 函数相同。
在许多情况下，实际上不需要创建一组文件操作；debugfs 代码为简单的情况提供了许多辅助函数。包含单个整数值的文件可以通过以下任何一个函数创建：

    void debugfs_create_u8(const char *name, umode_t mode,
			   struct dentry *parent, u8 *value);
    void debugfs_create_u16(const char *name, umode_t mode,
			    struct dentry *parent, u16 *value);
    void debugfs_create_u32(const char *name, umode_t mode,
			    struct dentry *parent, u32 *value);
    void debugfs_create_u64(const char *name, umode_t mode,
			    struct dentry *parent, u64 *value);

这些文件支持读取和写入给定值；如果某个特定文件不应被写入，只需相应设置模式位即可。这些文件中的值以十进制表示；如果十六进制更合适，则可以使用以下函数代替：

    void debugfs_create_x8(const char *name, umode_t mode,
			   struct dentry *parent, u8 *value);
    void debugfs_create_x16(const char *name, umode_t mode,
			    struct dentry *parent, u16 *value);
    void debugfs_create_x32(const char *name, umode_t mode,
			    struct dentry *parent, u32 *value);
    void debugfs_create_x64(const char *name, umode_t mode,
			    struct dentry *parent, u64 *value);

只要开发者知道要导出的值的大小，这些函数都是有用的。但是，某些类型在不同架构上可能有不同的宽度，这使得情况变得有些复杂。有一些函数旨在帮助处理这种特殊情况：

    void debugfs_create_size_t(const char *name, umode_t mode,
			       struct dentry *parent, size_t *value);

如预期的那样，此函数将创建一个代表类型为 size_t 的变量的 debugfs 文件。
类似地，对于十进制和十六进制的类型为 unsigned long 的变量也有辅助函数：

    struct dentry *debugfs_create_ulong(const char *name, umode_t mode,
					struct dentry *parent,
					unsigned long *value);
    void debugfs_create_xul(const char *name, umode_t mode,
			    struct dentry *parent, unsigned long *value);

布尔值可以使用以下函数放置在 debugfs 中：

    void debugfs_create_bool(const char *name, umode_t mode,
                             struct dentry *parent, bool *value);

对生成文件的读取将返回 Y（对于非零值）或 N，后面跟着一个换行符。如果写入该文件，它可以接受大写或小写字母，或者 1 或 0。任何其他输入都会被默默地忽略。
同样，atomic_t 值也可以使用以下函数放置在 debugfs 中：

    void debugfs_create_atomic_t(const char *name, umode_t mode,
				 struct dentry *parent, atomic_t *value)

读取此文件会获取 atomic_t 值，写入此文件会设置 atomic_t 值。
```
另一个选项是导出一段任意的二进制数据块，其结构和功能如下：

    struct debugfs_blob_wrapper {
	void *data;
	unsigned long size;
    };

    struct dentry *debugfs_create_blob(const char *name, umode_t mode,
				       struct dentry *parent,
				       struct debugfs_blob_wrapper *blob);

读取该文件将返回 `debugfs_blob_wrapper` 结构所指向的数据。一些驱动程序使用“blobs”作为返回多行（静态）格式化文本输出的简单方式。此函数可以用于导出二进制信息，但在主线代码中似乎没有相关实现。请注意，所有使用 `debugfs_create_blob()` 创建的文件都是只读的。
如果你想在调试过程中转储寄存器块（这在开发过程中非常常见，尽管很少有相关代码进入主线），debugfs 提供了两个函数：一个用于创建仅包含寄存器的文件，另一个用于将寄存器块插入到另一个顺序文件中：

    struct debugfs_reg32 {
	char *name;
	unsigned long offset;
    };

    struct debugfs_regset32 {
	const struct debugfs_reg32 *regs;
	int nregs;
	void __iomem *base;
	struct device *dev;     /* 可选设备用于运行时电源管理 */
    };

    debugfs_create_regset32(const char *name, umode_t mode,
			    struct dentry *parent,
			    struct debugfs_regset32 *regset);

    void debugfs_print_regs32(struct seq_file *s, const struct debugfs_reg32 *regs,
			 int nregs, void __iomem *base, char *prefix);

“base” 参数可以为0，但你可能希望使用 `__stringify` 构建 `reg32` 数组，并且许多寄存器名称（宏）实际上是相对于寄存器块基地址的字节偏移量。
如果你想在 debugfs 中转储一个 `u32` 数组，你可以创建一个文件：

    struct debugfs_u32_array {
	u32 *array;
	u32 n_elements;
    };

    void debugfs_create_u32_array(const char *name, umode_t mode,
			struct dentry *parent,
			struct debugfs_u32_array *array);

“array” 参数包装了一个指向数组数据的指针及其元素数量。注意：一旦数组创建后，其大小不能更改。
有一个辅助函数用于创建与设备相关的 `seq_file`：

   void debugfs_create_devm_seqfile(struct device *dev,
				const char *name,
				struct dentry *parent,
				int (*read_fn)(struct seq_file *s,
					void *data));

“dev” 参数是与此 debugfs 文件相关的设备，“read_fn” 是一个函数指针，用于打印 `seq_file` 的内容。
还有一些其他目录相关的辅助函数：

    struct dentry *debugfs_rename(struct dentry *old_dir,
    				  struct dentry *old_dentry,
		                  struct dentry *new_dir,
				  const char *new_name);

    struct dentry *debugfs_create_symlink(const char *name,
                                          struct dentry *parent,
				      	  const char *target);

调用 `debugfs_rename()` 将给现有的 debugfs 文件一个新的名字，可能是在不同的目录中。新的名字在调用前必须不存在；返回值是更新后的 `old_dentry`。
符号链接可以通过 `debugfs_create_symlink()` 创建。

所有 debugfs 用户必须考虑一个重要问题：debugfs 中创建的任何目录都没有自动清理机制。如果模块卸载时不显式地删除 debugfs 条目，结果将是大量无效指针和极其不友好的行为。
因此，所有 debugfs 用户——至少那些可以作为模块构建的用户——必须准备好删除他们在 debugfs 中创建的所有文件和目录。文件可以通过以下方式删除：

    void debugfs_remove(struct dentry *dentry);

`dentry` 值可以为 NULL 或错误值，在这种情况下不会删除任何内容。
曾经，debugfs 用户需要记住他们创建的每个 debugfs 文件的 `dentry` 指针以便清理所有文件。但现在我们生活在更加文明的时代，debugfs 用户可以调用：

    void debugfs_remove_recursive(struct dentry *dentry);

如果此函数传递的是顶级目录对应的 `dentry` 指针，则该目录下的整个层次结构将被删除。
.. [1] http://lwn.net/Articles/309298/
