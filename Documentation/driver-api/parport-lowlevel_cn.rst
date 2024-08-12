以下是文档的中文翻译：

===============================
并口（PARPORT）接口文档
===============================

:时间戳: <2000-02-24 13:30:20 twaugh>

以下列出了以下几个函数：

全局函数::
  parport_register_driver
  parport_unregister_driver
  parport_enumerate
  parport_register_device
  parport_unregister_device
  parport_claim
  parport_claim_or_block
  parport_release
  parport_yield
  parport_yield_blocking
  parport_wait_peripheral
  parport_poll_peripheral
  parport_wait_event
  parport_negotiate
  parport_read
  parport_write
  parport_open
  parport_close
  parport_device_id
  parport_device_coords
  parport_find_class
  parport_find_device
  parport_set_timeout

端口函数（可被低级驱动程序覆盖）：

  SPP（标准并行端口）::
    port->ops->read_data
    port->ops->write_data
    port->ops->read_status
    port->ops->read_control
    port->ops->write_control
    port->ops->frob_control
    port->ops->enable_irq
    port->ops->disable_irq
    port->ops->data_forward
    port->ops->data_reverse

  EPP（增强型并行端口）::
    port->ops->epp_write_data
    port->ops->epp_read_data
    port->ops->epp_write_addr
    port->ops->epp_read_addr

  ECP（扩展功能端口）::
    port->ops->ecp_write_data
    port->ops->ecp_read_data
    port->ops->ecp_write_addr

  其他::
    port->ops->nibble_read_data
    port->ops->byte_read_data
    port->ops->compat_write_data

并口子系统由“parport”（核心端口共享代码）和各种低级驱动程序组成，后者实际执行端口访问。每个低级驱动程序处理一种特定类型的端口（如PC、Amiga等）。并口对设备驱动程序作者的接口可以分为全局函数和端口函数。
全局函数主要用于在设备驱动程序与并口子系统之间进行通信：获取可用端口列表，声明端口供独家使用等。它们还包括一些在任何支持IEEE 1284架构上都能工作的“通用”函数。
端口函数由低级驱动程序提供，尽管核心并口模块为某些例程提供了通用“默认”实现。
端口函数可以分为三组：SPP、EPP和ECP。
SPP（标准并行端口）函数修改所谓的“SPP”寄存器：数据、状态和控制。硬件可能实际上并没有这样的寄存器，但PC有，并且这个接口是基于常见的PC实现建模的。其他低级驱动程序可能能够模拟大部分的功能。
EPP（增强型并行端口）函数用于在IEEE 1284 EPP模式下读写，而ECP（扩展功能端口）函数则用于IEEE 1284 ECP模式。（BECP呢？有人关心吗？）
EPP和/或ECP传输可能有硬件辅助也可能没有。如果有，则可能会或不会使用这些硬件辅助。如果没有使用硬件，则传输将由软件驱动。为了应对只勉强支持IEEE 1284的外围设备，提供了一个低级驱动程序特定函数来调整“修正系数”。
全局函数
================

parport_register_driver - 将设备驱动程序注册到并口中
---------------------------------------------------------------

SYNOPSIS
^^^^^^^^

::

	#include <linux/parport.h>

	struct parport_driver {
		const char *name;      // 驱动程序的文本名称
		void (*attach) (struct parport *);  // 处理新端口的函数指针
		void (*detach) (struct parport *);  // 处理因低级驱动卸载而消失的端口的函数指针
		struct parport_driver *next;        // 指向下一个并口驱动程序的指针
	};
	int parport_register_driver (struct parport_driver *driver);

DESCRIPTION
^^^^^^^^^^^

为了在检测到并行端口时得到通知，应调用parport_register_driver。您的驱动程序会立即接收到所有已检测到的端口的通知，并且每当加载新的低级驱动程序时也会接收到新的端口通知。
一个`struct parport_driver`包含您的驱动程序的文本名称、指向处理新端口的函数的指针以及指向处理由于低级驱动程序卸载而消失的端口的函数的指针。只有在端口未被使用（即其上没有注册任何设备）的情况下才会将其移除。
传递给attach/detach函数的`struct parport *`参数的可见部分包括：

