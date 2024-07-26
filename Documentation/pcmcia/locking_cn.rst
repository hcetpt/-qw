### 锁定

#### A) 概览，锁定层次：
===============================

`pcmcia_socket_list_rwsem`
- 仅保护套接字列表

- `skt_mutex`
    - 序列化卡片插入/弹出操作

      - `ops_mutex`
          - 序列化套接字操作

#### B) 排他
============

以下函数和对`struct pcmcia_socket`结构体的回调必须在持有`skt_mutex`的情况下调用：

- `socket_detect_change()`
- `send_event()`
- `socket_reset()`
- `socket_shutdown()`
- `socket_setup()`
- `socket_remove()`
- `socket_insert()`
- `socket_early_resume()`
- `socket_late_resume()`
- `socket_resume()`
- `socket_suspend()`

- `struct pcmcia_callback *callback`

以下函数和对`struct pcmcia_socket`结构体的回调必须在持有`ops_mutex`的情况下调用：

- `socket_reset()`
- `socket_setup()`

- `struct pccard_operations *ops`
- `struct pccard_resource_ops *resource_ops;`

请注意，`send_event()` 和 `struct pcmcia_callback *callback` 必须不在持有`ops_mutex`的情况下调用。

#### C) 保护
=============

1. 全局数据：
--------------
`struct list_head pcmcia_socket_list;`

由`pcmcia_socket_list_rwsem`保护；

2. 每个套接字的数据：
-------------------
`resource_ops`及其数据由`ops_mutex`保护；
`struct pcmcia_socket`的主结构体如下保护（未提及只读字段或单次使用字段）：

- 由`pcmcia_socket_list_rwsem`保护：

  - `struct list_head socket_list;`

- 由`thread_lock`保护：

  - `unsigned int thread_events;`

- 由`skt_mutex`保护：

  - `u_int suspended_state;`
  - `void (*tune_bridge);`
  - `struct pcmcia_callback *callback;`
  - `int resume_status;`

- 由`ops_mutex`保护：

  - `socket_state_t socket;`
  - `u_int state;`
  - `u_short lock_count;`
  - `pccard_mem_map cis_mem;`
  - `void __iomem *cis_virt;`
  - `struct { } irq;`
  - `io_window_t io[];`
  - `pccard_mem_map win[];`
  - `struct list_head cis_cache;`
  - `size_t fake_cis_len;`
  - `u8 *fake_cis;`
  - `u_int irq_mask;`
  - `void (*zoom_video);`
  - `int (*power_hook);`
  - `u8 resource...;`
  - `struct list_head devices_list;`
  - `u8 device_count;`
  - `struct pcmcia_state;`

3. 每个PCMCIA设备的数据：
--------------------------

`struct pcmcia_device`的主结构体如下保护（未提及只读字段或单次使用字段）：

- 由`pcmcia_socket->ops_mutex`保护：

  - `struct list_head socket_device_list;`
  - `struct config_t *function_config;`
  - `u16 _irq:1;`
  - `u16 _io:1;`
  - `u16 _win:4;`
  - `u16 _locked:1;`
  - `u16 allow_func_id_match:1;`
  - `u16 suspended:1;`
  - `u16 _removed:1;`

- 由PCMCIA驱动程序保护：

  - `io_req_t io;`
  - `irq_req_t irq;`
  - `config_req_t conf;`
  - `window_handle_t win;`
