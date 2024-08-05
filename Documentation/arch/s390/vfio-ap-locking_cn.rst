SPDX 许可证标识符: GPL-2.0

======================
VFIO AP 锁概述
======================
本文档描述了与 vfio_ap 设备驱动程序安全运行相关的锁。在整个文档中，以下变量将用于表示文中所述结构的实例：

.. code-block:: c

  struct ap_matrix_dev *matrix_dev;
  struct ap_matrix_mdev *matrix_mdev;
  struct kvm *kvm;

矩阵设备锁 (drivers/s390/crypto/vfio_ap_private.h)
---------------------------------------------------------------

.. code-block:: c

  struct ap_matrix_dev {
  	..
   struct list_head mdev_list;
   struct mutex mdevs_lock;
   ..
}

矩阵设备锁 (matrix_dev->mdevs_lock) 实现为 struct ap_matrix_dev 单个对象中的全局互斥锁。此锁控制对每个 matrix_mdev (matrix_dev->mdev_list) 中包含的所有字段的访问。在读取、写入或使用 matrix_mdev 实例中的字段数据时必须持有此锁，该实例代表 vfio_ap 设备驱动程序的一个中介设备。
KVM 锁 (include/linux/kvm_host.h)
---------------------------------------

.. code-block:: c

  struct kvm {
  	..
   struct mutex lock;
   ..
}

KVM 锁 (kvm->lock) 控制对 KVM 客户机的状态数据的访问。当一个或多个 AP 适配器、域或控制域被插入到或从客户机拔出时，vfio_ap 设备驱动程序必须持有此锁。KVM 指针存储在包含已附加到 KVM 客户机的中介设备状态的 matrix_mdev 实例中 (matrix_mdev->kvm = kvm)。
客户机锁 (drivers/s390/crypto/vfio_ap_private.h)
-----------------------------------------------------------

.. code-block:: c

  struct ap_matrix_dev {
  	..
   struct list_head mdev_list;
   struct mutex guests_lock;
   ..
}

客户机锁 (matrix_dev->guests_lock) 控制对 matrix_mdev 实例 (matrix_dev->mdev_list) 的访问，这些实例代表了包含已附加到 KVM 客户机的中介设备状态的中介设备。此锁必须持有：

1. 在 vfio_ap 设备驱动程序使用它来将 AP 设备插入/拔出到 KVM 客户机时，控制对 KVM 指针 (matrix_mdev->kvm) 的访问。
### 翻译成中文：

2. 向 `matrix_dev->mdev_list` 添加或从中移除 `matrix_mdev` 实例
为了确保在遍历列表以查找用于将 AP 设备接入/拔出到 KVM 客户机的 `ap_matrix_mdev` 实例时，锁定顺序正确，这是必要的。
例如，当从 vfio_ap 设备驱动程序中移除队列设备时，如果适配器被接入到 KVM 客户机，则必须将其拔出。为了确定适配器是否已被接入，需要找到分配给该队列的 `matrix_mdev` 对象。然后可以使用 KVM 指针 (`matrix_mdev->kvm`) 来判断中介设备是否已接入（`matrix_mdev->kvm != NULL`），如果是，则拔出适配器。

如果不使用 KVM 指针来接入/拔出接入到 KVM 客户机的设备，则无需获取 Guest 锁来访问 KVM 指针；但是，在这种情况下，为了访问 KVM 指针，必须持有 Matrix 设备锁 (`matrix_dev->mdevs_lock`)，因为 KVM 指针是在 Matrix 设备锁保护下设置和清除的。一个例子是处理 PQAP(AQIC) 指令子函数拦截的函数。这个处理器只需要访问 KVM 指针来设置或清除 IRQ 资源，因此只需持有 `matrix_dev->mdevs_lock`。

### PQAP Hook 锁 (arch/s390/include/asm/kvm_host.h)

---

```c
typedef int (*crypto_hook)(struct kvm_vcpu *vcpu);

struct kvm_s390_crypto {
  	..
  	struct rw_semaphore pqap_hook_rwsem;
  	crypto_hook *pqap_hook;
  	..
};
```

PQAP Hook 锁是一个读写信号量，它控制对处理器 `(*kvm->arch.crypto.pqap_hook)` 的函数指针的访问，该处理器在主机拦截 PQAP(AQIC) 指令子函数时被调用。设置 `pqap_hook` 值时必须以写模式持有此锁，并在调用 `pqap_hook` 函数时以读模式持有此锁。
