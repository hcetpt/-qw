VDUSE - "vDPA 设备在用户空间"

vDPA（virtio 数据路径加速）设备是一种使用符合 virtio 规范的数据路径以及特定于供应商的控制路径的设备。vDPA 设备可以物理地存在于硬件上，也可以通过软件进行模拟。VDUSE 是一个框架，使得在用户空间中实现软件模拟的 vDPA 设备成为可能。为了使设备模拟更加安全，模拟的 vDPA 设备的控制路径在内核中处理，而数据路径则在用户空间中实现。
需要注意的是，目前 VDUSE 框架仅支持 virtio 块设备，当由非特权用户运行实现数据路径的用户空间进程时，这可以减少安全风险。在解决了相应设备驱动程序的安全问题或将来修复了这些问题之后，可以添加对其他设备类型的支持。

创建/销毁 VDUSE 设备
----------------------

VDUSE 设备按以下步骤创建：

1. 使用 ioctl(VDUSE_CREATE_DEV) 在 /dev/vduse/control 上创建一个新的 VDUSE 实例
2. 使用 ioctl(VDUSE_VQ_SETUP) 在 /dev/vduse/$NAME 上设置每个 virtqueue
3. 开始处理来自 /dev/vduse/$NAME 的 VDUSE 消息。当将 VDUSE 实例附加到 vDPA 总线时，第一条消息将会到达
4. 发送 VDPA_CMD_DEV_NEW netlink 消息以将 VDUSE 实例附加到 vDPA 总线

VDUSE 设备按以下步骤销毁：

1. 发送 VDPA_CMD_DEV_DEL netlink 消息以将 VDUSE 实例从 vDPA 总线分离
2. 关闭指向 /dev/vduse/$NAME 的文件描述符
3. 使用 ioctl(VDUSE_DESTROY_DEV) 在 /dev/vduse/control 上销毁 VDUSE 实例

netlink 消息可以通过 iproute2 中的 vdpa 工具发送，或者使用下面的示例代码：

```c
static int netlink_add_vduse(const char *name, enum vdpa_command cmd)
{
    struct nl_sock *nlsock;
    struct nl_msg *msg;
    int famid;

    nlsock = nl_socket_alloc();
    if (!nlsock)
        return -ENOMEM;

    if (genl_connect(nlsock))
        goto free_sock;

    famid = genl_ctrl_resolve(nlsock, VDPA_GENL_NAME);
    if (famid < 0)
        goto close_sock;

    msg = nlmsg_alloc();
    if (!msg)
        goto close_sock;

    if (!genlmsg_put(msg, NL_AUTO_PORT, NL_AUTO_SEQ, famid, 0, 0, cmd, 0))
        goto nla_put_failure;

    NLA_PUT_STRING(msg, VDPA_ATTR_DEV_NAME, name);
    if (cmd == VDPA_CMD_DEV_NEW)
        NLA_PUT_STRING(msg, VDPA_ATTR_MGMTDEV_DEV_NAME, "vduse");

    if (nl_send_sync(nlsock, msg))
        goto close_sock;

    nl_close(nlsock);
    nl_socket_free(nlsock);

    return 0;
nla_put_failure:
    nlmsg_free(msg);
close_sock:
    nl_close(nlsock);
free_sock:
    nl_socket_free(nlsock);
    return -1;
}
```

VDUSE 如何工作
-------------------

如前所述，通过在 /dev/vduse/control 上执行 ioctl(VDUSE_CREATE_DEV) 创建 VDUSE 设备。通过这个 ioctl，用户空间可以指定一些基本配置，例如设备名称（唯一标识一个 VDUSE 设备）、virtio 特性、virtio 配置空间、virtqueue 数量等，用于这个模拟设备。
然后，一个字符设备接口（/dev/vduse/$NAME）被导出到用户空间以进行设备仿真。用户空间可以使用VDUSE_VQ_SETUP ioctl在/dev/vduse/$NAME上添加针对每个virtqueue的配置，例如virtqueue的最大大小。初始化之后，VDUSE设备可以通过VDPA_CMD_DEV_NEW netlink消息附接到vDPA总线。用户空间需要通过read()/write()操作/dev/vduse/$NAME来接收/回复来自VDUSE内核模块的一些控制消息，如下所示：

