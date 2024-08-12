==================
NVDIMM 安全性
==================

1. 引言
--------

随着 Intel 设备特定方法 (DSM) v1.8 规范 [1] 的引入，安全性 DSM 也被引入。该规范新增了以下安全性 DSM：获取安全状态、设置密码短语、禁用密码短语、解锁单元、冻结锁定、安全擦除和覆盖写入。为了支持这些安全操作，并公开通用 API 以允许中立于供应商的操作，已在 `struct dimm` 中添加了一个名为 `security_ops` 的数据结构。

2. Sysfs 接口
---------------
在 NVDIMM 的 sysfs 目录中提供了名为“security”的 sysfs 属性。例如：
/sys/devices/LNXSYSTM:00/LNXSYBUS:00/ACPI0012:00/ndbus0/nmem0/security

该属性的“show”部分将显示该 DIMM 的安全状态。可获得的状态包括：禁用、解锁、锁定、冻结和覆盖写入。如果该设备不支持安全性，则该 sysfs 属性将不可见。
该属性的“store”部分接受多个命令以支持某些安全功能：
- `update <old_keyid> <new_keyid>` - 启用或更新密码短语
- `disable <keyid>` - 禁用已启用的安全性并移除密钥
- `freeze` - 冻结安全状态的更改
- `erase <keyid>` - 删除现有的用户加密密钥
- `overwrite <keyid>` - 擦除整个 NVDIMM
- `master_update <keyid> <new_keyid>` - 启用或更新主密码短语
- `master_erase <keyid>` - 删除现有的用户加密密钥

3. 密钥管理
--------------

密钥通过 DIMM ID 与有效负载相关联。例如：
```bash
# cat /sys/devices/LNXSYSTM:00/LNXSYBUS:00/ACPI0012:00/ndbus0/nmem0/nfit/id
8089-a2-1740-00000133
```
DIMM ID 将与密钥有效负载（密码短语）一起提供给内核。
安全密钥基于每个DIMM一个密钥的方式进行管理。密钥的“密码短语”预期长度为32字节。这与ATA安全性规范[2]类似。最初通过在解锁nvdimm时调用request_key()内核API来获取密钥。用户需确保所有用于解锁的密钥都在内核用户密钥环中。
格式为enc32的nvdimm加密密钥具有如下描述格式：
nvdimm:<总线提供者特定唯一ID>

请参阅文件``Documentation/security/keys/trusted-encrypted.rst``以创建格式为enc32的加密密钥。建议使用带有主信任密钥的TPM对加密密钥进行密封。
4. 解锁
------------
当内核正在枚举DIMM时，内核将尝试从内核用户密钥环中检索密钥。这是锁定DIMM可以被解锁的唯一时刻。一旦解锁，DIMM将保持解锁状态直到重启。通常，在initramfs阶段，实体（例如shell脚本）会将所有相关的加密密钥注入内核用户密钥环中。这为解锁功能提供了访问包含各自nvdimms密码短语的所有相关密钥的机会。建议在通过modprobe加载libnvdimm之前注入密钥。
5. 更新
---------
在进行更新时，预期现有的密钥将从内核用户密钥环中移除，并作为不同的（旧）密钥重新注入。对于旧密钥的描述是什么并不重要，因为我们只关心更新操作中的keyid。同时，新密钥应按照本文档前面所述的描述格式注入。写入sysfs属性的更新命令格式为：
update <旧keyid> <新keyid>

如果由于启用安全性而没有旧keyid，则应传递0。
6. 冻结
---------
冻结操作不需要任何密钥。具有root权限的用户可以冻结安全性配置。
7. 禁用
----------
禁用安全性的命令格式为：
disable <keyid>

与nvdimm关联、含有当前密码短语的有效密钥应当存在于内核用户密钥环中。
8. 安全擦除
---------------
执行安全擦除的命令格式为：
erase <keyid>

与nvdimm关联、含有当前密码短语的有效密钥应当存在于内核用户密钥环中。
9. 覆写
------------
执行覆写的命令格式为：
overwrite <keyid>

如果没有启用安全性，覆写可以无需密钥进行。可以通过传递0作为密钥序列号来表示无密钥。
可以通过轮询sysfs属性"security"来等待覆写完成。
覆盖操作可能持续数十分钟或更长时间，这取决于 NVDIMM 的大小。
应注入与 NVDIMM 关联的当前用户密码短语加密密钥，并通过 sysfs 传递其 keyid。
10. 主密钥更新
-----------------
执行主密钥更新的命令格式为：
update <旧 keyid> <新 keyid>

主密钥更新的操作机制与普通更新相同，只是将主密码密钥传递给内核。主密码密钥仅仅是另一个加密密钥。
此命令仅在安全功能被禁用时可用。
11. 主密钥擦除
-----------------
执行主密钥擦除的命令格式为：
master_erase <当前 keyid>

此命令的操作机制与普通擦除相同，只是将主密码密钥传递给内核。主密码密钥同样是另一个加密密钥。
此命令仅在启用主密钥安全功能时可用，这由扩展的安全状态指示。

[1]: https://pmem.io/documents/NVDIMM_DSM_Interface-V1.8.pdf

[2]: http://www.t13.org/documents/UploadedDocuments/docs2006/e05179r4-ACS-SecurityClarifications.pdf
