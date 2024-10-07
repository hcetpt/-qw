SPDX 许可证标识符: GPL-2.0

====================================
FLIC（浮动中断控制器）
====================================

FLIC 处理浮动（非每 CPU）中断，例如 I/O、服务和某些机器检查中断。所有中断都存储在一个与 VM 相关的待处理中断列表中。FLIC 对这个列表执行操作。
仅允许实例化一个 FLIC 实例。
FLIC 提供以下支持：
- 添加中断（KVM_DEV_FLIC_ENQUEUE）
- 检查当前待处理的中断（KVM_FLIC_GET_ALL_IRQS）
- 清除所有待处理的浮动中断（KVM_DEV_FLIC_CLEAR_IRQS）
- 清除一个待处理的浮动 I/O 中断（KVM_DEV_FLIC_CLEAR_IO_IRQ）
- 启用/禁用对客户机透明的异步页面错误
- 注册和修改适配器中断源（KVM_DEV_FLIC_ADAPTER_*）
- 修改 AIS（适配器中断抑制）模式状态（KVM_DEV_FLIC_AISM）
- 在指定的适配器上注入适配器中断（KVM_DEV_FLIC_AIRQ_INJECT）
- 获取/设置所有 AIS 模式状态（KVM_DEV_FLIC_AISM_ALL）

组：
  KVM_DEV_FLIC_ENQUEUE
    将缓冲区及其长度传递给内核，然后注入到待处理中断列表中。
attr->addr 包含指向缓冲区的指针，attr->len 包含缓冲区的长度。
从用户空间复制的数据结构 kvm_s390_irq 的格式定义在 usr/include/linux/kvm.h 中。

KVM_DEV_FLIC_GET_ALL_IRQS
    将所有浮动中断复制到用户空间提供的缓冲区中。
如果缓冲区太小，则返回 -ENOMEM，这是提示用户空间尝试使用更大的缓冲区。
如果内核空间缓冲区分配失败，则返回 -ENOBUFS。
如果复制数据到用户空间失败，则返回 -EFAULT。
所有中断保持待处理状态，即不会从当前待处理中断列表中删除。
attr->addr 包含用户空间地址，所有中断数据将被复制到该缓冲区中。
attr->attr 包含缓冲区的字节大小。

KVM_DEV_FLIC_CLEAR_IRQS
    简单地删除当前待处理浮动中断列表中的所有元素。不会向客户机注入任何中断。

KVM_DEV_FLIC_CLEAR_IO_IRQ
    删除一个（如果存在）子通道的 I/O 中断，该子通道由通过 attr->addr（地址）和 attr->attr（长度）指定的缓冲区传递的子系统标识符确定。

KVM_DEV_FLIC_APF_ENABLE
    启用客户机的异步页面错误。因此，在发生严重页面错误时，主机被允许异步处理此错误并继续运行客户机。

KVM_DEV_FLIC_APF_DISABLE_WAIT
    禁用客户机的异步页面错误，并等待所有已挂起的异步页面错误完成。这是必要的，以在迁移中断列表之前为每个初始化中断触发一个完成中断。

KVM_DEV_FLIC_ADAPTER_REGISTER
    注册一个 I/O 适配器中断源。需要一个 kvm_s390_io_adapter 描述要注册的适配器：

    ```c
    struct kvm_s390_io_adapter {
        __u32 id;
        __u8 isc;
        __u8 maskable;
        __u8 swap;
        __u8 flags;
    };
    ```

    其中，id 包含适配器的唯一 ID，isc 表示要使用的 I/O 中断子类，maskable 表示此适配器是否可以屏蔽（关闭中断），swap 表示指示器是否需要字节交换，flags 包含适配器的其他特性。
    目前定义的 'flags' 值包括：

    - KVM_S390_ADAPTER_SUPPRESSIBLE：适配器受 AIS（适配器中断抑制）功能的影响。此标志仅在启用 AIS 功能时有效。

    未知的标志值将被忽略。

KVM_DEV_FLIC_ADAPTER_MODIFY
    修改现有 I/O 适配器中断源的属性。需要一个 kvm_s390_io_adapter_req 指定适配器和操作：

    ```c
    struct kvm_s390_io_adapter_req {
        __u32 id;
        __u8 type;
        __u8 mask;
        __u16 pad0;
        __u64 addr;
    };
    ```

    id 指定适配器和操作类型。支持的操作包括：

    - KVM_S390_IO_ADAPTER_MASK
      根据 mask 中指定的内容屏蔽或解除屏蔽适配器。

    - KVM_S390_IO_ADAPTER_MAP
      这现在是一个空操作。映射完全由中断路由完成。
KVM_S390_IO_ADAPTER_UNMAP  
现在这是一个无操作指令。映射完全由中断路由处理。

KVM_DEV_FLIC_AISM  
如果启用了AIS功能，则修改指定ISC的适配器中断抑制模式。需要一个kvm_s390_ais_req来描述如下：

```c
struct kvm_s390_ais_req {
    __u8 isc;
    __u16 mode;
};
```

isc 包含目标I/O中断子类，mode 包含目标适配器中断抑制模式。目前支持以下模式：

- KVM_S390_AIS_MODE_ALL: 全部中断模式，即允许注入airq；
- KVM_S390_AIS_MODE_SINGLE: 单次中断模式，即只允许一次airq注入，并且随后的适配器中断将被抑制，直到再次设置为全部中断或单次中断模式。

KVM_DEV_FLIC_AIRQ_INJECT  
在指定适配器上注入适配器中断。
attr->attr 包含适配器的唯一ID，这允许进行特定适配器的检查和操作。
对于受AIS影响的适配器，在AIS功能启用的情况下，根据适配器中断抑制模式处理isc的airq注入抑制。

KVM_DEV_FLIC_AISM_ALL  
获取或设置所有ISC的适配器中断抑制模式。需要一个kvm_s390_ais_all来描述如下：

```c
struct kvm_s390_ais_all {
    __u8 simm; /* 单次中断模式掩码 */
    __u8 nimm; /* 无中断模式掩码 */
};
```

simm 包含所有ISC的单次中断模式掩码，nimm 包含所有ISC的无中断模式掩码。simm 和 nimm 中的每个位对应一个ISC（最高有效位0表示ISC 0等）。simm位和nimm位的组合表示一个ISC的AIS模式。

KVM_DEV_FLIC_AISM_ALL 由 KVM_CAP_S390_AIS_MIGRATION 指示。

注意：在FLIC设备上执行未知组或属性的 KVM_SET_DEVICE_ATTR/KVM_GET_DEVICE_ATTR 设备ioctl时，会返回错误代码EINVAL（而不是API文档中规定的ENXIO）。不能通过尝试使用时产生的错误代码来判断FLIC操作是否不可用。

注意：如果指定了零schid，KVM_DEV_FLIC_CLEAR_IO_IRQ ioctl 将返回EINVAL。
