Sync File API 指南
===================

:作者: Gustavo Padovan <gustavo at padovan dot org>

本文档旨在为设备驱动程序开发者提供关于 Sync File API 的介绍及其使用方法。Sync File 是承载围栏（结构 dma_fence）的载体，这些围栏用于在驱动程序之间或跨进程边界进行同步。
Sync File API 主要用于向用户空间发送和接收围栏信息。它使用户空间能够执行显式围栏操作，即生产者驱动程序（如 GPU 或 V4L 驱动程序）不直接将围栏与缓冲区关联，而是通过 Sync File 将与缓冲区相关的围栏发送到用户空间。
然后，该 Sync File 可以被发送给消费者（例如 DRM 驱动程序），在接收到的围栏信号之前，消费者不会对缓冲区做任何处理，也就是说，发出围栏的驱动程序不再使用/处理该缓冲区，并且会发出信号表明缓冲区已准备好使用。对于消费者到生产者的循环部分，过程类似。
Sync File 使得用户空间可以感知驱动程序间共享缓冲区的同步。
Sync File 最初是在 Android 内核中添加的，但当前的 Linux 桌面环境也能从中获益良多。

### 输入围栏与输出围栏

Sync File 可以从驱动程序到用户空间，也可以相反方向。当 Sync File 从驱动程序发送到用户空间时，我们称其中包含的围栏为“输出围栏”。这些围栏与驱动程序正在处理或将要处理的缓冲区相关联，因此驱动程序创建输出围栏以便通过 `dma_fence_signal()` 通知何时完成对该缓冲区的使用（或处理）。
输出围栏是由驱动程序创建的围栏。
另一方面，如果驱动程序通过 Sync File 从用户空间接收围栏，则称这些围栏为“输入围栏”。接收输入围栏意味着我们需要等待这些围栏的信号才能使用与之相关的缓冲区。

### 创建 Sync File

当驱动程序需要向用户空间发送输出围栏时，它会创建一个 Sync File 接口：
```c
struct sync_file *sync_file_create(struct dma_fence *fence);
```

调用者传递输出围栏并获取 Sync File。这只是第一步，接下来需要在 Sync File 的 `file` 成员上安装一个文件描述符。为此，先获取一个文件描述符：
```c
fd = get_unused_fd_flags(O_CLOEXEC);
```
然后将其安装到 Sync File 的 `file` 成员上：
```c
fd_install(fd, sync_file->file);
```
现在 Sync File 的文件描述符可以发送到用户空间了。
如果创建过程失败，或者由于其他原因需要释放 `sync_file`，应当使用 `fput(sync_file->file)`。
### 从用户空间接收同步文件
当用户空间需要向驱动程序发送一个围栏(fence)时，它会将同步文件的文件描述符传递给内核。然后，内核可以从该文件描述符中检索到围栏信息。
#### 接口:
```c
struct dma_fence *sync_file_get_fence(int fd);
```
返回的引用归调用者所有，并且必须在之后通过 `dma_fence_put()` 来释放。如果出现错误，则返回 `NULL`。
#### 参考资料:
1. 在 `include/linux/sync_file.h` 中定义的 `struct sync_file` 结构体。
2. 上述提到的所有接口均定义在 `include/linux/sync_file.h` 中。
