### SPDX 许可证标识符：GPL-2.0

#### V4L2 文件句柄处理器
--------------

`struct v4l2_fh` 提供了一种简单的方法来维护由 V4L2 框架使用的文件句柄特定数据。
**请注意：**
新驱动程序必须使用 `struct v4l2_fh`，
因为它还被用来实现优先级处理（参见 :ref:`VIDIOC_G_PRIORITY`）。

V4L2 框架中的 `v4l2_fh` 的使用者（不是驱动程序）可以通过测试 `video_device`->flags 中的 `V4L2_FL_USES_V4L2_FH` 位来判断一个驱动程序是否使用 `v4l2_fh` 作为其 `file->private_data` 指针。当调用 `v4l2_fh_init` 时，该位会被设置。

`struct v4l2_fh` 作为驱动程序自定义文件句柄结构的一部分进行分配，并且在驱动程序的 `open()` 函数中通过将 `file->private_data` 设置为指向它来初始化。

在很多情况下，`struct v4l2_fh` 会嵌入到一个更大的结构体中。在这种情况下，你应该按以下步骤操作：

1. 在 `open()` 函数中调用 `v4l2_fh_init` 和 `v4l2_fh_add`。
2. 在 `release()` 函数中调用 `v4l2_fh_del` 和 `v4l2_fh_exit`。

驱动程序可以使用 `container_of` 宏来提取它们自己的文件句柄结构。
示例：

```c
struct my_fh {
    int blah;
    struct v4l2_fh fh;
};

// ...

int my_open(struct file *file)
{
    struct my_fh *my_fh;
    struct video_device *vfd;
    int ret;

    // ...

    my_fh = kzalloc(sizeof(*my_fh), GFP_KERNEL);

    // ...

    v4l2_fh_init(&my_fh->fh, vfd);

    // ...
}
```
下面是代码和描述的中文翻译：

```c
// 在打开文件时初始化私有数据，并将文件句柄添加到视频设备的文件句柄列表中
static int my_open(struct file *file) {
    file->private_data = &my_fh->fh; // 将自定义结构体中的文件句柄指针赋值给 file 的 private_data 成员
    v4l2_fh_add(&my_fh->fh); // 将文件句柄添加到 video_device 的文件句柄列表中
    return 0;
}

// 在关闭文件时释放资源并清理文件句柄
static int my_release(struct file *file) {
    struct v4l2_fh *fh = file->private_data; // 从 file 结构体获取 v4l2_fh 指针
    struct my_fh *my_fh = container_of(fh, struct my_fh, fh); // 通过 v4l2_fh 获取到自定义的 my_fh 结构体

    // ... 其他释放资源的操作 ...

    v4l2_fh_del(&my_fh->fh); // 从 video_device 中删除文件句柄
    v4l2_fh_exit(&my_fh->fh); // 清理文件句柄
    kfree(my_fh); // 释放 my_fh 所占用的内存
    return 0;
}
```

下面是 V4L2 文件句柄操作函数的简要说明：

- `v4l2_fh_init`: 初始化文件句柄。**必须**在驱动程序的 `v4l2_file_operations`->`open()` 处理器中调用。
- `v4l2_fh_add`: 将 `v4l2_fh` 添加到 `video_device` 的文件句柄列表中。必须在文件句柄完全初始化后调用。
- `v4l2_fh_del`: 使文件句柄与 `video_device` 解除关联。此时可以调用文件句柄退出函数。
- `v4l2_fh_exit`: 清理文件句柄。清理完成后，可以释放 `v4l2_fh` 占用的内存。

如果 `struct v4l2_fh` 不是嵌入式的，那么可以使用以下辅助函数：

- `v4l2_fh_open`: 分配一个 `struct v4l2_fh`，对其进行初始化，并将其添加到与 `struct file` 关联的 `struct video_device` 中。
- `v4l2_fh_release`: 从与 `struct file` 关联的 `struct video_device` 中删除 `v4l2_fh`，清理该结构体并释放它所占用的内存。

这两个函数可以插入到 `v4l2_file_operations` 的 `open()` 和 `release()` 操作中。

许多驱动程序需要在第一个文件句柄打开以及最后一个文件句柄关闭时执行某些操作。为此，增加了两个辅助函数来检查 `v4l2_fh` 结构是否是与设备节点相关的唯一打开的文件句柄：

- `v4l2_fh_is_singular`: 如果文件句柄是唯一打开的文件句柄，则返回 1；否则返回 0。
```c:func:`v4l2_fh_is_singular_file <v4l2_fh_is_singular_file>` (struct file *filp)

- 类似的功能，但是它通过 `filp->private_data` 调用 `v4l2_fh_is_singular`
V4L2 文件句柄函数和数据结构
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. kernel-doc:: include/media/v4l2-fh.h
```

翻译为：

```C函数 `v4l2_fh_is_singular_file <v4l2_fh_is_singular_file>` (struct file *filp)

- 功能类似，但它是通过 `filp->private_data` 调用 `v4l2_fh_is_singular`
V4L2 文件句柄函数和数据结构
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. 内核文档:: include/media/v4l2-fh.h
```