struct parport
	{
		struct parport *next;  // 列表中的下一个并口
		const char *name;      // 端口名称
		unsigned int modes;    // 硬件模式的位字段
		struct parport_device_info probe_info;  // IEEE1284信息
		int number;            // 并口索引
		struct parport_operations *ops;
		..
结构体中还有其他成员，但不应直接操作它们。
`modes` 成员总结了底层硬件的能力。它由一些标志组成，这些标志可以进行位或运算：

  ============================= ===============================================
  PARPORT_MODE_PCSPP		IBM PC 寄存器可用，
				即作用于数据、控制和状态寄存器的函数可能
				直接写入硬件
PARPORT_MODE_TRISTATE		数据驱动器可以关闭
这允许数据线用于逆向（外围设备到主机）
				传输
PARPORT_MODE_COMPAT		硬件可以协助
				兼容模式（打印机）传输，即使用 compat_write_block
PARPORT_MODE_EPP		硬件可以协助 EPP
				传输
PARPORT_MODE_ECP		硬件可以协助 ECP
				传输
PARPORT_MODE_DMA		硬件可以使用 DMA，因此您可能
				希望将 ISA DMA 可用内存（即使用
				GFP_DMA 标志与 kmalloc 分配的内存）
			 传递给低层驱动程序以利用此功能
  ============================= ===============================================

`modes` 中还可能存在其他标志
`modes` 的内容仅作为建议。例如，如果硬件支持 DMA，并且 `modes` 中包含 PARPORT_MODE_DMA，则并不一定意味着在可能的情况下总会使用 DMA。
同样地，能够协助ECP传输的硬件不一定被使用。

**返回值**
^^^^^^^^^^^^

成功时返回零，否则返回错误代码。
**错误**
^^^^^^

没有。 （它会失败吗？为什么返回int？）

**示例**
^^^^^^^

```c
static void lp_attach (struct parport *port)
{
    ..
    private = kmalloc (...);
    dev[count++] = parport_register_device (...);
    ..
}

static void lp_detach (struct parport *port)
{
    ..
}

static struct parport_driver lp_driver = {
    "lp",
    lp_attach,
    lp_detach,
    NULL /* 总是在这里放NULL */
};

int lp_init (void)
{
    ..
    if (parport_register_driver (&lp_driver)) {
        /* 失败；我们无能为力。 */
        return -EIO;
    }
    ..
}
```

**另见**
^^^^^^^^

parport_unregister_driver, parport_register_device, parport_enumerate

---

**parport_unregister_driver - 告诉并口忘记这个驱动程序**
--------------------------------------------------------------------

**简介**
^^^^^^^^

```c
#include <linux/parport.h>

struct parport_driver {
    const char *name;
    void (*attach) (struct parport *);
    void (*detach) (struct parport *);
    struct parport_driver *next;
};
void parport_unregister_driver (struct parport_driver *driver);
```

**描述**
^^^^^^^^^^^

这告诉并口不要通知设备驱动程序关于新端口或端口消失的消息。属于该驱动程序的已注册设备并不会被注销：必须对每一个设备使用parport_unregister_device。
**示例**
^^^^^^^

```c
void cleanup_module (void)
{
    ..
    /* 停止通知。 */
    parport_unregister_driver (&lp_driver);

    /* 注销设备。 */
    for (i = 0; i < NUM_DEVS; i++)
        parport_unregister_device (dev[i]);
    ..
}
```
### 参见
^^^^^^^^

`parport_register_driver`, `parport_enumerate`

### parport_enumerate - 获取并列端口列表（已废弃）
------------------------------------------------------------------

### 简介
^^^^^^^^

```
#include <linux/parport.h>

struct parport *parport_enumerate (void);
```

### 描述
^^^^^^^^^^^

获取当前机器上有效并列端口列表中的第一个端口。
使用返回的 `struct parport *` 中的 `struct parport *next` 元素可以找到后续的并列端口。如果 `next` 为 NULL，则表示列表中没有更多的并列端口。列表中的端口数量不会超过 `PARPORT_MAX`。

### 返回值
^^^^^^^^^^^^

返回描述当前机器上的一个有效并列端口的 `struct parport *`，如果没有这样的端口则返回 NULL。

### 错误
^^^^^^

此函数可能返回 NULL 表示没有可用的并列端口。

### 示例
^^^^^^^

```
int detect_device (void)
{
    struct parport *port;

    for (port = parport_enumerate (); port != NULL; port = port->next) {
        /* 尝试检测端口上的设备... */
        ..
    }

    ..
}
```

### 注意
^^^^^

`parport_enumerate` 已被废弃；应该使用 `parport_register_driver`。

### 参见
^^^^^^^^

`parport_register_driver`, `parport_unregister_driver`

### parport_register_device - 注册以使用端口
------------------------------------------------

### 简介
^^^^^^^^

```
#include <linux/parport.h>

typedef int (*preempt_func) (void *handle);
typedef void (*wakeup_func) (void *handle);
typedef int (*irq_func) (int irq, void *handle, struct pt_regs *);

struct pardevice *parport_register_device(struct parport *port,
                                           const char *name,
                                           preempt_func preempt,
                                           wakeup_func wakeup,
                                           irq_func irq,
                                           int flags,
                                           void *handle);
```

### 描述
^^^^^^^^^^^

使用此函数在并列端口 (`port`) 上注册你的设备驱动程序。一旦完成注册，你将能够使用 `parport_claim` 和 `parport_release` 来使用该端口。
(`name`) 参数是出现在 `/proc` 文件系统中的设备名称。字符串必须在整个设备生命周期内保持有效（直到调用 `parport_unregister_device`）。
此函数将在你的驱动程序中注册三个回调：`preempt`、`wakeup` 和 `irq`。这些回调都可以设置为 NULL，以表明不需要这些回调。
当调用`"preempt"`函数时，是因为另一个驱动程序希望使用并行端口。如果当前还不能释放并行端口，则`"preempt"`函数应返回非零值——如果返回零，则端口将被另一个驱动程序占用，并且在使用之前必须重新获取该端口。

当另一个驱动程序已经释放了端口并且没有其他驱动程序声称拥有它时，会调用`"wakeup"`函数。你可以在`"wakeup"`函数中声明并行端口（在这种情况下，声明一定会成功），或者如果你现在不需要端口的话选择不声明。

如果你的驱动程序已声明的并行端口上发生了中断，则会调用`"irq"`函数。（这里可以写一些关于共享中断的内容。）

`"handle"`是一个指向特定于驱动程序的数据的指针，并传递给回调函数。
`"flags"`可能是以下标志的按位组合：

| 标志 | 意义 |
| --- | --- |
| `PARPORT_DEV_EXCL` | 设备完全不能与其他设备共享并行端口 |
| | 只有在绝对必要时才使用 |

这些类型定义实际上并没有定义——它们仅显示以使函数原型更易读。
返回的`"struct pardevice"`结构体的可见部分如下：

```c
struct pardevice {
    struct parport *port;       // 关联的端口
    void *private;              // 设备驱动程序的 'handle'
    ..
};
```

**返回值**
--------------

一个`struct pardevice *`：一个注册的并行端口设备的句柄，可用于`parport_claim`、`parport_release`等操作。

**错误**
----------

返回值为NULL表示在该端口上注册设备时出现了问题。

**示例**
-----------

```c
static int preempt (void *handle)
{
    if (busy_right_now)
        return 1;

    must_reclaim_port = 1;
    return 0;
}

static void wakeup (void *handle)
{
    struct toaster *private = handle;
    struct pardevice *dev = private->dev;
    if (!dev) return; /* 避免竞争条件 */

    if (want_port)
        parport_claim (dev);
}

static int toaster_detect (struct toaster *private, struct parport *port)
{
    private->dev = parport_register_device (port, "toaster", preempt,
                                            wakeup, NULL, 0,
                                            private);
    if (!private->dev)
        /* 无法与并行端口注册。 */
        return -EIO;

    must_reclaim_port = 0;
    busy_right_now = 1;
    parport_claim_or_block (private->dev);
    ..
}
```
/* 在烤面包机预热时不需要端口。 */
		busy_right_now = 0;
		..
busy_right_now = 1;
		if (must_reclaim_port) {
			parport_claim_or_block (private->dev);
			must_reclaim_port = 0;
		}
		..
}