.. code-block:: c

    static int vduse_message_handler(int dev_fd)
    {
        int len;
        struct vduse_dev_request req;
        struct vduse_dev_response resp;

        len = read(dev_fd, &req, sizeof(req));
        if (len != sizeof(req))
            return -1;

        resp.request_id = req.request_id;

        switch (req.type) {

        /* 处理不同类型的消息 */

        }

        len = write(dev_fd, &resp, sizeof(resp));
        if (len != sizeof(resp))
            return -1;

        return 0;
    }

VDUSE框架目前引入了三种类型的消息：

- VDUSE_GET_VQ_STATE：获取virtqueue的状态，用户空间应返回split virtqueue的可用索引或packed virtqueue的设备/驱动器环形计数器和可用/已用索引。
- VDUSE_SET_STATUS：设置设备状态，用户空间应遵循virtio规范：https://docs.oasis-open.org/virtio/virtio/v1.1/virtio-v1.1.html 来处理此消息。例如，如果设备不能接受从VDUSE_DEV_GET_FEATURES ioctl获得的协商后的virtio特性，则无法设置FEATURES_OK状态位。
- VDUSE_UPDATE_IOTLB：通知用户空间更新指定IOVA范围内的内存映射，用户空间首先应移除旧映射，然后通过VDUSE_IOTLB_GET_FD ioctl设置新映射。

在通过VDUSE_SET_STATUS消息设置DRIVER_OK状态位后，用户空间能够开始数据平面处理，步骤如下：

1. 使用VDUSE_VQ_GET_INFO ioctl获取指定virtqueue的信息，包括大小、描述符表、可用环和已用环的IOVA，状态和就绪状态。
2. 将上述IOVA传递给VDUSE_IOTLB_GET_FD ioctl，以便将这些IOVA区域映射到用户空间。以下是一些示例代码：

.. code-block:: c

    static int perm_to_prot(uint8_t perm)
    {
        int prot = 0;

        switch (perm) {
        case VDUSE_ACCESS_WO:
            prot |= PROT_WRITE;
            break;
        case VDUSE_ACCESS_RO:
            prot |= PROT_READ;
            break;
        case VDUSE_ACCESS_RW:
            prot |= PROT_READ | PROT_WRITE;
            break;
        }

        return prot;
    }

    static void *iova_to_va(int dev_fd, uint64_t iova, uint64_t *len)
    {
        int fd;
        void *addr;
        size_t size;
        struct vduse_iotlb_entry entry;

        entry.start = iova;
        entry.last = iova;

        /*
         * 找到与指定范围[start, last]重叠的第一个IOVA区域，并返回相应的文件描述符
         */
        fd = ioctl(dev_fd, VDUSE_IOTLB_GET_FD, &entry);
        if (fd < 0)
            return NULL;

        size = entry.last - entry.start + 1;
        *len = entry.last - iova + 1;
        addr = mmap(0, size, perm_to_prot(entry.perm), MAP_SHARED,
                    fd, entry.offset);
        close(fd);
        if (addr == MAP_FAILED)
            return NULL;

        /*
         * 使用一些数据结构（如链表）存储iotlb映射。当接收到相应的VDUSE_UPDATE_IOTLB消息或设备重置时，应调用munmap(2)释放缓存映射
         */

        return addr + iova - entry.start;
    }

3. 使用VDUSE_VQ_SETUP_KICKFD ioctl为指定的virtqueue设置kick事件文件描述符。kick事件文件描述符由VDUSE内核模块用于通知用户空间消费可用环。这是可选的，因为用户空间可以选择轮询可用环。
4. 监听kick事件文件描述符（可选），并消费可用环。描述符表中描述的缓冲区也应在访问前通过VDUSE_IOTLB_GET_FD ioctl映射到用户空间。
5. 在填充已用环后，使用VDUSE_INJECT_VQ_IRQ ioctl为特定virtqueue注入中断。
有关uAPI的更多详细信息，请参阅 include/uapi/linux/vduse.h
