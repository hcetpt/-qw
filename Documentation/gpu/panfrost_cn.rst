SPDX 许可证标识符: GPL-2.0+

=========================
 drm/Panfrost Mali 驱动
=========================

.. _panfrost-usage-stats:

Panfrost DRM 客户端使用统计实现
==============================================

drm/Panfrost 驱动实现了 DRM 客户端使用统计规范，该规范在 :ref:`drm-client-usage-stats` 中有详细描述。以下是一个输出示例，展示了实现的键值对和当前所有可能的格式选项：

::
      pos:    0
      flags:  02400002
      mnt_id: 27
      ino:    531
      drm-driver:     panfrost
      drm-client-id:  14
      drm-engine-fragment:    1846584880 ns
      drm-cycles-fragment:    1424359409
      drm-maxfreq-fragment:   799999987 Hz
      drm-curfreq-fragment:   799999987 Hz
      drm-engine-vertex-tiler:        71932239 ns
      drm-cycles-vertex-tiler:        52617357
      drm-maxfreq-vertex-tiler:       799999987 Hz
      drm-curfreq-vertex-tiler:       799999987 Hz
      drm-total-memory:       290 MiB
      drm-shared-memory:      0 MiB
      drm-active-memory:      226 MiB
      drm-resident-memory:    36496 KiB
      drm-purgeable-memory:   128 KiB

可能的 `drm-engine-` 键名包括：`fragment` 和 `vertex-tiler`。
`drm-curfreq-` 值表示该引擎当前的工作频率。
用户需要注意，默认情况下，由于节能考虑，引擎和周期采样是禁用的。查询 `fdinfo` 文件的应用程序必须确保通过写入适当的 sysfs 节点来切换驱动器的工作配置文件状态：

```
echo <N> > /sys/bus/platform/drivers/panfrost/[a-f0-9]*.gpu/profiling
```

其中 `<N>` 是 `0` 或 `1`，取决于所需的启用状态。
