下面是给定内容的中文翻译：

==========================================================================
ARM 架构中用于注册和调用固件特定操作的接口
==========================================================================

作者：Tomasz Figa <t.figa@samsung.com>

某些板卡上运行有在 TrustZone 安全世界中的安全固件，这改变了某些初始化过程的方式。这就需要为这类平台提供一个接口来指定可用的固件操作，并在必要时调用它们。
固件操作可以通过填充 `struct firmware_ops` 结构体并使用 `register_firmware_ops()` 函数进行注册来指定：

    void register_firmware_ops(const struct firmware_ops *ops)

`ops` 指针必须非空。关于 `struct firmware_ops` 及其成员的更多信息可以在头文件 `arch/arm/include/asm/firmware.h` 中找到。
提供了一组默认的、空的操作集，因此如果平台不需要固件操作，则无需设置任何内容。
要调用固件操作，提供了一个辅助宏：

    #define call_firmware_op(op, ...)                \
            ((firmware_ops->op) ? firmware_ops->op(__VA_ARGS__) : (-ENOSYS))

该宏会检查是否提供了相应的操作，如果有则调用它；否则返回 `-ENOSYS` 来表明给定的操作不可用（例如，允许回退到传统操作）。

下面是一个注册固件操作的例子：

    /* 板卡文件 */

    static int platformX_do_idle(void)
    {
        /* 告诉 platformX 固件进入空闲状态 */
        return 0;
    }

    static int platformX_cpu_boot(int i)
    {
        /* 告诉 platformX 固件启动 CPU i */
        return 0;
    }

    static const struct firmware_ops platformX_firmware_ops = {
        .do_idle        = platformX_do_idle,
        .cpu_boot       = platformX_cpu_boot,
        /* 其他在 platformX 上不可用的操作 */
    };

    /* 机器描述符中的 init_early 回调函数 */
    static void __init board_init_early(void)
    {
        register_firmware_ops(&platformX_firmware_ops);
    }

下面是一个使用固件操作的例子：

    /* 某些平台代码，例如 SMP 初始化 */

    __raw_writel(__pa_symbol(exynos4_secondary_startup),
        CPU1_BOOT_REG);

    /* 调用 Exynos 特定的 smc 调用 */
    if (call_firmware_op(cpu_boot, cpu) == -ENOSYS)
        cpu_boot_legacy(...); /* 尝试传统方式 */

    gic_raise_softirq(cpumask_of(cpu), 1);