参见
^^^^^^^^

`parport_unregister_device`, `parport_claim`


`parport_unregister_device` - 结束使用端口
-----------------------------------------------
简介

::

	#include <linux/parport.h>

	void parport_unregister_device (struct pardevice *dev);

描述
^^^^^^^^^^^

此函数与`parport_register_device`相对。使用`parport_unregister_device`后，“dev”将不再是有效的设备句柄。
你不应该注销当前已声明的设备，尽管如果你这样做了，它将被自动释放。
示例
^^^^^^^

::

	..
kfree (dev->private); /* 在丢失指针之前 */
	parport_unregister_device (dev);
	..
参见
^^^^^^^^

`parport_unregister_driver`


`parport_claim`, `parport_claim_or_block` - 为设备声明并控制并行端口
----------------------------------------------------------------------------

简介
^^^^^^^^

::

	#include <linux/parport.h>

	int parport_claim (struct pardevice *dev);
	int parport_claim_or_block (struct pardevice *dev);

描述
^^^^^^^^^^^

这些函数尝试获取“dev”注册的并行端口的控制权。“parport_claim”不会阻塞，但“parport_claim_or_block”可能会这样做。（在这里添加关于可中断或不可中断地阻塞的内容。）

你不应该尝试再次声明你已经声明的端口
返回值
^^^^^^^^^^^^

