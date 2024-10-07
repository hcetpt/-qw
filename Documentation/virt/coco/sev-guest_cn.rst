SPDX 许可证标识符: GPL-2.0

===================================================================
SEV 客户端 API 文档
===================================================================

1. 总体描述
======================

SEV API 是一组用于客户端或管理程序获取或设置 SEV 虚拟机某方面特性的 ioctl。这些 ioctl 属于以下几类：

- 管理程序 ioctl：这些 ioctl 查询和设置影响整个 SEV 固件的全局属性。这些 ioctl 由平台配置工具使用。
- 客户端 ioctl：这些 ioctl 查询和设置 SEV 虚拟机的属性。

2. API 描述
==================

本节描述了用于从 SEV 固件查询 SEV 客户端报告的 ioctl。对于每个 ioctl，提供了以下信息及其描述：

  技术：
      提供此 ioctl 的 SEV 技术。可以是 SEV、SEV-ES、SEV-SNP 或全部。
  类型：
      管理程序或客户端。ioctl 可以在客户端内部或管理程序中使用。
  参数：
      ioctl 接受的参数。
  返回值：
      返回值。一般错误码（如 -ENOMEM, -EINVAL）不详细列出，但具有特定含义的错误会列出。

客户端 ioctl 应该在 /dev/sev-guest 设备的文件描述符上发出。ioctl 接受 struct snp_user_guest_request。输入和输出结构分别通过 req_data 和 resp_data 字段指定。如果由于固件错误导致 ioctl 执行失败，则会设置 fw_error 代码，否则将 fw_error 设置为 -1。固件会检查消息序列计数器是否比客户端的消息序列计数器大一。如果客户端驱动未能递增消息计数器（例如计数器溢出），则返回 -EIO。

```
struct snp_guest_request_ioctl {
    // 消息版本号
    __u32 msg_version;

    // 请求和响应结构地址
    __u64 req_data;
    __u64 resp_data;

    // bits[63:32]: VMM 错误码，bits[31:0] 固件错误码（见 psp-sev.h）
    union {
        __u64 exitinfo2;
        struct {
            __u32 fw_error;
            __u32 vmm_error;
        };
    };
};
```

管理程序 ioctl 发送到 /dev/sev 设备的文件描述符。ioctl 接受下面文档中的命令 ID/输入结构。
```markdown
### 结构体 sev_issue_cmd
- **命令ID**
  - `__u32 cmd`
- **命令请求结构**
  - `__u64 data`
- **失败时的固件错误码（参见 psp-sev.h）**
  - `__u32 error`

### 2.1 SNP_GET_REPORT
------------------
- **技术**: sev-snp
- **类型**: 客户端 ioctl
- **输入参数**: struct snp_report_req
- **返回值**: 成功时返回 struct snp_report_resp，出错时返回负数

`SNP_GET_REPORT` ioctl 可用于从 SEV-SNP 固件查询认证报告。此 ioctl 使用 SEV-SNP 固件提供的 `SNP_GUEST_REQUEST (MSG_REPORT_REQ)` 命令来查询认证报告。成功时，`snp_report_resp.data` 将包含报告内容，报告格式在 SEV-SNP 规范中有详细描述，请参阅 SEV-SNP 规范获取更多信息。

### 2.2 SNP_GET_DERIVED_KEY
-----------------------
- **技术**: sev-snp
- **类型**: 客户端 ioctl
- **输入参数**: struct snp_derived_key_req
- **返回值**: 成功时返回 struct snp_derived_key_resp，出错时返回负数

`SNP_GET_DERIVED_KEY` ioctl 可用于获取从根密钥派生的密钥。派生的密钥可用于客户机的各种目的，例如封存密钥或与外部实体通信。此 ioctl 使用 SEV-SNP 固件提供的 `SNP_GUEST_REQUEST (MSG_KEY_REQ)` 命令来派生密钥。有关密钥派生请求中传递的各个字段的详细信息，请参阅 SEV-SNP 规范。成功时，`snp_derived_key_resp.data` 将包含派生的密钥值，详细信息请参阅 SEV-SNP 规范。

### 2.3 SNP_GET_EXT_REPORT
----------------------
- **技术**: sev-snp
- **类型**: 客户端 ioctl
- **输入输出参数**: struct snp_ext_report_req
- **返回值**: 成功时返回 struct snp_report_resp，出错时返回负数

`SNP_GET_EXT_REPORT` ioctl 类似于 `SNP_GET_REPORT`，不同之处在于它返回的报告中包含了额外的证书数据。这些证书数据由 hypervisor 通过 `SNP_SET_EXT_CONFIG` 提供。此 ioctl 使用 SEV-SNP 固件提供的 `SNP_GUEST_REQUEST (MSG_REPORT_REQ)` 命令来获取认证报告。成功时，`snp_ext_report_resp.data` 将包含认证报告，而 `snp_ext_report_req.certs_address` 将包含证书数据。如果 blob 的长度小于预期，则 `snp_ext_report_req.certs_len` 将被更新为预期值。
```
### 查看 GHCB 规格以获取如何解析证书 blob 的详细信息

