```python
# -*- coding: utf-8; mode: python -*-

# SPDX-License-Identifier: GPL-2.0

project = 'Linux Media Subsystem 文档'

# 可以使用以下命令运行 Sphinx 的 nitpicky 模式：
nitpicky = True

# 在 nitpicky 构建中，不引用任何 intersphinx 对象
intersphinx_mapping = {}

# 在 nitpicky 模式下，它会抱怨许多缺失的引用：
#
# 1) 仅仅是类型定义，如：bool, __u32 等；
# 2) 它会抱怨像 enum, NULL 这样的内容；
# 3) 它会抱怨应该在其他书籍中的符号（但目前尚未移植到 ReST）
#
# 下面的列表包含了一组在 nitpicky 模式下应忽略的符号
#
nitpick_ignore = [
    ("c:func", "clock_gettime"),
    ("c:func", "close"),
    ("c:func", "container_of"),
    ("c:func", "copy_from_user"),
    ("c:func", "copy_to_user"),
    ("c:func", "determine_valid_ioctls"),
    ("c:func", "ERR_PTR"),
    ("c:func", "i2c_new_client_device"),
    ("c:func", "ioctl"),
    ("c:func", "IS_ERR"),
    ("c:func", "KERNEL_VERSION"),
    ("c:func", "mmap"),
    ("c:func", "open"),
    ("c:func", "pci_name"),
    ("c:func", "poll"),
    ("c:func", "PTR_ERR"),
    ("c:func", "read"),
    ("c:func", "release"),
    ("c:func", "set"),
    ("c:func", "struct fd_set"),
    ("c:func", "struct pollfd"),
    ("c:func", "usb_make_path"),
    ("c:func", "wait_finish"),
    ("c:func", "wait_prepare"),
    ("c:func", "write"),

    ("c:type", "atomic_t"),
    ("c:type", "bool"),
    ("c:type", "boolean"),
    ("c:type", "buf_queue"),
    ("c:type", "device"),
    ("c:type", "device_driver"),
    ("c:type", "device_node"),
    ("c:type", "enum"),
    ("c:type", "fd"),
    ("c:type", "fd_set"),
    ("c:type", "file"),
    ("c:type", "i2c_adapter"),
    ("c:type", "i2c_board_info"),
    ("c:type", "i2c_client"),
    ("c:type", "int16_t"),
    ("c:type", "ktime_t"),
    ("c:type", "led_classdev_flash"),
    ("c:type", "list_head"),
    ("c:type", "lock_class_key"),
    ("c:type", "module"),
    ("c:type", "mutex"),
    ("c:type", "NULL"),
    ("c:type", "off_t"),
    ("c:type", "pci_dev"),
    ("c:type", "pdvbdev"),
    ("c:type", "poll_table"),
    ("c:type", "platform_device"),
    ("c:type", "pollfd"),
    ("c:type", "poll_table_struct"),
    ("c:type", "s32"),
    ("c:type", "s64"),
    ("c:type", "sd"),
    ("c:type", "size_t"),
    ("c:type", "spi_board_info"),
    ("c:type", "spi_device"),
    ("c:type", "spi_master"),
    ("c:type", "ssize_t"),
    ("c:type", "fb_fix_screeninfo"),
    ("c:type", "pollfd"),
    ("c:type", "timeval"),
    ("c:type", "video_capability"),
    ("c:type", "timeval"),
    ("c:type", "__u16"),
    ("c:type", "u16"),
    ("c:type", "__u32"),
    ("c:type", "u32"),
    ("c:type", "__u64"),
    ("c:type", "u64"),
    ("c:type", "u8"),
    ("c:type", "uint16_t"),
    ("c:type", "uint32_t"),
    ("c:type", "union"),
    ("c:type", "__user"),
    ("c:type", "usb_device"),
    ("c:type", "usb_interface"),
    ("c:type", "v4l2_std_id"),
    ("c:type", "video_system_t"),
    ("c:type", "vm_area_struct"),

    # 不透明结构体

    ("c:type", "v4l2_m2m_dev"),
]
```
