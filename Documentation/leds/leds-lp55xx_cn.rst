以下是提供的英文内容翻译成中文：

=============================
LP5521/LP5523/LP55231/LP5562/LP8501 公共驱动程序
=============================

作者：Milo (Woogyom) Kim <milo.kim@ti.com>

描述
------------

LP5521、LP5523/55231、LP5562 和 LP8501 具有以下共同特性：
- 通过 I2C 访问寄存器
- 设备初始化和去初始化
- 为多个输出通道创建 LED 类设备
- 用户空间接口的设备属性
- 运行 LED 模式的程序存储器

LP55xx 公共驱动程序通过导出函数提供这些功能:
`lp55xx_init_device()` / `lp55xx_deinit_device()`
- `lp55xx_register_leds()` / `lp55xx_unregister_leds()`
- `lp55xx_register_sysfs()` / `lp55xx_unregister_sysfs()`

（驱动程序结构数据）

在 LP55xx 公共驱动程序中，使用了两种不同的数据结构：
- `lp55xx_led`
  控制多路输出 LED 通道，如 LED 电流、通道索引等
- `lp55xx_chip`
  通用芯片控制，例如 I2C 和平台数据
例如，LP5521 最多具有 3 个 LED 通道；
LP5523/55231 具有 9 个输出通道：

  - 对于 LP5521 的 `lp55xx_chip`... `lp55xx_led` #1
                                       `lp55xx_led` #2
                                       `lp55xx_led` #3

  - 对于 LP5523 的 `lp55xx_chip`... `lp55xx_led` #1
                                       `lp55xx_led` #2

                                       `lp55xx_led` #9

（芯片依赖代码）

为了支持特定设备配置，使用了特殊结构 `lpxx_device_config`：
- 最大通道数
  - 复位命令、芯片使能命令
  - 芯片特定初始化
  - 亮度控制寄存器访问
  - 设置 LED 输出电流
  - 运行模式的程序存储器地址访问
  - 额外的设备特定属性

（固件接口）

LP55xx 系列设备具有内部程序存储器，用于运行各种 LED 模式。
该模式数据被保存为用户空间中的文件，
或者十六进制字节串通过I2C接口被写入内存。
LP55xx通用驱动支持固件接口。
LP55xx芯片具有三个编程引擎。
为了加载和运行模式，编程序列如下：
1. 选择一个引擎编号（1/2/3）
2. 更改模式以进行加载
3. 将模式数据写入选定区域
4. 更改模式以运行

LP55xx通用驱动提供了简单的接口如下：
`select_engine`：
    选择用于运行程序的引擎编号
`run_engine`：
    启动通过固件接口加载的程序
`firmware`：
    加载程序数据

对于LP5523，还需要一个额外的命令，即`enginex_leds`，
它用于在每个引擎编号下选择LED输出。
更详细的说明，请参见`leds-lp5523.txt`。
例如，在LP5521的引擎#1中运行闪烁模式：

```
echo 1 > /sys/bus/i2c/devices/xxxx/select_engine
echo 1 > /sys/class/firmware/lp5521/loading
echo "4000600040FF6000" > /sys/class/firmware/lp5521/data
echo 0 > /sys/class/firmware/lp5521/loading
echo 1 > /sys/bus/i2c/devices/xxxx/run_engine
```

例如，在LP55231的引擎#3中运行闪烁模式，

两个LED被配置为模式输出通道：

```
echo 3 > /sys/bus/i2c/devices/xxxx/select_engine
echo 1 > /sys/class/firmware/lp55231/loading
echo "9d0740ff7e0040007e00a0010000" > /sys/class/firmware/lp55231/data
echo 0 > /sys/class/firmware/lp55231/loading
echo "000001100" > /sys/bus/i2c/devices/xxxx/engine3_leds
echo 1 > /sys/bus/i2c/devices/xxxx/run_engine
```

要同时在引擎#2和#3中启动闪烁模式：

```
for idx in 2 3
do
  echo $idx > /sys/class/leds/red/device/select_engine
  sleep 0.1
  echo 1 > /sys/class/firmware/lp5521/loading
  echo "4000600040FF6000" > /sys/class/firmware/lp5521/data
  echo 0 > /sys/class/firmware/lp5521/loading
done
echo 1 > /sys/class/leds/red/device/run_engine
```

