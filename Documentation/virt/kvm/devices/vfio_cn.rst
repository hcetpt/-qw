SPDX 许可证标识符: GPL-2.0

===================
VFIO 虚拟设备
===================

支持的设备类型：

  - KVM_DEV_TYPE_VFIO

每个虚拟机只能创建一个 VFIO 实例。创建的设备会跟踪虚拟机使用的 VFIO 文件（组或设备），以及这些组/设备中对虚拟机正确性和加速重要的特性。当这些组/设备被启用和禁用时，应该更新 KVM 关于它们的存在情况。当注册到 KVM 时，会持有 VFIO 文件的引用。
组：
  KVM_DEV_VFIO_FILE
	别名：KVM_DEV_VFIO_GROUP

KVM_DEV_VFIO_FILE 属性：
  KVM_DEV_VFIO_FILE_ADD：将一个 VFIO 文件（组/设备）添加到 VFIO-KVM 设备跟踪中

	kvm_device_attr.addr 指向一个 int32_t 文件描述符，用于 VFIO 文件
KVM_DEV_VFIO_FILE_DEL：从 VFIO-KVM 设备跟踪中移除一个 VFIO 文件（组/设备）

	kvm_device_attr.addr 指向一个 int32_t 文件描述符，用于 VFIO 文件
KVM_DEV_VFIO_GROUP（仅限处理 VFIO 组 fd 的旧版 kvm 设备组）：
  KVM_DEV_VFIO_GROUP_ADD：仅对于组 fd，与 KVM_DEV_VFIO_FILE_ADD 相同

  KVM_DEV_VFIO_GROUP_DEL：仅对于组 fd，与 KVM_DEV_VFIO_FILE_DEL 相同

  KVM_DEV_VFIO_GROUP_SET_SPAPR_TCE：附加由 sPAPR KVM 分配的访客可见的 TCE 表

kvm_device_attr.addr 指向一个结构体：

		struct kvm_vfio_spapr_tce {
			__s32	groupfd;
			__s32	tablefd;
		};

	其中：

	- @groupfd 是一个 VFIO 组的文件描述符；
	- @tablefd 是通过 KVM_CREATE_SPAPR_TCE 分配的 TCE 表的文件描述符；

上述 FILE/GROUP_ADD 操作应在通过 VFIO_GROUP_GET_DEVICE_FD 访问设备文件描述符之前调用，以支持需要在其 .open_device() 回调中设置 kvm 指针的驱动程序。同样，通过字符设备 open 获取设备访问权限并使用 VFIO_DEVICE_BIND_IOMMUFD 的文件描述符也应如此。对于此类文件描述符，应在 VFIO_DEVICE_BIND_IOMMUFD 之前调用 FILE_ADD，以支持前面提到的驱动程序。
