=============================
S/390 驱动模型接口
=============================

1. CCW 设备
--------------

所有可以通过 CCW 地址寻址的设备都称为“CCW 设备”——即使它们实际上并非由 CCW 驱动。
所有的 CCW 设备都是通过子通道访问的，这反映在 devices/ 目录下的结构中：

```
devices/
   - system/
   - css0/
     - 0.0.0000/0.0.0815/
     - 0.0.0001/0.0.4711/
     - 0.0.0002/
     - 0.1.0000/0.1.1234/
     ...
- defunct/
```

在这个例子中，设备 0815 通过子通道集 0 中的子通道 0 访问；设备 4711 通过子通道集 0 中的子通道 1 访问；而子通道 2 是一个非 I/O 子通道。设备 1234 通过子通道集 1 中的子通道 0 访问。
名为 "defunct" 的子通道不代表系统上的任何实际子通道；它是一个伪子通道，当其他 CCW 设备在其原来的子通道上变得可操作时，被替换的 CCW 设备将被移动到该伪子通道。如果这些 CCW 设备再次在其原来的子通道上变得可操作，它们将再次被移动到正确的子通道上。

您应该通过其总线 ID（例如 0.0.4711）来访问 CCW 设备；可以在 bus/ccw/devices/ 下找到该设备。
所有 CCW 设备都会通过 sysfs 导出一些数据：
- cutype:
    控制单元类型/型号
- devtype:
    设备类型/型号（如果适用）
- availability:
    可能是 'good' 或 'boxed'；对于断开连接的设备则为 'no path' 或 'no device'
- online:
    用于设置设备在线或离线的接口
在设备断开这一特殊情况中（参见1.2节中的通知功能），将0管道到在线状态会强制删除该设备。

设备驱动程序可以添加条目来导出每个设备的数据和接口。
此外，还有一些数据是按子通道基础导出的（参见`bus/css/devices/`下的内容）：

chpids：
	通过哪些chpid连接该设备
pimpampom：
	已安装路径、可用路径和运行中路径的掩码
也可能存在其他额外数据，例如对于块设备。

1.1 启用ccw设备
------------------

这一过程分为几个步骤：
a. 每个驱动程序可以提供一个或多个参数接口，在这些接口中可以指定参数。这些接口也由驱动程序负责管理。
b. 完成a步骤后，如果需要的话，最终通过“在线”接口启用设备。

1.2 编写ccw设备的驱动程序
-----------------------------

基本的`struct ccw_device`和`struct ccw_driver`数据结构可以在`include/asm/ccwdev.h`中找到：

```c
  struct ccw_device {
	spinlock_t *ccwlock;
	struct ccw_device_private *private;
	struct ccw_device_id id;

	struct ccw_driver *drv;
	struct device dev;
	int online;

	void (*handler) (struct ccw_device *dev, unsigned long intparm,
			 struct irb *irb);
  };

  struct ccw_driver {
	struct module *owner;
	struct ccw_device_id *ids;
	int (*probe) (struct ccw_device *);
	int (*remove) (struct ccw_device *);
	int (*set_online) (struct ccw_device *);
	int (*set_offline) (struct ccw_device *);
	int (*notify) (struct ccw_device *, int);
	struct device_driver driver;
	char *name;
  };
```

"private"字段包含仅用于内部I/O操作所需的数据，并不对设备驱动程序开放。
每个驱动程序都应该在其MODULE_DEVICE_TABLE声明它所感兴趣的CU类型/型号和/或设备类型/型号。这些信息稍后可以在`struct ccw_device_id`字段中找到：

```c
  struct ccw_device_id {
	__u16   match_flags;

	__u16   cu_type;
	__u16   dev_type;
	__u8    cu_model;
	__u8    dev_model;

	unsigned long driver_info;
  };
```

ccw_driver中的函数应以如下方式使用：

probe：
	此函数由设备层为每个驱动程序感兴趣的设备调用。驱动程序应该只分配私有结构体放入`dev->driver_data`中并创建属性（如果需要）。同时，中断处理程序（参见下文）也应该在这里设置。
这些是Linux内核中与ccw设备相关的回调函数的描述。下面是对应的中文翻译：

### `probe` 函数

**类型定义：**

```c
int (*probe) (struct ccw_device *cdev);
```

**参数：**

- `cdev`: 要探测的设备。

### `remove` 函数

**描述：**

此函数由设备层在移除驱动程序、设备或模块时调用。驱动程序应该在这里执行清理操作。

**类型定义：**

```c
int (*remove) (struct ccw_device *cdev);
```

**参数：**

- `cdev`: 要移除的设备。

### `set_online` 函数

**描述：**

当通过 "online" 属性激活设备时，此函数由通用I/O层调用。驱动程序应在此处最终设置并激活设备。

**类型定义：**

```c
int (*set_online) (struct ccw_device *);
```

**参数：**

- `cdev`: 要激活的设备。通用层已验证该设备尚未在线。

### `set_offline` 函数

**描述：**

当通过 "online" 属性使设备停用时，此函数由通用I/O层调用。驱动程序应关闭设备，但不应取消分配其私有数据。

