### ktime访问器

设备驱动程序可以使用`ktime_get()`及在`linux/timekeeping.h`中声明的许多相关函数来读取当前时间。作为一般准则，如果两个访问器都适用于特定用途，则优选使用名称较短的那个。

#### 基于ktime_t的基本接口

推荐的最简单形式返回一个不透明的`ktime_t`类型，根据不同的时钟参考有不同变体：

```c
ktime_t ktime_get(void);
```

- **CLOCK_MONOTONIC**

  适用于可靠的时戳和精确测量短时间间隔。从系统启动开始计时，但在暂停期间会停止。

```c
ktime_t ktime_get_boottime(void);
```

- **CLOCK_BOOTTIME**

  类似于`ktime_get()`，但在暂停时不会停止。例如，可以用于需要跨过暂停操作与其他机器同步的密钥过期时间。

```c
ktime_t ktime_get_real(void);
```

- **CLOCK_REALTIME**

  返回相对于1970年开始的UNIX纪元的时间（使用协调世界时UTC），与用户空间中的`gettimeofday()`相同。这用于所有需要跨越重启持久化的时戳，如inode时间戳，但对于内部使用应尽量避免，因为它可能会因闰秒更新、NTP调整或用户空间中的`settimeofday()`操作而向后跳跃。

```c
ktime_t ktime_get_clocktai(void);
```

- **CLOCK_TAI**

  类似于`ktime_get_real()`，但使用国际原子时(TAI)参考而不是UTC，以避免在闰秒更新时跳变。在内核中很少有用。

```c
ktime_t ktime_get_raw(void);
```

- **CLOCK_MONOTONIC_RAW**

  类似于`ktime_get()`，但以硬件clocksource相同的速率运行，没有针对时钟漂移的(NTP)调整。这也很少在内核中被需要。

#### 纳秒、timespec64和秒输出

对于上述所有的函数，还有不同格式的变体，具体取决于用户的需求：

```c
u64 ktime_get_ns(void);
u64 ktime_get_boottime_ns(void);
u64 ktime_get_real_ns(void);
u64 ktime_get_clocktai_ns(void);
u64 ktime_get_raw_ns(void);
```

- **纳秒**

  与简单的`ktime_get`函数相同，但返回指定时钟参考下的纳秒数，这对于某些调用者可能更方便。

```c
void ktime_get_ts64(struct timespec64 *);
void ktime_get_boottime_ts64(struct timespec64 *);
void ktime_get_real_ts64(struct timespec64 *);
void ktime_get_clocktai_ts64(struct timespec64 *);
void ktime_get_raw_ts64(struct timespec64 *);
```

- **timespec64**

  与上述函数相同，但返回一个`struct timespec64`，将时间分为秒和纳秒两部分。这可以在打印时间时避免额外的除法，或者在传递给期望`timespec`或`timeval`结构的外部接口时。

```c
time64_t ktime_get_seconds(void);
time64_t ktime_get_boottime_seconds(void);
time64_t ktime_get_real_seconds(void);
time64_t ktime_get_clocktai_seconds(void);
time64_t ktime_get_raw_seconds(void);
```

- **秒**

  返回粗粒度的时间版本为标量`time64_t`。这避免了访问时钟硬件，并将秒数向下舍入到上一次定时器滴答的整秒数，使用相应的参考。
```
粗粒度和快速访问
-------------------------

存在一些额外的变体以适应更为专业化的场景：

.. c:function:: ktime_t ktime_get_coarse( void )
		ktime_t ktime_get_coarse_boottime( void )
		ktime_t ktime_get_coarse_real( void )
		ktime_t ktime_get_coarse_clocktai( void )

.. c:function:: u64 ktime_get_coarse_ns( void )
		u64 ktime_get_coarse_boottime_ns( void )
		u64 ktime_get_coarse_real_ns( void )
		u64 ktime_get_coarse_clocktai_ns( void )

.. c:function:: void ktime_get_coarse_ts64( struct timespec64 * )
		void ktime_get_coarse_boottime_ts64( struct timespec64 * )
		void ktime_get_coarse_real_ts64( struct timespec64 * )
		void ktime_get_coarse_clocktai_ts64( struct timespec64 * )

这些函数比非粗粒度版本执行更快，但精度较低，它们对应于用户空间中的CLOCK_MONOTONIC_COARSE和CLOCK_REALTIME_COARSE，以及等效的启动时间/TAI/原始时间基准（这些在用户空间中不可用）。这里返回的时间对应于最近一次定时器滴答的时间点，可能已经过去多达10毫秒（对于CONFIG_HZ=100的情况），与读取'jiffies'变量类似。这些函数只有在被快速路径调用，并且仍然期望获得优于秒级的精度时才有用，但又无法轻易地使用'jiffies'，例如用于inode的时间戳。
跳过硬件时钟访问可以节省大约100个CPU周期，在大多数具有可靠循环计数器的现代机器上，但在较旧的硬件上，如果采用外部时钟源，则可能节省几微秒。

.. c:function:: u64 ktime_get_mono_fast_ns( void )
		u64 ktime_get_raw_fast_ns( void )
		u64 ktime_get_boot_fast_ns( void )
		u64 ktime_get_tai_fast_ns( void )
		u64 ktime_get_real_fast_ns( void )

这些变体可以从任何上下文安全地调用，包括从不可屏蔽中断(NMI)期间的时间守护程序更新，以及在进入挂起状态时关闭时钟源的情况下。
这对于某些追踪或调试代码以及机器检查报告是有用的，但是大多数驱动程序不应调用它们，因为在某些条件下允许时间跳跃。

已废弃的时间接口
--------------------------

较旧的内核使用了一些其他接口，这些接口正在逐步淘汰，但在移植到这里的第三方驱动程序中可能会出现。特别是，所有返回'struct timeval'或'struct timespec'的接口已被替换，因为tv_sec成员在32位架构上的2038年会溢出。以下是推荐的替代方案：

.. c:function:: void ktime_get_ts( struct timespec * )

请改用ktime_get()或ktime_get_ts64()。

.. c:function:: void do_gettimeofday( struct timeval * )
		void getnstimeofday( struct timespec * )
		void getnstimeofday64( struct timespec64 * )
		void ktime_get_real_ts( struct timespec * )

ktime_get_real_ts64()是直接的替代品，但考虑使用单调时间（ktime_get_ts64()）和/或基于ktime_t的接口（ktime_get()/ktime_get_real()）。

.. c:function:: struct timespec current_kernel_time( void )
		struct timespec64 current_kernel_time64( void )
		struct timespec get_monotonic_coarse( void )
		struct timespec64 get_monotonic_coarse64( void )

这些被ktime_get_coarse_real_ts64()和ktime_get_coarse_ts64()所取代。然而，许多需要粗粒度时间的代码可以使用简单的'jiffies'，而有些驱动程序实际上可能想要更高分辨率的访问器。

.. c:function:: struct timespec getrawmonotonic( void )
		struct timespec64 getrawmonotonic64( void )
		struct timespec timekeeping_clocktai( void )
		struct timespec64 timekeeping_clocktai64( void )
		struct timespec get_monotonic_boottime( void )
		struct timespec64 get_monotonic_boottime64( void )

这些被ktime_get_raw()/ktime_get_raw_ts64()、ktime_get_clocktai()/ktime_get_clocktai_ts64()以及ktime_get_boottime()/ktime_get_boottime_ts64()所取代。
然而，如果特定的时钟源选择对用户不重要，则考虑为了保持一致性转换为ktime_get()/ktime_get_ts64()。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