这是另一个针对LP5523的例子，
通过`engine2_leds`选择了全部的LED串：

```
echo 2 > /sys/bus/i2c/devices/xxxx/select_engine
echo 1 > /sys/class/firmware/lp5523/loading
echo "9d80400004ff05ff437f0000" > /sys/class/firmware/lp5523/data
echo 0 > /sys/class/firmware/lp5523/loading
echo "111111111" > /sys/bus/i2c/devices/xxxx/engine2_leds
echo 1 > /sys/bus/i2c/devices/xxxx/run_engine
```

一旦将`loading`设置为0，注册的回调函数就会被调用。
在回调函数中，选定的引擎被加载并且内存得到更新。
要运行编程模式，应启用`run_engine`属性。
LP8501的模式序列与LP5523类似，
但是模式数据是特定的。
例 1）使用引擎 1：

```shell
echo 1 > /sys/bus/i2c/devices/xxxx/select_engine
echo 1 > /sys/class/firmware/lp8501/loading
echo "9d0140ff7e0040007e00a001c000" > /sys/class/firmware/lp8501/data
echo 0 > /sys/class/firmware/lp8501/loading
echo 1 > /sys/bus/i2c/devices/xxxx/run_engine
```

例 2）同时使用引擎 2 和 3：

```shell
echo 2 > /sys/bus/i2c/devices/xxxx/select_engine
sleep 1
echo 1 > /sys/class/firmware/lp8501/loading
echo "9d0140ff7e0040007e00a001c000" > /sys/class/firmware/lp8501/data
echo 0 > /sys/class/firmware/lp8501/loading
sleep 1
echo 3 > /sys/bus/i2c/devices/xxxx/select_engine
sleep 1
echo 1 > /sys/class/firmware/lp8501/loading
echo "9d0340ff7e0040007e00a001c000" > /sys/class/firmware/lp8501/data
echo 0 > /sys/class/firmware/lp8501/loading
sleep 1
echo 1 > /sys/class/leds/d1/device/run_engine
```

（`run_engine`和`firmware_cb`）

运行程序数据的序列是通用的，
但每个设备都有自己的命令专用寄存器地址。
为了支持这一点，在每个驱动程序中可以配置`run_engine`和`firmware_cb`。
- `run_engine`：
    控制选定的引擎。
- `firmware_cb`：
    加载固件完成后的回调函数。
芯片特定的命令用于加载和更新程序内存
（预定义的模式数据）

如果没有固件接口，LP55xx 驱动程序提供了另一种方法来加载LED模式。这就是“预定义”模式。
平台数据中定义了预设模式，并且如果需要的话，可以通过 sysfs 加载它（们）。

要使用预设模式的概念，应配置 `patterns` 和 `num_patterns`。

预设模式数据示例：

  /* mode_1: 闪烁数据 */
  static const u8 mode_1[] = {
		0x40, 0x00, 0x60, 0x00, 0x40, 0xFF, 0x60, 0x00,
		};

  /* mode_2: 始终开启 */
  static const u8 mode_2[] = { 0x40, 0xFF, };

  struct lp55xx_predef_pattern board_led_patterns[] = {
	{
		.r = mode_1,
		.size_r = ARRAY_SIZE(mode_1),
	},
	{
		.b = mode_2,
		.size_b = ARRAY_SIZE(mode_2),
	},
  }

  struct lp55xx_platform_data lp5562_pdata = {
  ..
	.patterns      = board_led_patterns,
	.num_patterns  = ARRAY_SIZE(board_led_patterns),
  };

然后，mode_1 和 mode_2 可以通过 sysfs 运行：

  echo 1 > /sys/bus/i2c/devices/xxxx/led_pattern    # 红色 LED 闪烁模式
  echo 2 > /sys/bus/i2c/devices/xxxx/led_pattern    # 蓝色 LED 始终开启

要停止运行模式：

  echo 0 > /sys/bus/i2c/devices/xxxx/led_pattern