零的返回值表示成功声明了端口，调用者现在拥有并行端口。
如果`parport_claim_or_block`在成功返回前阻塞，则返回值是正数
错误
^^^^^^

========== ==========================================================
  -EAGAIN  端口当前不可用，但稍后再尝试声明可能成功
下面是给定内容的中文翻译：

---

### 参见

**parport_release**

---

**parport_release**
-------------------

**parport_release** 用于释放并行端口。

#### 用法概要

```c
#include <linux/parport.h>

void parport_release (struct pardevice *dev);
```

#### 描述

一旦并行端口设备被获取，可以使用 `parport_release` 来释放它。该函数不会失败，但你不应该释放你没有控制权的设备。

#### 示例

```c
static size_t write (struct pardevice *dev, const void *buf,
                     size_t len)
{
    ...
    written = dev->port->ops->write_ecp_data (dev->port, buf,
                                              len);
    parport_release (dev);
    ...
}
```

#### 参见

change_mode, parport_claim, parport_claim_or_block, parport_yield

---

**parport_yield**, **parport_yield_blocking** - 暂时释放并行端口

#### 用法概要

```c
#include <linux/parport.h>

int parport_yield (struct pardevice *dev);
int parport_yield_blocking (struct pardevice *dev);
```

#### 描述

当一个驱动程序控制着一个并行端口时，它可能允许另一个驱动程序暂时“借用”它。`parport_yield` 不会阻塞；`parport_yield_blocking` 可能会阻塞。

#### 返回值

- 零返回值表示调用者仍然拥有端口且调用没有阻塞。
- `parport_yield_blocking` 的正数返回值表示调用者仍然拥有端口且调用已阻塞。
- `-EAGAIN` 的返回值表示调用者不再拥有端口，并且在使用前必须重新获取。

#### 错误

| 值       | 描述                                                         |
|----------|--------------------------------------------------------------|
| `-EAGAIN` | 并行端口的所有权已被放弃                                     |

#### 参见

**parport_release**

---

**parport_wait_peripheral** - 等待状态线，最长 35 毫秒

#### 用法概要

```c
#include <linux/parport.h>

int parport_wait_peripheral (struct parport *port,
                             unsigned char mask,
                             unsigned char val);
```

#### 描述

等待 mask 中的状态线与 val 中的值匹配。

#### 返回值

| 值       | 描述                                                             |
|----------|------------------------------------------------------------------|
| `-EINTR` | 有信号待处理                                                     |
| `0`      | mask 中的状态线具有 val 中的值                                   |
| `1`      | 等待超时（已过去 35 毫秒）                                       |

#### 参见

**parport_poll_peripheral**

---

**parport_poll_peripheral** - 等待状态线，以微秒为单位

#### 用法概要

```c
#include <linux/parport.h>

int parport_poll_peripheral (struct parport *port,
                             unsigned char mask,
                             unsigned char val,
                             int usec);
```

#### 描述

等待 mask 中的状态线与 val 中的值匹配。
### RETURN VALUE
^^^^^^^^^^^^

======== ==========================================================
 -EINTR  有信号待处理
      0  mask中的状态行在val中有值
      1  等待超时（usec微秒已过去）
======== ==========================================================

### 参见
^^^^^^^^

parport_wait_peripheral

### parport_wait_event - 在端口上等待事件
------------------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

int parport_wait_event (struct parport *port, signed long timeout)
```

### 描述
^^^^^^^^^^^

在端口上等待事件（例如，中断）。超时时间以节拍为单位。
### 返回值
^^^^^^^^^^^^

======= ==========================================================
      0  成功
     <0  错误（尽快退出）
     >0  超时
======= ==========================================================

### parport_negotiate - 执行IEEE 1284协商
-------------------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

int parport_negotiate (struct parport *, int mode);
```

### 描述
^^^^^^^^^^^

执行IEEE 1284协商
### 返回值
^^^^^^^^^^^^

======= ==========================================================
     0  握手成功；可用的IEEE 1284外围设备和模式
    -1  握手失败；外围设备不合规（或不存在）
     1  握手成功；存在IEEE 1284外围设备但模式不可用
======= ==========================================================

### 参见
^^^^^^^^

parport_read, parport_write

### parport_read - 从设备读取数据
------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

ssize_t parport_read (struct parport *, void *buf, size_t len);
```

### 描述
^^^^^^^^^^^

根据当前的IEEE 1284传输模式从设备读取数据。这仅适用于支持反向数据传输的模式。
### 返回值
^^^^^^^^^^^^

如果为负数，则表示错误代码；否则表示传输的字节数
### 参见
^^^^^^^^

parport_write, parport_negotiate

### parport_write - 向设备写入数据
------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

ssize_t parport_write (struct parport *, const void *buf, size_t len);
```

