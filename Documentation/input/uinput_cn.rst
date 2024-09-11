uinput 模块
=============

简介
============

uinput 是一个内核模块，它使得从用户空间模拟输入设备成为可能。通过写入 `/dev/uinput`（或 `/dev/input/uinput`）设备，一个进程可以创建具有特定功能的虚拟输入设备。一旦这个虚拟设备被创建，该进程可以通过它发送事件，这些事件将被传递给用户空间和内核消费者。

接口
=========

```
linux/uinput.h
```

uinput 头文件定义了用于创建、设置和销毁虚拟设备的 ioctl。

libevdev
========

libevdev 是一个为 evdev 设备提供接口的包装库，它可以用来创建 uinput 设备并发送事件。与直接访问 uinput 相比，使用 libevdev 更不容易出错，并且应考虑在新软件中使用。

有关 libevdev 的示例和更多信息，请参见：[https://www.freedesktop.org/software/libevdev/doc/latest/](https://www.freedesktop.org/software/libevdev/doc/latest/)

示例
========

键盘事件
---------------

第一个示例展示了如何创建一个新的虚拟设备以及如何发送按键事件。为了简化，所有默认导入和错误处理程序都被移除了。
```c
#include <linux/uinput.h>

void emit(int fd, int type, int code, int val)
{
    struct input_event ie;

    ie.type = type;
    ie.code = code;
    ie.value = val;
    /* 下面的时间戳值会被忽略 */
    ie.time.tv_sec = 0;
    ie.time.tv_usec = 0;

    write(fd, &ie, sizeof(ie));
}

int main(void)
{
    struct uinput_setup usetup;

    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);

    /*
     * 下面的 ioctl 将使即将创建的设备能够传递按键事件，在这种情况下是空格键
    */
    ioctl(fd, UI_SET_EVBIT, EV_KEY);
    ioctl(fd, UI_SET_KEYBIT, KEY_SPACE);

    memset(&usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234; /* 示例供应商 */
    usetup.id.product = 0x5678; /* 示例产品 */
    strcpy(usetup.name, "Example device");

    ioctl(fd, UI_DEV_SETUP, &usetup);
    ioctl(fd, UI_DEV_CREATE);

    /*
     * 在 UI_DEV_CREATE 时，内核将为该设备创建设备节点。我们在代码中插入了一个暂停，以便用户空间有时间检测、初始化新设备，并开始监听事件，否则它不会注意到我们即将发送的事件。这个暂停仅在我们的示例代码中需要！
    */
    sleep(1);

    /* 按键按下，报告事件，发送按键释放，再次报告 */
    emit(fd, EV_KEY, KEY_SPACE, 1);
    emit(fd, EV_SYN, SYN_REPORT, 0);
    emit(fd, EV_KEY, KEY_SPACE, 0);
    emit(fd, EV_SYN, SYN_REPORT, 0);

    /*
     * 给用户空间一些时间来读取事件，然后我们用 UI_DEV_DESTROY 销毁设备
    */
    sleep(1);

    ioctl(fd, UI_DEV_DESTROY);
    close(fd);

    return 0;
}
```

鼠标移动
---------------

此示例展示了如何创建一个行为类似于物理鼠标的虚拟设备。
```c
#include <linux/uinput.h>

/* emit 函数与第一个示例相同 */

int main(void)
{
    struct uinput_setup usetup;
    int i = 50;

    int fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);

    /* 启用左键和相对事件 */
    ioctl(fd, UI_SET_EVBIT, EV_KEY);
    ioctl(fd, UI_SET_KEYBIT, BTN_LEFT);

    ioctl(fd, UI_SET_EVBIT, EV_REL);
    ioctl(fd, UI_SET_RELBIT, REL_X);
    ioctl(fd, UI_SET_RELBIT, REL_Y);

    memset(&usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234; /* 示例供应商 */
    usetup.id.product = 0x5678; /* 示例产品 */
    strcpy(usetup.name, "Example device");

    ioctl(fd, UI_DEV_SETUP, &usetup);
    ioctl(fd, UI_DEV_CREATE);

    /*
     * 在 UI_DEV_CREATE 时，内核将为该设备创建设备节点。我们在代码中插入了一个暂停，以便用户空间有时间检测、初始化新设备，并开始监听事件，否则它不会注意到我们即将发送的事件。这个暂停仅在我们的示例代码中需要！
    */
    sleep(1);

    /* 沿对角线移动鼠标，每个轴移动 5 个单位 */
    while (i--) {
        emit(fd, EV_REL, REL_X, 5);
        emit(fd, EV_REL, REL_Y, 5);
        emit(fd, EV_SYN, SYN_REPORT, 0);
        usleep(15000);
    }

    /*
     * 给用户空间一些时间来读取事件，然后我们用 UI_DEV_DESTROY 销毁设备
    */
    sleep(1);

    ioctl(fd, UI_DEV_DESTROY);
    close(fd);

    return 0;
}
```

uinput 旧接口
--------------------

在 uinput 版本 5 之前，并没有专门的 ioctl 来设置虚拟设备。支持旧版本 uinput 接口的程序需要填充 `uinput_user_dev` 结构体并通过写入 uinput 文件描述符来配置新的 uinput 设备。新代码不应使用旧接口，而应通过 ioctl 调用或使用 libevdev 进行交互。
```c
#include <linux/uinput.h>

/* emit 函数与第一个示例相同 */

int main(void)
{
    struct uinput_user_dev uud;
    int version, rc, fd;

    fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    rc = ioctl(fd, UI_GET_VERSION, &version);

    if (rc == 0 && version >= 5) {
        /* 使用 UI_DEV_SETUP */
        return 0;
    }

    /*
     * 下面的 ioctl 将使即将创建的设备能够传递按键事件，在这种情况下是空格键
    */
```
```c
ioctl(fd, UI_SET_EVBIT, EV_KEY);
ioctl(fd, UI_SET_KEYBIT, KEY_SPACE);

memset(&uud, 0, sizeof(uud));
snprintf(uud.name, UINPUT_MAX_NAME_SIZE, "uinput old interface");
write(fd, &uud, sizeof(uud));

ioctl(fd, UI_DEV_CREATE);

/*
 * 在 UI_DEV_CREATE 时，内核将为该设备创建设备节点。我们在这里插入一个暂停，
 * 以便用户空间有时间检测、初始化新设备，并开始监听事件，否则它将不会注意到我们即将发送的事件。
 * 这个暂停仅在我们的示例代码中需要！
 */
sleep(1);

/* 按键按下，报告事件，发送按键释放，并再次报告 */
emit(fd, EV_KEY, KEY_SPACE, 1);
emit(fd, EV_SYN, SYN_REPORT, 0);
emit(fd, EV_KEY, KEY_SPACE, 0);
emit(fd, EV_SYN, SYN_REPORT, 0);

/*
 * 在我们使用 UI_DEV_DESTROY 销毁设备之前，给用户空间一些时间来读取事件
 */
sleep(1);

ioctl(fd, UI_DEV_DESTROY);

close(fd);
return 0;
```

这段代码的中文注释如下：

```c
ioctl(fd, UI_SET_EVBIT, EV_KEY);
ioctl(fd, UI_SET_KEYBIT, KEY_SPACE);

memset(&uud, 0, sizeof(uud));
snprintf(uud.name, UINPUT_MAX_NAME_SIZE, "uinput old interface");
write(fd, &uud, sizeof(uud));

ioctl(fd, UI_DEV_CREATE);

/*
 * 在 UI_DEV_CREATE 时，内核将为该设备创建设备节点。我们在这里插入一个暂停，
 * 以便用户空间有时间检测、初始化新设备，并开始监听事件，否则它将不会注意到我们即将发送的事件。
 * 这个暂停仅在我们的示例代码中需要！
 */
sleep(1);

/* 按键按下，报告事件，发送按键释放，并再次报告 */
emit(fd, EV_KEY, KEY_SPACE, 1);
emit(fd, EV_SYN, SYN_REPORT, 0);
emit(fd, EV_KEY, KEY_SPACE, 0);
emit(fd, EV_SYN, SYN_REPORT, 0);

/*
 * 在我们使用 UI_DEV_DESTROY 销毁设备之前，给用户空间一些时间来读取事件
 */
sleep(1);

ioctl(fd, UI_DEV_DESTROY);

close(fd);
return 0;
```
