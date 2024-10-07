=============  
PCMCIA 驱动
=============

sysfs
-----

可以在运行时向设备驱动程序的 pcmcia_device_id 表中添加新的 PCMCIA ID，如下所示：

```sh
echo "match_flags manf_id card_id func_id function device_no \
prod_id_hash[0] prod_id_hash[1] prod_id_hash[2] prod_id_hash[3]" > \
/sys/bus/pcmcia/drivers/{driver}/new_id
```

所有字段都作为十六进制值传递（无需前导 0x）。这些字段的意义在 PCMCIA 规范中有描述，其中 `match_flags` 是由 `PCMCIA_DEV_ID_MATCH_*` 常量组合而成的位或运算，这些常量定义在 `include/linux/mod_devicetable.h` 中。

一旦添加后，对于其（新更新的）pcmcia_device_id 列表中的任何未被声明的 PCMCIA 设备，将调用该驱动程序的探测例程。

一个常见的用例是根据制造商 ID 和卡片 ID 添加一个新的设备（从设备树中的 `manf_id` 和 `card_id` 文件获取）。为此，只需使用以下命令：

```sh
echo "0x3 manf_id card_id 0 0 0 0 0 0 0" > \
/sys/bus/pcmcia/drivers/{driver}/new_id
```

在加载驱动程序之后执行上述命令。
