### SPDX 许可证标识符：GPL-2.0-only
### 版权 (C) 2022 Red Hat, Inc.

#### 重定向

##### XDP_REDIRECT

**支持的映射**

XDP_REDIRECT 支持以下类型的映射：

- `BPF_MAP_TYPE_DEVMAP`
- `BPF_MAP_TYPE_DEVMAP_HASH`
- `BPF_MAP_TYPE_CPUMAP`
- `BPF_MAP_TYPE_XSKMAP`

有关这些映射的更多信息，请参阅特定映射文档。

**流程**

``` 
[内核文档] net/core/filter.c
文档: xdp 重定向
```

**注释**
并非所有驱动程序都支持重定向后的帧传输，对于那些支持的驱动程序，并非所有驱动程序都支持非线性帧。非线性的 XDP 缓冲区/帧是指包含多个片段的缓冲区/帧。

#### 调试丢包问题

XDP_REDIRECT 的静默丢包可以通过以下方式进行调试：

- bpf_trace
- perf_record

**bpf_trace**

可以使用以下 bpftrace 命令捕获并统计所有的 XDP 追踪点：

```none
sudo bpftrace -e 'tracepoint:xdp:* { @cnt[probe] = count(); }'
正在附加 12 个追踪点..
^C

@cnt[tracepoint:xdp:mem_connect]: 18
@cnt[tracepoint:xdp:mem_disconnect]: 18
@cnt[tracepoint:xdp:xdp_exception]: 19605
@cnt[tracepoint:xdp:xdp_devmap_xmit]: 1393604
@cnt[tracepoint:xdp:xdp_redirect]: 22292200
```

**注释**
各种 XDP 追踪点可以在 `source/include/trace/events/xdp.h` 中找到。

可以使用以下 bpftrace 命令提取作为 err 参数返回的 `ERRNO`：

```none
sudo bpftrace -e \
'tracepoint:xdp:xdp_redirect*_err {@redir_errno[-args->err] = count();}
tracepoint:xdp:xdp_devmap_xmit {@devmap_errno[-args->err] = count();}'
```

**perf_record**

perf 工具也支持记录追踪点：

```none
perf record -a -e xdp:xdp_redirect_err \
    -e xdp:xdp_redirect_map_err \
    -e xdp:xdp_exception \
    -e xdp:xdp_devmap_xmit
```

#### 参考资料

- https://github.com/xdp-project/xdp-tutorial/tree/master/tracing02-xdp-monitor
