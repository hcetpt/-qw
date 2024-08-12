数字电视前端 kABI
-------------------

数字电视前端
~~~~~~~~~~~~~~

数字电视前端 kABI 定义了一个用于将底层、特定于硬件的驱动程序注册到与硬件无关的前端层的内部接口。这仅对数字电视设备驱动程序编写者感兴趣。此 API 的头文件名为 `dvb_frontend.h`，位于 `include/media/` 中。

解调器驱动程序
^^^^^^^^^^^^^^^^^^^

解调器驱动程序负责与硬件的解码部分通信。此类驱动程序应实现 `dvb_frontend_ops` 类型，以说明支持哪种类型的数字电视标准，并指向一系列允许 DVB 核心通过 `include/media/dvb_frontend.c` 下的代码命令硬件的函数。
在驱动程序 `foo` 中此类结构的一个典型示例是：

```c
static struct dvb_frontend_ops foo_ops = {
	.delsys = { SYS_DVBT, SYS_DVBT2, SYS_DVBC_ANNEX_A },
	.info = {
		.name	= "foo DVB-T/T2/C 驱动程序",
		.caps = FE_CAN_FEC_1_2 |
			FE_CAN_FEC_2_3 |
			FE_CAN_FEC_3_4 |
			FE_CAN_FEC_5_6 |
			FE_CAN_FEC_7_8 |
			FE_CAN_FEC_AUTO |
			FE_CAN_QPSK |
			FE_CAN_QAM_16 |
			FE_CAN_QAM_32 |
			FE_CAN_QAM_64 |
			FE_CAN_QAM_128 |
			FE_CAN_QAM_256 |
			FE_CAN_QAM_AUTO |
			FE_CAN_TRANSMISSION_MODE_AUTO |
			FE_CAN_GUARD_INTERVAL_AUTO |
			FE_CAN_HIERARCHY_AUTO |
			FE_CAN_MUTE_TS |
			FE_CAN_2G_MODULATION,
		.frequency_min = 42000000, /* Hz */
		.frequency_max = 1002000000, /* Hz */
		.symbol_rate_min = 870000,
		.symbol_rate_max = 11700000
	},
	.init = foo_init,
	.sleep = foo_sleep,
	.release = foo_release,
	.set_frontend = foo_set_frontend,
	.get_frontend = foo_get_frontend,
	.read_status = foo_get_status_and_stats,
	.tune = foo_tune,
	.i2c_gate_ctrl = foo_i2c_gate_ctrl,
	.get_frontend_algo = foo_get_algo,
};
```

在打算用于卫星电视接收的驱动程序 `bar` 中此类结构的一个典型示例是：

```c
static const struct dvb_frontend_ops bar_ops = {
	.delsys = { SYS_DVBS, SYS_DVBS2 },
	.info = {
		.name		= "Bar DVB-S/S2 解调器",
		.frequency_min	= 500000, /* KHz */
		.frequency_max	= 2500000, /* KHz */
		.frequency_stepsize	= 0,
		.symbol_rate_min = 1000000,
		.symbol_rate_max = 45000000,
		.symbol_rate_tolerance = 500,
		.caps = FE_CAN_INVERSION_AUTO |
			FE_CAN_FEC_AUTO |
			FE_CAN_QPSK,
	},
	.init = bar_init,
	.sleep = bar_sleep,
	.release = bar_release,
	.set_frontend = bar_set_frontend,
	.get_frontend = bar_get_frontend,
	.read_status = bar_get_status_and_stats,
	.i2c_gate_ctrl = bar_i2c_gate_ctrl,
	.get_frontend_algo = bar_get_algo,
	.tune = bar_tune,

	/* 卫星特有 */
	.diseqc_send_master_cmd = bar_send_diseqc_msg,
	.diseqc_send_burst = bar_send_burst,
	.set_tone = bar_set_tone,
	.set_voltage = bar_set_voltage,
};
```

