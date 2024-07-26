=====================
HID 传感器框架
=====================

HID 传感器框架提供了必要的接口以实现与传感器中心相连的传感器驱动程序。传感器中心是一个 HID 设备，并提供符合 HID 1.12 传感器用途表的报告描述符。

根据 HID 1.12 “HID 传感器用途”规范中的描述：
“为传感器标准化 HID 用途将允许（但不强制）传感器硬件供应商在 USB 边界处提供一致的即插即用接口，从而使得某些操作系统可以集成通用设备驱动程序，这些驱动程序可以在不同的供应商之间重用，减轻供应商自行提供驱动程序的需求。”

本规范描述了许多用途 ID，它们描述了传感器的类型以及各个数据字段。每个传感器可以有可变数量的数据字段。字段的长度和顺序在报告描述符中指定。例如，报告描述符的一部分可能如下所示：

```
INPUT(1)[INPUT]
.
Field(2)
        Physical(0020.0073)
        Usage(1)
          0020.045f
        Logical Minimum(-32767)
        Logical Maximum(32767)
        Report Size(8)
        Report Count(1)
        Report Offset(16)
        Flags(Variable Absolute)
.
.
```

该报告指出“传感器页 (0x20)”包含一个三维加速度计 (0x73)。
这个三维加速度计有一些字段。例如，字段 2 是运动强度 (0x045f)，其逻辑最小值为 -32767，逻辑最大值为 32767。字段的顺序和每个字段的长度很重要，因为输入事件原始数据将使用此格式。

实施
==============

本规范定义了多种不同类型的传感器及其不同的数据字段集。对于不同类型的传感器来说，很难为用户空间应用程序提供一个通用的输入事件。例如，加速度计可以发送 X、Y 和 Z 数据，而环境光传感器可以发送光照数据。

因此，实现分为两部分：

- 核心 HID 驱动程序
- 个别传感器处理部分（传感器驱动程序）

核心驱动程序
-------------

核心驱动程序 (hid-sensor-hub) 注册为一个 HID 驱动程序。它解析报告描述符并识别所有存在的传感器。它添加了一个名为 HID-SENSOR-xxxx 的 MFD 设备（其中 xxxx 是规范中的用途 ID）。
例如：

为三维加速度计驱动程序注册了 HID-SENSOR-200073
如果插入具有此名称的任何驱动程序，则将调用该功能的探测例程。因此，如果检测到三维加速度计，处理加速度计的驱动程序可以注册此名称并被探测。
核心驱动提供了一组API，这些API可以被处理驱动用来为特定的使用ID注册和获取事件。此外，它还提供了解析函数，用于获取和设置每个输入/特性/输出报告。
单独的传感器处理部分（传感器驱动）
-------------------------------------

处理驱动将使用由核心驱动提供的接口来解析报告并获取字段的索引，同时也可以获取事件。此驱动可以通过IIO接口来利用为某种类型的传感器定义的标准ABI。
核心驱动接口
=============

回调结构如下：

  每个处理驱动都可以使用这个结构来设置一些回调：
- `int (*suspend)(..)`：当接收到HID挂起时的回调
- `int (*resume)(..)`：当接收到HID恢复时的回调
- `int (*capture_sample)(..)`：为其中一个数据字段捕获一个样本
- `int (*send_event)(..)`：当接收到一个完整的事件时的回调，该事件可能包含多个数据字段

注册函数如下：

  `int sensor_hub_register_callback(struct hid_sensor_hub_device *hsdev, u32 usage_id, struct hid_sensor_hub_callbacks *usage_callback);`

为一个使用ID注册回调函数。回调函数不允许睡眠。

  `int sensor_hub_remove_callback(struct hid_sensor_hub_device *hsdev, u32 usage_id);`

移除一个使用ID的回调函数。

解析函数如下：

  `int sensor_hub_input_get_attribute_info(struct hid_sensor_hub_device *hsdev, u8 type, u32 usage_id, u32 attr_usage_id, struct hid_sensor_hub_attribute_info *info);`

处理驱动可以查找感兴趣的某些字段，并检查这些字段是否存在于报告描述符中。如果存在，则会存储必要的信息以便能够单独设置或获取字段。这些索引避免了每次都需要搜索和获取字段索引来进行设置或获取的情况。
设置特性报告：

  `int sensor_hub_set_feature(struct hid_sensor_hub_device *hsdev, u32 report_id, u32 field_index, s32 value);`

此接口用于设置特征报告中字段的值。例如，如果有一个报告间隔字段，该字段在之前通过`sensor_hub_input_get_attribute_info`调用解析过，那么可以直接设置该独立字段。

  `int sensor_hub_get_feature(struct hid_sensor_hub_device *hsdev, u32 report_id, u32 field_index, s32 *value);`