### 描述
^^^^^^^^^^^

根据当前的IEEE 1284传输模式向设备写入数据。这仅适用于支持正向数据传输的模式。
### 返回值
^^^^^^^^^^^^

如果为负数，则表示错误代码；否则表示传输的字节数
### 参见
^^^^^^^^

parport_read, parport_negotiate

### parport_open - 为特定设备编号注册设备
-----------------------------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

struct pardevice *parport_open (int devnum, const char *name,
				        int (*pf) (void *),
					void (*kf) (void *),
					void (*irqf) (int, void *,
						      struct pt_regs *),
					int flags, void *handle);
```

### 描述
^^^^^^^^^^^

类似于parport_register_device，但接受设备编号而不是指向struct parport的指针。
### 返回值
^^^^^^^^^^^^

参见parport_register_device。如果没有与devnum关联的设备，则返回NULL
### 参见
^^^^^^^^

parport_register_device

### parport_close - 为特定设备编号注销设备
--------------------------------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

void parport_close (struct pardevice *dev);
```

### 描述
^^^^^^^^^^^

这是对于parport_open的parport_unregister_device的等价物。
### 参见
^^^^^^^^

parport_unregister_device, parport_open

### parport_device_id - 获取IEEE 1284设备ID
----------------------------------------------

### 概要
^^^^^^^^

```c
#include <linux/parport.h>

ssize_t parport_device_id (int devnum, char *buffer, size_t len);
```

### 描述
^^^^^^^^^^^

获取与给定设备相关的IEEE 1284设备ID。
### 返回值
^^^^^^^^^^^^

如果是负数，则表示一个错误代码；否则，表示包含设备ID的缓冲区字节数。设备ID的格式如下：

	[长度][ID]

前两个字节表示整个设备ID的包内长度，并且是采用大端序。ID是一个由以下形式的键值对序列组成：

	key:value;

### 注意
^^^^^

许多设备具有不符合IEEE 1284标准的设备ID。

### 参见
^^^^^^^^

parport_find_class, parport_find_device

### parport_device_coords - 将设备编号转换为设备坐标
-------------------------------------------------------------------

### 概述
^^^^^^^^

```c
#include <linux/parport.h>

int parport_device_coords (int devnum, int *parport, int *mux,
                           int *daisy);
```

### 描述
^^^^^^^^^^^

在设备编号（以零为基础）和设备坐标（端口、多路复用器、菊花链地址）之间进行转换。
### 返回值
^^^^^^^^^^^^

成功时返回零，在这种情况下坐标是(``*parport``, ``*mux``,
``*daisy``)。
### 参见
^^^^^^^^

parport_open, parport_device_id

### parport_find_class - 根据类别查找设备
-----------------------------------------------

### 概述
^^^^^^^^

```c
#include <linux/parport.h>

typedef enum {
    PARPORT_CLASS_LEGACY = 0,       /* 非IEEE1284设备 */
    PARPORT_CLASS_PRINTER,
    PARPORT_CLASS_MODEM,
    PARPORT_CLASS_NET,
    PARPORT_CLASS_HDC,              /* 硬盘控制器 */
    PARPORT_CLASS_PCMCIA,
    PARPORT_CLASS_MEDIA,            /* 多媒体设备 */
    PARPORT_CLASS_FDC,              /* 软盘控制器 */
    PARPORT_CLASS_PORTS,
    PARPORT_CLASS_SCANNER,
    PARPORT_CLASS_DIGCAM,
    PARPORT_CLASS_OTHER,            /* 其他任何设备 */
    PARPORT_CLASS_UNSPEC,           /* ID中没有CLS字段 */
    PARPORT_CLASS_SCSIADAPTER
} parport_device_class;

int parport_find_class (parport_device_class cls, int from);
```

### 描述
^^^^^^^^^^^

根据类别查找设备。搜索从设备编号from+1开始。
### 返回值
^^^^^^^^^^^^

该类别的下一个设备的设备编号，如果不存在此类设备则返回-1。
### 注意
^^^^^

示例使用：

```c
int devnum = -1;
while ((devnum = parport_find_class (PARPORT_CLASS_DIGCAM, devnum)) != -1) {
    struct pardevice *dev = parport_open (devnum, ...);
    ..
}
```
### 参见
^^^^^^^^

parport_find_device, parport_open, parport_device_id

### parport_find_device - 根据类别查找设备
------------------------------------------------

### 概述
^^^^^^^^

```c
#include <linux/parport.h>

int parport_find_device (const char *mfg, const char *mdl, int from);
```

