SPDX 许可证标识符: GPL-2.0

==================================
XFRM proc - `/proc/net/xfrm_*` 文件
==================================

中村雅人 <nakam@linux-ipv6.org>

转换统计信息
------------

xfrm_proc 代码是一组统计数据，显示被转换代码丢弃的报文数量及其原因。这些计数器作为 Linux 私有 MIB 的一部分定义。可以在 `/proc/net/xfrm_stat` 中查看这些计数器。

入站错误
~~~~~~~~~~~~~~

XfrmInError:
	所有未匹配其他类别的错误

XfrmInBufferError:
	没有剩余的缓冲区

XfrmInHdrError:
	报头错误

XfrmInNoStates:
	未找到状态
	即入站 SPI、地址或 IPsec 协议在 SA 上不正确

XfrmInStateProtoError:
	转换协议特定错误
	例如 SA 密钥不正确

XfrmInStateModeError:
	转换模式特定错误

XfrmInStateSeqError:
	序列错误
	即序列号超出窗口范围

XfrmInStateExpired:
	状态已过期

XfrmInStateMismatch:
	状态选项不匹配
	例如 UDP 封装类型不匹配

XfrmInStateInvalid:
	状态无效

XfrmInTmplMismatch:
	未找到匹配的状态模板
	例如入站 SA 正确但 SP 规则不正确

XfrmInNoPols:
	未找到状态的策略
	例如入站 SA 正确但未找到 SP

XfrmInPolBlock:
	策略丢弃

XfrmInPolError:
	策略错误

XfrmAcquireError:
	使用前状态尚未完全获取

XfrmFwdHdrError:
	不允许报文的转发路由

XfrmInStateDirError:
	状态方向不匹配（查找时在输入路径上找到了输出状态，期望输入或无方向）

出站错误
~~~~~~~~~~~~~~~

XfrmOutError:
	所有未匹配其他类别的错误

XfrmOutBundleGenError:
	捆绑生成错误

XfrmOutBundleCheckError:
	捆绑检查错误

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
	策略丢弃

XfrmOutPolDead:
	策略失效

XfrmOutPolError:
	策略错误

XfrmOutStateInvalid:
	状态无效，可能已过期

XfrmOutStateDirError:
	状态方向不匹配（查找时在输出路径上找到了输入状态，期望输出或无方向）
