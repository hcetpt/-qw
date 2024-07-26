### SPDX 许可证标识符：GPL-2.0

==================================
XFRM proc - `/proc/net/xfrm_*` 文件
==================================

Masahide NAKAMURA <nakam@linux-ipv6.org>

### 转换统计信息
-------------------------

XFRM_PROC 代码是一组统计数据，显示被转换代码丢弃的包的数量及其原因。这些计数器是作为 Linux 私有 MIB（管理信息库）的一部分定义的。这些计数器可以在 `/proc/net/xfrm_stat` 中查看。

#### 入站错误
~~~~~~~~~~~~~~

XfrmInError:
    所有不匹配其他情况的错误

XfrmInBufferError:
    没有足够的缓冲区

XfrmInHdrError:
    头部错误

XfrmInNoStates:
    未找到状态
    即入站 SPI、地址或 IPsec 协议在安全关联中不正确

XfrmInStateProtoError:
    转换协议特定错误
    例如，SA 密钥不正确

XfrmInStateModeError:
    转换模式特定错误

XfrmInStateSeqError:
    序列错误
    即序列号超出窗口范围

XfrmInStateExpired:
    状态已过期

XfrmInStateMismatch:
    状态选项不匹配
    例如，UDP 封装类型不匹配

XfrmInStateInvalid:
    状态无效

XfrmInTmplMismatch:
    状态没有匹配的模板
    例如，入站 SA 正确但 SP 规则不正确

XfrmInNoPols:
    未为状态找到策略
    例如，入站 SA 正确但未找到 SP

XfrmInPolBlock:
    策略拒绝

XfrmInPolError:
    策略错误

XfrmAcquireError:
    在使用之前状态尚未完全获取

XfrmFwdHdrError:
    不允许包的转发路由

XfrmInStateDirError:
    状态方向不匹配（查找时在入站路径上找到了输出状态，期望的是入站或无方向）

#### 出站错误
~~~~~~~~~~~~~~~
XfrmOutError:
    所有不匹配其他情况的错误

XfrmOutBundleGenError:
    组合生成错误

XfrmOutBundleCheckError:
    组合检查错误

XfrmOutNoStates:
    未找到状态

XfrmOutStateProtoError:
    转换协议特定错误

XfrmOutStateModeError:
    转换模式特定错误

XfrmOutStateSeqError:
    序列错误
    即序列号溢出

XfrmOutStateExpired:
    状态已过期

XfrmOutPolBlock:
    策略拒绝

XfrmOutPolDead:
    策略失效

XfrmOutPolError:
    策略错误

XfrmOutStateInvalid:
    状态无效，可能已过期

XfrmOutStateDirError:
    状态方向不匹配（查找时在出站路径上找到了入站状态，期望的是出站或无方向）
