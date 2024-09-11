=====================
HID 传感器框架
=====================

HID 传感器框架提供了必要的接口以实现与传感器集线器相连的传感器驱动程序。该传感器集线器是一个 HID 设备，并提供符合 HID 1.12 传感器使用表的报告描述符。

根据 HID 1.12 “HID 传感器使用”规范中的描述：
“对传感器硬件使用的 HID 标准化将允许（但不要求）传感器硬件供应商在 USB 边界处提供一致的即插即用接口，从而使得一些操作系统能够整合通用设备驱动程序，这些驱动程序可以在不同的供应商之间重用，免除供应商自行提供驱动程序的需求。”

此规范定义了许多使用 ID，它们描述了传感器类型及各个数据字段。每个传感器可以有不同数量的数据字段。字段的长度和顺序在报告描述符中指定。例如，报告描述符的一部分可能如下所示：

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

报告表明“传感器页面 (0x20)”包含一个三维加速度计 (0x73)。这个三维加速度计有一些字段。例如，字段 2 是运动强度 (0x045f)，其逻辑最小值为 -32767，逻辑最大值为 32767。字段的顺序和每个字段的长度非常重要，因为输入事件原始数据将使用这种格式。

实施
==============

此规范定义了许多不同类型且具有不同数据字段集的传感器。对于不同类型的传感器，很难有一个统一的用户空间应用程序输入事件。例如，加速度计可以发送 X、Y 和 Z 数据，而环境光传感器可以发送光照数据。

因此，实施分为两部分：

- 核心 HID 驱动程序
- 单个传感器处理部分（传感器驱动程序）

核心驱动程序
-----------
核心驱动程序（hid-sensor-hub）注册为 HID 驱动程序。它解析报告描述符并识别所有存在的传感器。它会添加一个名为 HID-SENSOR-xxxx 的 MFD 设备（其中 xxxx 是来自规范的使用 ID）。
例如：

HID-SENSOR-200073 注册用于三维加速度计驱动程序
如果插入任何具有此名称的驱动程序，则将调用该功能的探测例程。因此，如果检测到三维加速度计，加速度计处理驱动程序可以注册此名称并被探测。
核心驱动程序提供了一组API，处理驱动程序可以使用这些API来注册和获取特定使用ID的事件。此外，它还提供了解析函数，用于获取和设置每个输入/特性/输出报告。
单独的传感器处理部分（传感器驱动程序）
--------------------------------------------

处理驱动程序将使用核心驱动程序提供的接口来解析报告并获取字段的索引，还可以获取事件。这个驱动程序可以使用IIO接口来使用为某种类型的传感器定义的标准ABI。
核心驱动程序接口
==================

回调结构：
```
每个处理驱动程序都可以使用此结构来设置一些回调函数。
int (*suspend)(..): 在接收到HID挂起时的回调函数
int (*resume)(..): 在接收到HID恢复时的回调函数
int (*capture_sample)(..): 为其中一个数据字段捕获一个样本
int (*send_event)(..): 接收到一个完整的事件，该事件可能包含多个数据字段
```

注册函数：
```
int sensor_hub_register_callback(struct hid_sensor_hub_device *hsdev,
                                 u32 usage_id,
                                 struct hid_sensor_hub_callbacks *usage_callback);

为一个使用ID注册回调函数。回调函数不允许休眠。

int sensor_hub_remove_callback(struct hid_sensor_hub_device *hsdev,
                               u32 usage_id);

移除一个使用ID的回调函数。
```

解析函数：
```
int sensor_hub_input_get_attribute_info(struct hid_sensor_hub_device *hsdev,
                                        u8 type,
                                        u32 usage_id, u32 attr_usage_id,
                                        struct hid_sensor_hub_attribute_info *info);

处理驱动程序可以查找感兴趣的某些字段，并检查它们是否存在于报告描述符中。如果存在，则存储必要的信息以便能够单独设置或获取字段。
这些索引避免了每次都需要搜索并获取字段索引来设置或获取值。
```

设置特征报告：
```
int sensor_hub_set_feature(struct hid_sensor_hub_device *hsdev, u32 report_id,
                           u32 field_index, s32 value);

此接口用于设置特征报告中的某个字段的值。例如，如果有一个报告间隔字段，通过调用`sensor_hub_input_get_attribute_info`解析后，可以直接设置该字段。
```

获取特征报告：
```
int sensor_hub_get_feature(struct hid_sensor_hub_device *hsdev, u32 report_id,
                           u32 field_index, s32 *value);

此接口用于获取输入报告中的某个字段的值。例如，如果有一个报告间隔字段，通过调用`sensor_hub_input_get_attribute_info`解析后，可以直接获取该字段的值。
```

获取原始值：
```
int sensor_hub_input_attr_get_raw_value(struct hid_sensor_hub_device *hsdev,
                                        u32 usage_id,
                                        u32 attr_usage_id, u32 report_id);

此接口用于通过输入报告获取特定字段的值。例如，加速度计想要轮询X轴的值，那么它可以使用X轴的使用ID调用此函数。由于HID传感器可以提供事件，因此通常不需要轮询任何字段。如果有新的样本，核心驱动程序将调用已注册的回调函数来处理样本。
```

HID自定义和通用传感器
------------------------

HID传感器规范定义了两种特殊的传感器使用类型。由于它们不代表标准传感器，因此无法使用Linux IIO类型的接口来定义。
这些传感器的目的是扩展功能或提供一种混淆传感器通信数据的方式。如果没有数据与其封装形式之间的映射关系，应用程序/驱动程序很难确定传感器正在通信的数据是什么。
这允许一些区分性的使用场景，其中供应商可以提供应用程序。一些常见的使用场景包括调试其他传感器或提供一些事件，如键盘的插入/拔出或盖子的打开/关闭。

为了使应用程序能够利用这些传感器，这里通过sysfs属性组、属性和misc设备接口导出了这些传感器。以下是sysfs表示的一个示例：

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

这里有一个自定义传感器，包含四个字段：两个特性（feature）和两个输入（input）。每个字段由一组属性表示。除了“值”字段外，所有字段都是只读的。“值”字段是可读写的。
示例如下：

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

如何启用这样的传感器？
^^^^^^^^^^^^^^^^^^^^^^^^^^

默认情况下，传感器可能被电源门控。要启用它，可以使用sysfs属性“enable”：

```
$ echo 1 > enable_sensor
```

一旦启用并上电后，传感器可以通过HID报告报告值。这些报告通过misc设备接口以FIFO顺序推送：

```
/dev$ tree | grep HID-SENSOR-2000e1.6.auto
│   │   │   ├── 10:53 -> ../HID-SENSOR-2000e1.6.auto
│   ├──  HID-SENSOR-2000e1.6.auto
```

每个报告可以是可变长度的，并且前面有一个头部。这个头部包含一个32位的用途ID、64位的时间戳和32位的原始数据长度字段。