### 描述
^^^^^^^^^^^

根据制造商和型号查找设备。搜索从设备编号from+1开始。
### 返回值
^^^^^^^^^^^^

符合指定条件的下一个设备的设备编号，如果不存在此类设备则返回-1。
### 注意
^^^^^

示例使用：

```c
int devnum = -1;
while ((devnum = parport_find_device ("IOMEGA", "ZIP+", devnum)) != -1) {
    struct pardevice *dev = parport_open (devnum, ...);
    ..
}
```
### 参见
^^^^^^^^

parport_find_class, parport_open, parport_device_id

### parport_set_timeout - 设置空闲超时时间
------------------------------------------------

### 概述
^^^^^^^^

```c
#include <linux/parport.h>

long parport_set_timeout (struct pardevice *dev, long inactivity);
```

### 描述
^^^^^^^^^^^

为注册的设备设置空闲超时时间（以滴答为单位）。返回之前的超时时间。
### 返回值
^^^^^^^^^^^^

上次的超时时间，以滴答为单位。

### 注意事项
^^^^^

对于并口的一些 `port->ops` 函数可能需要一段时间来执行，这可能是由于外围设备上的延迟造成的。当外围设备在 `inactivity` 滴答时间内没有响应后，将发生超时，并且阻塞函数会返回。
0 滴答的超时是一个特殊情况：该函数必须尽可能地完成操作而不进行阻塞或使硬件处于未知状态。例如，在中断处理程序中执行端口操作时，应使用 0 滴答的超时。
一旦为注册的设备设置了一个超时时间，这个值就会一直保持不变，直到再次被设置。
### 参见
^^^^^^^^

`port->ops->xxx_read/write_yyy`

### 端口函数
=============

`port->ops` 结构中的函数（`struct parport_operations`）由负责该端口的低级驱动提供。
- `port->ops->read_data` —— 读取数据寄存器
---------------------------------------------

### 简介
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ..
    unsigned char (*read_data) (struct parport *port);
    ..
};
```

### 描述
^^^^^^^^^^^

如果 `port->modes` 包含 `PARPORT_MODE_TRISTATE` 标志，并且控制寄存器中的 `PARPORT_CONTROL_DIRECTION` 位被设置，则返回数据引脚上的值。如果 `port->modes` 包含 `PARPORT_MODE_TRISTATE` 标志而 `PARPORT_CONTROL_DIRECTION` 位未被设置，则返回值 _可能_ 是写入数据寄存器的最后一个值。否则，返回值是不确定的。
### 参见
^^^^^^^^

`write_data`, `read_status`, `write_control`

### `port->ops->write_data` —— 写入数据寄存器
-----------------------------------------------

### 简介
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ..
    void (*write_data) (struct parport *port, unsigned char d);
    ..
};
### 描述
^^^^^^^^^^^

写入数据寄存器。可能会有副作用（例如，产生一个STROBE脉冲）。
参见
^^^^^^^^

`read_data`，`read_status`，`write_control`

### `port->ops->read_status` - 读取状态寄存器
-------------------------------------------------

### 概要
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ...
    unsigned char (*read_status)(struct parport *port);
    ...
};
```

### 描述
^^^^^^^^^^^

从状态寄存器中读取信息。这是一个位掩码：

- `PARPORT_STATUS_ERROR` （打印机故障，“nFault”）
- `PARPORT_STATUS_SELECT` （在线，“Select”）
- `PARPORT_STATUS_PAPEROUT` （无纸，“PError”）
- `PARPORT_STATUS_ACK` （握手，“nAck”）
- `PARPORT_STATUS_BUSY` （忙，“Busy”）

可能存在其他设置的位
参见
^^^^^^^^

`read_data`，`write_data`，`write_control`

### `port->ops->read_control` - 读取控制寄存器
---------------------------------------------------

### 概要
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ...
    unsigned char (*read_control)(struct parport *port);
    ...
};
```

### 描述
^^^^^^^^^^^

返回最后一次写入控制寄存器的值（来自`write_control`或`frob_control`）。不会执行端口访问操作
参见
^^^^^^^^

`read_data`，`write_data`，`read_status`，`write_control`

### `port->ops->write_control` - 写入控制寄存器
-----------------------------------------------------

### 概要
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ...
    void (*write_control)(struct parport *port, unsigned char s);
    ...
};
```

### 描述
^^^^^^^^^^^

写入控制寄存器。这是一个位掩码：
```
- `PARPORT_CONTROL_STROBE` （nStrobe）
- `PARPORT_CONTROL_AUTOFD` （nAutoFd）
- `PARPORT_CONTROL_INIT` （nInit）
- `PARPORT_CONTROL_SELECT` （nSelectIn）
```
参见
^^^^^^^^