.. note::
   
   1) 对于卫星数字电视标准（DVB-S、DVB-S2、ISDB-S），频率以千赫兹 (kHz) 指定，而对于地面和有线标准，则以赫兹 (Hz) 指定。因此，如果同一前端同时支持这两种类型，您需要为每种标准分别设置 `dvb_frontend_ops` 结构。
   2) 如果硬件允许控制 I2C 门（直接或通过某个 GPIO 引脚），则存在 `.i2c_gate_ctrl` 字段，以便在调谐频道后将调谐器从 I2C 总线上移除。
   3) 所有新驱动程序都应通过 `.read_status` 实现 :ref:`DVBv5 统计信息 <dvbv5_stats>`。然而，为了向后兼容不支持 DVBv5 API 的遗留应用程序，还有一些回调用于获取信号强度、信噪比和 UCB 的统计信息。实现这些回调是可选的。这些回调可能在未来被移除，前提是所有现有驱动程序都支持 DVBv5 统计信息。
   4) 对于卫星电视标准，还需要一些回调来控制 LNB 和 DiSEqC：`.diseqc_send_master_cmd`、`.diseqc_send_burst`、`.set_tone` 和 `.set_voltage`。

`include/media/dvb_frontend.c` 包含一个内核线程，该线程负责调谐设备。它支持多种算法来检测频道，如 `dvbfe_algo` 枚举中定义的那样。
要使用的算法通过 `.get_frontend_algo` 获取。如果驱动程序没有在 `struct dvb_frontend_ops` 中填写其字段，那么默认情况下会使用 `DVBFE_ALGO_SW`，这意味着 DVB 核心在调谐时将执行锯齿形搜索，例如，它将首先尝试使用指定的中心频率 `f`，然后尝试 `f` + Δ, `f` - Δ, `f` + 2 × Δ, `f` - 2 × Δ 等等。
如果硬件内部具有某种之字形算法，你应该定义一个`.get_frontend_algo`函数，该函数将返回`DVBFE_ALGO_HW`。

.. note::

   核心前端支持还支持第三种类型（`DVBFE_ALGO_CUSTOM`），以便允许驱动程序定义其自己的硬件辅助算法。现在很少有硬件需要使用它。使用`DVBFE_ALGO_CUSTOM`要求在`struct dvb_frontend_ops`中提供其他函数回调。

连接前端驱动到桥接驱动
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在使用数字电视前端核心之前，桥接驱动应该连接前端解调器、调谐器和SEC设备，并调用:C:func:`dvb_register_frontend()`来在子系统中注册新的前端。在设备分离/移除时，桥接驱动应该调用:C:func:`dvb_unregister_frontend()`从核心中移除前端，然后调用:C:func:`dvb_frontend_detach()`来释放前端驱动分配的内存。
驱动程序也应该在其:C:type:`device_driver`.\ `suspend()`处理程序中调用:C:func:`dvb_frontend_suspend()`，以及在其:C:type:`device_driver`.\ `resume()`处理程序中调用:C:func:`dvb_frontend_resume()`。
还提供了几个其他可选函数来处理一些特殊情况。

.. _dvbv5_stats:

数字电视前端统计信息
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

介绍
^^^^^^^^^^^^