**类型定义：**

```c
int (*set_offline) (struct ccw_device *);
```

**参数：**

- `cdev`: 要停用的设备。通用层已验证该设备在线。

### `notify` 函数

**描述：**

此函数由通用I/O层为某些设备状态变化调用。

向驱动程序通知以下情况：

- 在在线状态下，设备被分离 (`CIO_GONE`) 或最后一条路径丢失 (`CIO_NO_PATH`)。驱动程序必须返回非零值以保留该设备；对于返回码为0的情况，设备将如常被删除（即使没有注册通知函数也是如此）。如果驱动程序希望保留设备，则将其移至断开连接状态。
- 在断开连接状态下，设备再次变为可操作 (`CIO_OPER`)。通用I/O层对设备编号和设备/控制单元进行一些合理性检查，以确定是否仍为同一设备。
如果不行，则移除旧设备并注册新设备。通过通知函数的返回码，设备驱动程序指示是否需要保留该设备：非0表示保留，0表示移除并重新注册该设备。

```c
int (*notify) (struct ccw_device *, int);
```

参数：
- `cdev` —— 状态发生变化的设备
- `event` —— 发生的事件。这可以是 CIO_GONE、CIO_NO_PATH 或 CIO_OPER 中的一个

结构体 `ccw_device` 的 `handler` 字段意在设置为该设备的中断处理程序。为了容纳使用多个不同处理程序的驱动程序（例如多子通道设备），这是 `ccw_device` 成员而非 `ccw_driver` 的成员。
中断处理程序在 `set_online()` 处理过程中与通用层进行注册，在调用驱动程序之前，且在 `set_offline()` 调用之后进行注销。另外，在注册后/注销前，执行路径分组或解散路径分组（如适用）。

```c
void (*handler) (struct ccw_device *dev, unsigned long intparm, struct irb *irb);
```

参数：
- `dev` —— 被调用处理程序的设备
- `intparm` —— 使设备驱动程序能够识别与中断相关联的 I/O，或者识别中断为未被请求的整数参数
- `irb` —— 包含累积状态的中断响应块

设备驱动程序从通用的 `ccw_device` 层调用，并可以从 `irb` 参数中获取有关中断的信息。

### 1.3 ccwgroup 设备
#### --------------------

ccwgroup 机制旨在处理由多个 `ccw` 设备组成的设备，如 LCS 或 CTC。

ccw 驱动程序提供了一个“group”属性。将 `ccw` 设备的总线 ID 传递给这个属性，可以创建一个包含这些 `ccw` 设备的 `ccwgroup` 设备（如果可能）。这个 `ccwgroup` 设备可以像普通 `ccw` 设备一样设置为在线或离线。
每个`ccwgroup`设备还提供了一个‘ungroup’属性，用于再次销毁该设备（仅在离线状态下）。这是一个通用的`ccwgroup`机制（驱动程序不需要实现除正常移除例程之外的任何内容）。
一个属于`ccwgroup`设备的`ccw`设备在其设备结构体中的`driver_data`字段中会保存指向该`ccwgroup`设备的指针。驱动程序不应触碰此字段——它应该使用`ccwgroup`设备的`driver_data`来存储其私有数据。
要实现一个`ccwgroup`驱动程序，请参阅`include/asm/ccwgroup.h`。请注意，大多数驱动程序都需要同时实现一个`ccwgroup`和一个`ccw`驱动程序。
2. 通道路径
--------------

通道路径像子通道一样，出现在通道子系统根目录(css0)下，并命名为`chp0.<chpid>`。它们没有驱动程序且不属于任何总线。
请注意，与2.4版本中的`/proc/chpids`不同，通道路径对象仅反映逻辑状态而不是物理状态，因为我们无法由于缺乏机器支持而一致地跟踪后者（实际上我们也不需要知道它）。
状态
- 可以是“在线”或“离线”
向其中写入“on”或“off”将使`chpid`逻辑上变为在线或离线
向在线的`chpid`写入“on”将触发对其连接的所有设备的路径重新探测。这可以用来强制内核重用用户已知为在线但机器尚未为此创建机器检查的通道路径
类型
- 通道路径的物理类型
共享
- 通道路径是否为共享
### 通道测量组 (Cmg)

- **通道测量组**

### 3. 系统设备

#### 3.1 xpram

`xpram` 在 `devices/system/` 下显示为 `xpram`。

#### 3.2 CPU

对于每个CPU，在 `devices/system/cpu/` 下创建一个目录。每个CPU都有一个属性 `online`，其值可以是0或1。

### 4. 其他设备

#### 4.1 Netiucv

- **Netiucv驱动** 在 `bus/iucv/drivers/netiucv` 下创建了一个属性 `connection`。向这个属性管道写入信息可以建立一个新的到指定主机的 `netiucv` 连接。
- `Netiucv` 连接在 `devices/iucv/` 下显示为 `"netiucv<ifnum>"`。接口编号按通过 `connection` 属性定义的连接顺序依次分配。

- **user**：显示连接伙伴。
- **buffer**：最大缓冲区大小。可以通过管道写入更改缓冲区大小。