`read_data`，`write_data`，`read_status`，`frob_control`

### `port->ops->frob_control` - 写入控制寄存器中的位
-----------------------------------------------------

### 概要
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ...
```
### 描述

```c
unsigned char (*frob_control) (struct parport *port,
					unsigned char mask,
					unsigned char val);
```

这等同于从控制寄存器中读取值，然后用`mask`屏蔽其中的某些位，并与`val`进行异或操作，最后将结果写回到控制寄存器中。由于某些端口不允许从控制端口读取数据，因此需要维护一个软件副本以记录其内容，因此`frob_control`实际上只涉及一次端口访问。

**参见**

- `read_data`
- `write_data`
- `read_status`
- `write_control`

### `port->ops->enable_irq` - 启用中断生成

#### 概述

```c
#include <linux/parport.h>

struct parport_operations {
	..
void (*enable_irq) (struct parport *port);
	..
};
```

平行端口硬件被指示在适当的时候生成中断，但这些时刻取决于具体的架构。对于PC架构而言，中断通常会在nAck信号上升沿时产生。

**参见**

- `disable_irq`

### `port->ops->disable_irq` - 禁止中断生成

#### 概述

```c
#include <linux/parport.h>

struct parport_operations {
	..
void (*disable_irq) (struct parport *port);
	..
};
```

平行端口硬件被指示不生成中断。注意：这里并不屏蔽中断本身。

**参见**

- `enable_irq`
### 参见
^^^^^^^^

`enable_irq`
---

`port->ops->data_forward` - 启用数据驱动程序
---------------------------------------------

### 概览
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ..
void (*data_forward) (struct parport *port);
    ..
};
```

### 描述
^^^^^^^^^^^

启用8位主机到外设通信的数据线驱动程序。

### 参见
^^^^^^^^

`data_reverse`



`port->ops->data_reverse` - 设置缓冲器为三态
---------------------------------------------

### 概览
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ..
void (*data_reverse) (struct parport *port);
    ..
};
```

### 描述
^^^^^^^^^^^

如果`port->modes`设置了`PARPORT_MODE_TRISTATE`位，则将数据总线置于高阻抗状态。

### 参见
^^^^^^^^

`data_forward`



`port->ops->epp_write_data` - 写入EPP数据
------------------------------------------

### 概览
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
    ..
size_t (*epp_write_data) (struct parport *port, const void *buf,
                    size_t len, int flags);
    ..
};
```

### 描述
^^^^^^^^^^^

以EPP模式写入数据，并返回已写入的字节数。
`flags`参数可以是以下一个或多个值，通过按位或运算组合：

======================= =================================================
`PARPORT_EPP_FAST`   使用快速传输。某些芯片提供16位和32位寄存器。但是，如果传输超时，返回值可能不可靠。
下面是给定内容的中文翻译：

---

### 参见

^^^^^^^^

`epp_read_data`, `epp_write_addr`, `epp_read_addr`

---

#### `port->ops->epp_read_data` - 读取EPP数据
_____________________________________________

##### 概述
^^^^^^^^

:::
```c
#include <linux/parport.h>

struct parport_operations {
    ..
    ssize_t (*epp_read_data) (struct parport *port, void *buf,
                            size_t len, int flags);
    ..
};
```

##### 描述
^^^^^^^^^^^

在EPP模式下读取数据，并返回已读取的字节数。
参数`flags`可以是一个或多个以下标志的按位或组合：

======================= =================================================
`PARPORT_EPP_FAST`       使用快速传输。某些芯片提供16位和32位寄存器。然而，如果传输超时，返回值可能不可靠。
======================= =================================================

### 参见
^^^^^^^^

`epp_write_data`, `epp_write_addr`, `epp_read_addr`

---

#### `port->ops->epp_write_addr` - 写入EPP地址
---------------------------------------------

##### 概述
^^^^^^^^

:::
```c
#include <linux/parport.h>

struct parport_operations {
    ..
    ssize_t (*epp_write_addr) (struct parport *port,
                            const void *buf, size_t len, int flags);
    ..
};
```

##### 描述
^^^^^^^^^^^

写入EPP地址（每次8位），并返回写入的数量。
参数`flags`可以是一个或多个以下标志的按位或组合：

======================= =================================================
`PARPORT_EPP_FAST`       使用快速传输。某些芯片提供16位和32位寄存器。然而，如果传输超时，返回值可能不可靠。
======================= =================================================

（对于此函数而言，`PARPORT_EPP_FAST`是否有意义？）

### 参见
^^^^^^^^

