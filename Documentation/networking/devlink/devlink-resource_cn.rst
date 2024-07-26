### SPDX 许可证标识符：GPL-2.0

#### Devlink 资源

`devlink` 提供了让驱动程序注册资源的能力，这可以让管理员查看特定资源的设备限制，以及当前正在使用的该资源的数量。此外，这些资源还可以选择性地具有可配置的大小，这使得管理员能够限制所使用的资源数量。例如，`netdevsim` 驱动程序将 `/IPv4/fib` 和 `/IPv4/fib-rules` 作为资源来限制给定设备的 IPv4 FIB 条目和规则的数量。

##### 资源 ID

每个资源都由一个 ID 表示，并包含有关其当前大小和相关子资源的信息。要访问子资源，你需要指定资源的路径。例如，`/IPv4/fib` 是 `IPv4` 资源下 `fib` 子资源的 ID。

##### 通用资源

通用资源用于描述可以被多个设备驱动程序共享的资源，其描述必须添加到下表中：

| 名称       | 描述 |
|------------|-------------------------|
| `physical_ports` | 交换机 ASIC 可支持的物理端口有限容量 |

##### 示例使用

驱动程序暴露的资源可以通过以下命令进行观察：

```shell
$ devlink resource show pci/0000:03:00.0
pci/0000:03:00.0:
  name kvd size 245760 unit entry
    resources:
      name linear size 98304 occ 0 unit entry size_min 0 size_max 147456 size_gran 128
      name hash_double size 60416 unit entry size_min 32768 size_max 180224 size_gran 128
      name hash_single size 87040 unit entry size_min 65536 size_max 212992 size_gran 128
```

某些资源的大小是可以改变的。例如：

```shell
$ devlink resource set pci/0000:03:00.0 path /kvd/hash_single size 73088
$ devlink resource set pci/0000:03:00.0 path /kvd/hash_double size 74368
```

更改不会立即生效，这一点可以通过 `size_new` 属性验证，该属性表示待定的大小更改。例如：

```shell
$ devlink resource show pci/0000:03:00.0
pci/0000:03:00.0:
  name kvd size 245760 unit entry size_valid false
  resources:
    name linear size 98304 size_new 147456 occ 0 unit entry size_min 0 size_max 147456 size_gran 128
    name hash_double size 60416 unit entry size_min 32768 size_max 180224 size_gran 128
    name hash_single size 87040 unit entry size_min 65536 size_max 212992 size_gran 128
```

需要注意的是，资源大小的更改可能需要重新加载设备才能生效。