#### 2.4 SNP_PLATFORM_STATUS
-----------------------
**技术**: sev-snp  
**类型**: 虚拟机 ioctl 命令  
**输出参数**: struct sev_user_data_snp_status  
**返回值**: 成功时返回 0，失败时返回负数

SNP_PLATFORM_STATUS 命令用于查询 SNP 平台状态。该状态包括 API 主版本、次版本及其他信息。有关更多详细信息，请参阅 SEV-SNP 规范。

#### 2.5 SNP_COMMIT
------------------
**技术**: sev-snp  
**类型**: 虚拟机 ioctl 命令  
**返回值**: 成功时返回 0，失败时返回负数

SNP_COMMIT 命令用于提交当前安装的固件。使用 SEV-SNP 固件命令 SNP_COMMIT 可防止回滚到先前提交的固件版本。这也会更新报告的 TCB，使其与当前安装的固件匹配。

#### 2.6 SNP_SET_CONFIG
------------------
**技术**: sev-snp  
**类型**: 虚拟机 ioctl 命令  
**输入参数**: struct sev_user_data_snp_config  
**返回值**: 成功时返回 0，失败时返回负数

SNP_SET_CONFIG 命令用于设置系统范围内的配置，例如在认证报告中报告的 TCB 版本。该命令类似于 SEV-SNP 规范中定义的 SNP_CONFIG 命令。可以通过 SNP_PLATFORM_STATUS 查询此命令影响的固件参数的当前值。

### SEV-SNP CPUID 强制执行
============================

SEV-SNP 客户端可以访问一个特殊页面，该页面包含由 PSP 在执行 SNP_LAUNCH_UPDATE 固件命令时验证过的 CPUID 值表。它提供了以下关于 CPUID 值有效性的保证：

- 其地址是通过引导加载程序/固件（通过 CC blob）获得的，并且这些二进制文件将作为 SEV-SNP 认证报告的一部分进行度量。
- 其初始状态会被加密/验证，因此在运行时尝试修改它会导致垃圾数据被写入，或者由于验证状态的变化，如果虚拟机尝试交换支持页，则会生成 #VC 异常。
- 尝试通过使用普通页或非 CPUID 加密页绕过 PSP 检查的虚拟机会改变 SEV-SNP 认证报告提供的度量结果。
- CPUID 页面的内容本身不会被度量，但在客户初始化过程中尝试修改 CPUID 页面预期内容的行为将受到 SNP_LAUNCH_UPDATE 执行期间对页面进行的 PSP CPUID 强制策略检查的限制。如果客户所有者实现了自己的 CPUID 值检查，稍后会注意到这一点。

需要注意的是，最后一个保证只有在内核在整个启动过程中都利用了 SEV-SNP CPUID 时才有用。否则，客户所有者的认证无法保证内核在启动过程中的某个时刻没有被提供错误的值。
4. SEV 客户机驱动通信密钥
==========================

SEV 客户机与 AMD 安全处理器（ASP，即 PSP）中的 SEV 固件之间的通信受到 VM 平台通信密钥（VMPCK）的保护。默认情况下，sev-guest 驱动使用与客户机运行的虚拟机特权级别（VMPL）关联的 VMPCK。如果该密钥被 sev-guest 驱动清除（请参阅驱动程序以了解为什么 VMPCK 可能会被清除），可以通过重新加载 sev-guest 驱动并使用 `vmpck_id` 模块参数指定所需的密钥来使用不同的密钥。

参考
----

SEV-SNP 和 GHCB 规范：developer.amd.com/sev

该驱动基于 SEV-SNP 固件规范 0.9 版和 GHCB 规范 2.0 版。