数字电视前端提供了一系列旨在帮助调整设备和测量服务质量的<ref>`统计信息 <frontend-stat-properties>`。
对于每个统计测量值，驱动程序应设置所使用的比例类型，或如果给定时间的统计信息不可用则设置为`FE_SCALE_NOT_AVAILABLE`。驱动程序还应提供每种类型的统计数量，通常对于大多数视频标准来说是1个 [#f2]_。
驱动程序应在初始化代码中初始化每个统计计数器的长度和比例。例如，如果前端提供信号强度，则应在初始化代码中如下所示：

```c
struct dtv_frontend_properties *c = &state->fe.dtv_property_cache;

c->strength.len = 1;
c->strength.stat[0].scale = FE_SCALE_NOT_AVAILABLE;
```

当统计信息更新时，设置比例：

```c
c->strength.stat[0].scale = FE_SCALE_DECIBEL;
c->strength.stat[0].uvalue = strength;
```

.. [#f2] 对于ISDB-T，它可以同时提供全局统计信息和按层的统计信息集。在这种情况下，len应该等于4。第一个值对应全局S/N载波比；其他值分别对应每一层，例如：

- `c->cnr.stat[0]` 为全局S/N载波比，
- `c->cnr.stat[1]` 为Layer A S/N载波比，
- `c->cnr.stat[2]` 为Layer B S/N载波比，
- `c->cnr.stat[3]` 为Layer C S/N载波比
.. note:: 请尽量使用`FE_SCALE_DECIBEL`而不是`FE_SCALE_RELATIVE`来进行信号强度和CNR测量。
### 统计分组
^^^^^^^^^^^^^^^^^^^^

目前支持几种统计分组：

#### 信号强度 (:ref:`DTV-STAT-SIGNAL-STRENGTH`)
- 测量调谐器或解调器模拟部分的信号强度水平。
- 通常从应用于调谐器和/或前端的增益中获得，以检测载波。当未检测到载波时，增益处于最大值（因此，强度最低）。
- 由于增益是通过一组调整增益的寄存器可见的，因此这种统计信息通常是可用的 [#f3]_。
- 驱动程序应尽量使其始终可用，因为这些统计信息可用于调整天线位置以及检查电缆问题。

.. [#f3] 在少数设备上，如果没有载波，则增益会持续漂移。对于此类设备，强度报告应首先检查调谐器是否检测到了载波（``FE_HAS_CARRIER``，参见 :c:type:`fe_status`），如果没有，则返回最低可能的值。

#### 载波信噪比 (:ref:`DTV-STAT-CNR`)
- 主载波的信噪比。
- 信噪比测量取决于设备。在某些硬件上，当主载波被检测到时它是可用的。在这种硬件上，CNR测量通常来自调谐器（例如，在``FE_HAS_CARRIER``之后，参见 :c:type:`fe_status`）。
- 在其他设备上，它需要内部FEC解码，因为前端间接地从其他参数（例如，在``FE_HAS_VITERBI``之后，参见 :c:type:`fe_status`）中测量它。
- 在内部FEC之后提供它是更常见的做法。
后向纠错后的比特计数（:ref:`DTV-STAT-POST-ERROR-BIT-COUNT` 和 :ref:`DTV-STAT-POST-TOTAL-BIT-COUNT`）
  - 这些计数器测量经过内部编码块的前向错误校正（FEC）之后的比特数和比特错误数
    （在Viterbi、LDPC或其他内部码之后）
- 由于其特性，这些统计数据依赖于完整的编码锁定状态
    （例如，在`FE_HAS_SYNC`或`FE_HAS_LOCK`之后，参见:c:type:`fe_status`）
前向纠错前的比特计数（:ref:`DTV-STAT-PRE-ERROR-BIT-COUNT` 和 :ref:`DTV-STAT-PRE-TOTAL-BIT-COUNT`）
  - 这些计数器测量在内部编码块的前向错误校正（FEC）之前的比特数和比特错误数
    （在Viterbi、LDPC或其他内部码之前）
- 并非所有前端都提供这类统计数据
- 由于其特性，这些统计数据依赖于内部编码锁定状态（例如，在`FE_HAS_VITERBI`之后，参见:c:type:`fe_status`）
块计数（:ref:`DTV-STAT-ERROR-BLOCK-COUNT` 和 :ref:`DTV-STAT-TOTAL-BLOCK-COUNT`）
  - 这些计数器测量经过内部编码块的前向错误校正（FEC）之后的块数和块错误数
    （在Viterbi、LDPC或其他内部码之后）
- 由于其特性，这些统计数据依赖于完整的编码锁定状态
    （例如，在`FE_HAS_SYNC`或`FE_HAS_LOCK`之后，参见:c:type:`fe_status`）

.. note:: 所有计数器应该单调递增，因为它们是从硬件收集的

处理状态和统计数据的一个典型逻辑示例如下：

```c
static int foo_get_status_and_stats(struct dvb_frontend *fe)
{
    struct foo_state *state = fe->demodulator_priv;
    struct dtv_frontend_properties *c = &fe->dtv_property_cache;

    int rc;
    enum fe_status *status;

    /* 状态和信号强度总是可用的 */
    rc = foo_read_status(fe, &status);
    if (rc < 0)
        return rc;

    rc = foo_read_strength(fe);
    if (rc < 0)
        return rc;

    /* 检查载噪比是否可用 */
    if (!(fe->status & FE_HAS_CARRIER))
        return 0;

    rc = foo_read_cnr(fe);
    if (rc < 0)
        return rc;

    /* 检查前向比特误码率统计是否可用 */
    if (!(fe->status & FE_HAS_VITERBI))
        return 0;

    rc = foo_get_pre_ber(fe);
    if (rc < 0)
        return rc;

    /* 检查后向比特误码率统计是否可用 */
    if (!(fe->status & FE_HAS_SYNC))
        return 0;

    rc = foo_get_post_ber(fe);
    if (rc < 0)
        return rc;
}
static const struct dvb_frontend_ops ops = {
    /* ... */
    .read_status = foo_get_status_and_stats,
};
```

**统计数据收集**

在几乎所有的前端硬件上，比特和字节计数是在一定时间后或者总比特/块计数达到某一值时（通常是可编程的），由硬件存储的，例如，每1000毫秒或接收1,000,000比特后。
因此，如果你过早地读取寄存器，最终会读取到与前一次读取相同的值，导致单调递增的值被过于频繁地增加。
驱动程序应承担避免过于频繁读取的责任。这可以通过两种方法来实现：

如果驱动程序有一个位表示收集的数据已准备好
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

在提供统计数据之前，驱动程序应检查该位。
下面这段代码示例（从mb86a20s驱动逻辑改编）展示了这种行为：

```c
static int foo_get_pre_ber(struct dvb_frontend *fe)
{
    struct foo_state *state = fe->demodulator_priv;
    struct dtv_frontend_properties *c = &fe->dtv_property_cache;
    int rc, bit_error;

    /* 检查BER测量是否已经可用 */
    rc = foo_read_u8(state, 0x54);
    if (rc < 0)
        return rc;

    if (!rc)
        return 0;

    /* 读取比特错误计数 */
    bit_error = foo_read_u32(state, 0x55);
    if (bit_error < 0)
        return bit_error;

    /* 读取总比特数 */
    rc = foo_read_u32(state, 0x51);
    if (rc < 0)
        return rc;

    c->pre_bit_error.stat[0].scale = FE_SCALE_COUNTER;
    c->pre_bit_error.stat[0].uvalue += bit_error;
    c->pre_bit_count.stat[0].scale = FE_SCALE_COUNTER;
    c->pre_bit_count.stat[0].uvalue += rc;

    return 0;
}
```

如果驱动程序不提供一个统计可用性的检查位
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

然而，一些设备可能没有提供一种检查统计数据是否可用的方法（或者检查方式未知）。它们甚至可能没有直接提供读取总比特数或块数的方法。
对于这些设备，驱动程序需要确保不会过于频繁地从寄存器中读取数据，并/或估计总的比特数/块数。
在这种驱动程序中，获取统计数据的典型例程可能是这样的（从dib8000驱动逻辑改编）：

```c
struct foo_state {
    /* ... */

    unsigned long per_jiffies_stats;
}
static int foo_get_pre_ber(struct dvb_frontend *fe)
{
    struct foo_state *state = fe->demodulator_priv;
    struct dtv_frontend_properties *c = &fe->dtv_property_cache;
    int rc, bit_error;
    u64 bits;

    /* 检查是否到了获取统计的时间 */
    if (!time_after(jiffies, state->per_jiffies_stats))
        return 0;

    /* 下一次统计应在1000毫秒后收集 */
    state->per_jiffies_stats = jiffies + msecs_to_jiffies(1000);

    /* 读取比特错误计数 */
    bit_error = foo_read_u32(state, 0x55);
    if (bit_error < 0)
        return bit_error;

    /*
     * 在这个特定前端设备上，没有寄存器可以提供每1000毫秒样本的比特数。
     * 所以，某个函数会基于DTV属性计算出这个数值
     */
    bits = get_number_of_bits_per_1000ms(fe);

    c->pre_bit_error.stat[0].scale = FE_SCALE_COUNTER;
    c->pre_bit_error.stat[0].uvalue += bit_error;
    c->pre_bit_count.stat[0].scale = FE_SCALE_COUNTER;
    c->pre_bit_count.stat[0].uvalue += bits;

    return 0;
}
```

请注意，在这两种情况下，我们都是通过`:c:type:` `dvb_frontend_ops` 的 ``.read_status`` 回调函数来获取统计数据。原理是前端核心将自动定期调用此函数（通常，在前端锁定时，每秒调用三次）。
这样保证了我们不会错过收集计数器并在正确的时间递增单调统计。
数字电视前端函数和类型
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/media/dvb_frontend.h
