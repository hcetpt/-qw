SPDX 许可证标识符: GPL-2.0

==================================
Tracefs 环形缓冲区内存映射
==================================

:作者: Vincent Donnefort <vdonnefort@google.com>

概述
=====
Tracefs 环形缓冲区内存映射提供了一种高效的数据流方法，因为不需要复制内存。应用程序通过映射环形缓冲区成为该环形缓冲区的消费者，类似于 trace_pipe 的方式。

内存映射设置
====================
映射是通过 trace_pipe_raw 接口的 mmap() 实现的。
映射的第一个系统页包含环形缓冲区的统计信息和描述。它被称为元数据页。元数据页中最重要的字段之一是 reader，其中包含可以被映射器安全读取的子缓冲区 ID（参见 ring-buffer-design.rst）。
元数据页后面是所有按递增 ID 排序的子缓冲区。因此，很容易知道 reader 在映射中的起始位置：

.. code-block:: c

        reader_id = meta->reader->id;
        reader_offset = meta->meta_page_size + reader_id * meta->subbuf_size;

当应用程序处理完当前的 reader 后，它可以使用 trace_pipe_raw ioctl() 的 TRACE_MMAP_IOCTL_GET_READER 获取一个新的 reader。这个 ioctl 也会更新元数据页中的字段。

限制
=====
当一个 Tracefs 环形缓冲区的映射已经存在时，不可能调整其大小（无论是增加整个环形缓冲区的大小还是每个子缓冲区的大小）。此外，也不能使用快照，并且会导致 splice 操作复制环形缓冲区的数据而不是使用无复制的交换操作。
允许并发读取者（无论是另一个映射该环形缓冲区的应用程序还是使用 trace_pipe 的内核），但不推荐这样做。它们会竞争环形缓冲区，输出是不可预测的，就像 trace_pipe 上的并发读取者一样。

示例
======
.. code-block:: c

        #include <fcntl.h>
        #include <stdio.h>
        #include <stdlib.h>
        #include <unistd.h>

        #include <linux/trace_mmap.h>

        #include <sys/mman.h>
        #include <sys/ioctl.h>

        #define TRACE_PIPE_RAW "/sys/kernel/tracing/per_cpu/cpu0/trace_pipe_raw"

        int main(void)
        {
                int page_size = getpagesize(), fd, reader_id;
                unsigned long meta_len, data_len;
                struct trace_buffer_meta *meta;
                void *map, *reader, *data;

                fd = open(TRACE_PIPE_RAW, O_RDONLY | O_NONBLOCK);
                if (fd < 0)
                        exit(EXIT_FAILURE);

                map = mmap(NULL, page_size, PROT_READ, MAP_SHARED, fd, 0);
                if (map == MAP_FAILED)
                        exit(EXIT_FAILURE);

                meta = (struct trace_buffer_meta *)map;
                meta_len = meta->meta_page_size;

                printf("entries:        %llu\n", meta->entries);
                printf("overrun:        %llu\n", meta->overrun);
                printf("read:           %llu\n", meta->read);
                printf("nr_subbufs:     %u\n", meta->nr_subbufs);

                data_len = meta->subbuf_size * meta->nr_subbufs;
                data = mmap(NULL, data_len, PROT_READ, MAP_SHARED, fd, meta_len);
                if (data == MAP_FAILED)
                        exit(EXIT_FAILURE);

                if (ioctl(fd, TRACE_MMAP_IOCTL_GET_READER) < 0)
                        exit(EXIT_FAILURE);

                reader_id = meta->reader.id;
                reader = data + meta->subbuf_size * reader_id;

                printf("Current reader address: %p\n", reader);

                munmap(data, data_len);
                munmap(meta, meta_len);
                close(fd);

                return 0;
        }