此接口用于获取输入报告中字段的值。例如，如果有一个报告间隔字段，该字段在之前通过`sensor_hub_input_get_attribute_info`调用解析过，那么可以直接获取该独立字段的值。

  `int sensor_hub_input_attr_get_raw_value(struct hid_sensor_hub_device *hsdev, u32 usage_id, u32 attr_usage_id, u32 report_id);`

此接口用于通过输入报告获取特定字段的值。例如，加速度计想要轮询X轴的值，那么它可以调用此函数，并传入X轴的使用ID。由于HID传感器可以提供事件，因此通常不需要轮询任何字段。如果有新的样本，核心驱动将会调用已注册的回调函数来处理该样本。

---

HID自定义与通用传感器
------------------------

HID传感器规范定义了两种特殊的传感器使用类型。由于它们不代表标准传感器，因此无法使用Linux IIO类型接口进行定义。
这些传感器的目的是扩展功能或者提供一种方式来混淆传感器通信的数据。如果不了解数据与其封装形式之间的映射关系，应用程序/驱动程序很难确定传感器正在通信的是什么数据。
这允许一些具有区分性的使用场景，其中供应商可以提供应用程序。
一些常见的使用场景包括调试其他传感器或提供一些事件，如
键盘的连接/断开或盖子的打开/关闭。
为了使应用程序能够利用这些传感器，这里通过 sysfs
属性组、属性和杂项设备接口将它们导出。
这种表示在 sysfs 上的一个示例如下：

```
/sys/devices/pci0000:00/INT33C2:00/i2c-0/i2c-INT33D1:00/0018:8086:09FA.0001/HID-SENSOR-2000e1.6.auto$
tree -R
│   ├──  enable_sensor
  │   │   ├── feature-0-200316
  │   │   │   ├── feature-0-200316-maximum
  │   │   │   ├── feature-0-200316-minimum
  │   │   │   ├── feature-0-200316-name
  │   │   │   ├── feature-0-200316-size
  │   │   │   ├── feature-0-200316-unit-expo
  │   │   │   ├── feature-0-200316-units
  │   │   │   ├── feature-0-200316-value
  │   │   ├── feature-1-200201
  │   │   │   ├── feature-1-200201-maximum
  │   │   │   ├── feature-1-200201-minimum
  │   │   │   ├── feature-1-200201-name
  │   │   │   ├── feature-1-200201-size
  │   │   │   ├── feature-1-200201-unit-expo
  │   │   │   ├── feature-1-200201-units
  │   │   │   ├── feature-1-200201-value
  │   │   ├── input-0-200201
  │   │   │   ├── input-0-200201-maximum
  │   │   │   ├── input-0-200201-minimum
  │   │   │   ├── input-0-200201-name
  │   │   │   ├── input-0-200201-size
  │   │   │   ├── input-0-200201-unit-expo
  │   │   │   ├── input-0-200201-units
  │   │   │   ├── input-0-200201-value
  │   │   ├── input-1-200202
  │   │   │   ├── input-1-200202-maximum
  │   │   │   ├── input-1-200202-minimum
  │   │   │   ├── input-1-200202-name
  │   │   │   ├── input-1-200202-size
  │   │   │   ├── input-1-200202-unit-expo
  │   │   │   ├── input-1-200202-units
  │   │   │   ├── input-1-200202-value
```

这里有一个自定义传感器，包含四个字段：两个特性（feature）和两个输入（input）
每个字段由一组属性表示。除了“值”（value）字段外的所有字段都是只读的。
值字段是可读写的。
示例：

```
/sys/bus/platform/devices/HID-SENSOR-2000e1.6.auto/feature-0-200316$ grep -r . *
feature-0-200316-maximum:6
feature-0-200316-minimum:0
feature-0-200316-name:property-reporting-state
feature-0-200316-size:1
feature-0-200316-unit-expo:0
feature-0-200316-units:25
feature-0-200316-value:1
```

如何启用此类传感器？
^^^^^^^^^^^^^^^^^^^^^^^^^^

默认情况下，传感器可能被电源门控。要启用它，可以使用 sysfs 属性 "enable" ：

```
$ echo 1 > enable_sensor
```

启用并供电后，传感器可以通过 HID 报告报告值。
这些报告通过杂项设备接口以先进先出 (FIFO) 的顺序推送：

```
/dev$ tree | grep HID-SENSOR-2000e1.6.auto
│   │   │   ├── 10:53 -> ../HID-SENSOR-2000e1.6.auto
│   ├──  HID-SENSOR-2000e1.6.auto
```

每个报告的长度可变，并且前面有一个报头。此报头
包含一个32位的用途ID，一个64位的时间戳和一个32位的原始数据长度字段。