`epp_write_data`, `epp_read_data`, `epp_read_addr`

---

#### `port->ops->epp_read_addr` - 读取EPP地址
-------------------------------------------

##### 概述
^^^^^^^^

:::
```c
#include <linux/parport.h>

struct parport_operations {
    ..
    ssize_t (*epp_read_addr) (struct parport *port, void *buf,
                            size_t len, int flags);
    ..
};
```
### DESCRIPTION
^^^^^^^^^^^

读取 EPP 地址（每个 8 位），并返回读取的数量。
`flags` 参数可以是以下一个或多个值，通过位或操作组合在一起：

======================= =================================================
PARPORT_EPP_FAST         使用快速传输。某些芯片提供 16 位和 32 位寄存器。但是，如果传输超时，则返回值可能不可靠。
======================= =================================================

（PARPORT_EPP_FAST 对此函数有意义吗？）

SEE ALSO
^^^^^^^^

epp_write_data, epp_read_data, epp_write_addr

### port->ops->ecp_write_data - 写入一块 ECP 数据
-----------------------------------------------------

SYNOPSIS
^^^^^^^^

```c
	#include <linux/parport.h>

	struct parport_operations {
		..
size_t (*ecp_write_data) (struct parport *port,
					const void *buf, size_t len, int flags);
		..
};
```

DESCRIPTION
^^^^^^^^^^^

写入一块 ECP 数据。`flags` 参数被忽略
RETURN VALUE
^^^^^^^^^^^^

写入的字节数
SEE ALSO
^^^^^^^^

ecp_read_data, ecp_write_addr

### port->ops->ecp_read_data - 读取一块 ECP 数据
---------------------------------------------------

SYNOPSIS
^^^^^^^^

```c
	#include <linux/parport.h>

	struct parport_operations {
		..
size_t (*ecp_read_data) (struct parport *port,
					void *buf, size_t len, int flags);
		..
};
```

DESCRIPTION
^^^^^^^^^^^

读取一块 ECP 数据。`flags` 参数被忽略
RETURN VALUE
^^^^^^^^^^^^

读取的字节数。注意：可能存在更多未读数据在 FIFO 中。有没有办法停止 FIFO 来防止这种情况？

SEE ALSO
^^^^^^^^

ecp_write_block, ecp_write_addr

### port->ops->ecp_write_addr - 写入一块 ECP 地址
----------------------------------------------------------

SYNOPSIS
^^^^^^^^

```c
	#include <linux/parport.h>

	struct parport_operations {
		..
```
### `ecp_write_addr` 函数描述

**原型：**

```c
size_t (*ecp_write_addr) (struct parport *port,
                          const void *buf, size_t len, int flags);
```

**描述：**

该函数用于写入一组ECP（Extended Capability Port）地址。参数`flags`被忽略。

**返回值：**

返回写入的字节数。

**注意事项：**

该函数可能会使用FIFO（First In First Out，先进先出），如果是这样，则不会返回直到FIFO为空。

**参见：**

- `ecp_read_data`
- `ecp_write_data`


### `nibble_read_data` 函数描述

**原型：**

```c
size_t (*nibble_read_data) (struct parport *port,
                            void *buf, size_t len, int flags);
```

**描述：**

该函数用于在半字节模式下读取一组数据。参数`flags`被忽略。

**返回值：**

返回完整读取的字节数。

**参见：**

- `byte_read_data`
- `compat_write_data`


### `byte_read_data` 函数描述

**原型：**

```c
size_t (*byte_read_data) (struct parport *port,
                          void *buf, size_t len, int flags);
```

**描述：**

该函数用于在字节模式下读取一组数据。

**返回值：**

返回完整读取的字节数。

这些函数定义了与并行端口（parport）相关的操作，并且通常被嵌入到`struct parport_operations`结构体中，用于指定不同的数据传输模式下的读写操作。
---

### 描述
^^^^^^^^^^^

以字节模式读取一块数据。`flags` 参数被忽略。

### 返回值
^^^^^^^^^^^^

所读取的字节数。

### 参见
^^^^^^^^

nibble_read_data, compat_write_data


### 
`port->ops->compat_write_data` - 以兼容模式写入一块数据
--------------------------------------------------------------------------

### 概述
^^^^^^^^

```
#include <linux/parport.h>

struct parport_operations {
	..
size_t (*compat_write_data) (struct parport *port,
					const void *buf, size_t len, int flags);
	..
};
```

### 描述
^^^^^^^^^^^

以兼容模式写入一块数据。`flags` 参数被忽略。

### 返回值
^^^^^^^^^^^^

所写入的字节数。

### 参见
^^^^^^^^

nibble_read_data, byte_read_data
