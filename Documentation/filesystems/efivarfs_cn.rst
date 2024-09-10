SPDX 许可证标识符: GPL-2.0

=======================================
efivarfs - 一个 (U)EFI 变量文件系统
=======================================

efivarfs 文件系统的创建是为了解决使用 sysfs 条目来维护 EFI 变量的不足。旧的 sysfs EFI 变量代码仅支持最多 1024 字节的变量。这一限制存在于 EFI 规范 0.99 版本中，但在任何完整版本发布之前已被移除。由于变量现在可以超过单个页面的大小，因此 sysfs 并不是处理这些变量的最佳接口。通过 efivarfs 文件系统，可以创建、删除和修改变量。
efivarfs 通常像这样挂载：

```
mount -t efivarfs none /sys/firmware/efi/efivars
```

由于存在许多固件错误，即删除非标准 UEFI 变量会导致系统固件无法完成 POST（加电自检），因此 efivarfs 中未被广泛认可的标准变量会被创建为不可更改的文件。这并不会阻止删除操作——“chattr -i”仍然有效——但它确实防止了这种故障被意外触发。

.. warning ::
      当显示 /sys/firmware/efi/efivars 中 UEFI 变量的内容时，例如使用 “hexdump”，请注意输出的前 4 个字节代表 UEFI 变量属性，采用小端格式表示。

实际上，每个 efivar 的输出由以下部分组成：

```
+-----------------------------------+
|4_bytes_of_attributes + efivar_data|
+-----------------------------------+
```

*参见：*

- 文档/admin-guide/acpi/ssdt-overlays.rst
- 文档/ABI/removed/sysfs-firmware-efi-vars
