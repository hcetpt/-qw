### SPDX 许可证标识符: GPL-2.0

#### TTY 结构体

##### 目录
* 本地目录

结构体 `tty_struct` 在 TTY 设备首次打开时由TTY层分配，并在最后一次关闭后释放。TTY层将此结构体传递给大多数 `struct tty_operations` 的钩子函数。`tty_struct` 的成员在下面的 `TTY 结构体参考` 中有详细说明。

##### 初始化

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_init_termios
```

#### 名称

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_name
```

#### 引用计数

```plaintext
内核文档位置: include/linux/tty.h
标识符: tty_kref_get
```

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_kref_put
```

#### 安装

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_standard_install
```

#### 读写操作

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_put_char
```

#### 启动与停止

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: start_tty stop_tty
```

#### 唤醒

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_wakeup
```

#### 挂断

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_hangup tty_vhangup tty_hung_up_p
```

#### 其他功能

```plaintext
内核文档位置: drivers/tty/tty_io.c
标识符: tty_do_resize
```

#### TTY 结构体标志位

```plaintext
内核文档位置: include/linux/tty.h
文档内容: TTY 结构体标志位
```

#### TTY 结构体参考

```plaintext
内核文档位置: include/linux/tty.h
标识符: tty_struct
```
