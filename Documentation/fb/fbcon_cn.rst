=======================
帧缓冲控制台
=======================

帧缓冲控制台（fbcon）正如其名，是在帧缓冲设备之上运行的文本控制台。它具有任何标准文本控制台驱动程序的功能，例如VGA控制台，并且由于其图形特性而具备额外功能。
在x86架构中，帧缓冲控制台是可选的，有些人甚至将其视为玩具。对于其他架构而言，它是唯一可用的显示设备，无论是文本还是图形。
那么fbcon有哪些特点呢？帧缓冲控制台支持高分辨率、各种字体类型、显示旋转、原始多头显示等。理论上，多色字体、混合、抗锯齿以及由底层显卡提供的任何功能也是可能实现的。

A. 配置
================

可以通过使用您喜欢的内核配置工具来启用帧缓冲控制台。它位于设备驱动程序 -> 图形支持 -> 控制台显示驱动程序支持 -> 帧缓冲控制台支持下。
选择'y'以静态编译支持或'm'以模块形式支持。该模块将是fbcon。
为了使fbcon激活，至少需要一个帧缓冲驱动程序，因此可以从众多可用的驱动程序中进行选择。对于x86系统，几乎普遍都有VGA卡，所以vga16fb和vesafb将始终可用。然而，使用特定芯片组的驱动程序会为您提供更高的速度和更多功能，如动态更改视频模式的能力。
为了显示企鹅标志，请选择图形支持 -> 启动标志中的任意标志。
此外，您需要选择至少一个内置字体，但如果您不做任何操作，内核配置工具将为您选择一个，默认情况下通常是8x16字体。
注意：一个常见的错误报告是启用了帧缓冲但没有启用帧缓冲控制台。根据驱动程序的不同，您可能会得到一个空白或乱码的显示，但系统仍然会启动完成。如果您幸运地拥有一个不改变显卡设置的驱动程序，那么您仍然可以获得VGA控制台。

B. 加载
==========

可能的情况：

1. 驱动程序和fbcon静态编译

通常，fbcon会自动接管您的控制台。值得注意的是vesafb。它需要用vga=引导参数明确激活。
2. 驱动程序静态编译，fbcon 作为模块编译

   根据驱动程序的不同，你可能会得到一个标准控制台或如上所述的混乱显示。要获得帧缓冲控制台，请执行 `modprobe fbcon`。
   
3. 驱动程序作为模块编译，fbcon 静态编译

   你会得到你的标准控制台。一旦驱动程序通过 `modprobe xxxfb` 加载后，fbcon 将自动接管控制台，除非使用了 fbcon=map:n 选项。详见下文。

4. 驱动程序和 fbcon 均作为模块编译
你可以按任意顺序加载它们。一旦两者都加载完毕，fbcon 将接管控制台。

C. 启动选项

   帧缓冲控制台有几个鲜为人知的启动选项，可以改变其行为。
   
1. fbcon=font:<name>

   选择初始字体。值 'name' 可以是任何内置的字体：10x18、6x10、6x8、7x14、Acorn8x8、MINI4x6、PEARL8x8、ProFont6x11、SUN12x22、SUN8x16、TER16x32、VGA8x16、VGA8x8。
注意，并非所有驱动程序都能处理宽度不是8的倍数的字体，例如 vga16fb。
   
2. fbcon=map:<0123>

   这是一个有趣的选项。它告诉系统将哪个驱动程序映射到哪个控制台。值 '0123' 是一个序列，会重复直到总长度为64（这是可用控制台的数量）。在上述示例中，它扩展为 012301230123...，映射关系如下：

   ```
   tty | 1 2 3 4 5 6 7 8 9 ..
   fb  | 0 1 2 3 0 1 2 3 0 ..
   （通过 'cat /proc/fb' 可以查看 fb 编号）
   ```

   一个可能有用的副作用是使用超过已加载帧缓冲驱动程序数量的映射值。例如，如果只有一个可用的驱动程序 fb0，添加 fbcon=map:1 会告诉 fbcon 不接管控制台。
之后，当你想要将控制台映射到帧缓冲设备时，可以使用 `con2fbmap` 工具。
3. fbcon=vc:<n1>-<n2>

此选项告诉 `fbcon` 只接管由值 `<n1>` 和 `<n2>` 指定范围内的控制台。指定范围之外的其他控制台仍由标准控制台驱动程序控制。
注意：对于 x86 机器，标准控制台是 VGA 控制台，通常位于同一视频卡上。因此，由 VGA 控制台控制的控制台将会出现乱码。
4. fbcon=rotate:<n>

此选项更改控制台显示的方向角度。值 `<n>` 接受以下几种情况：

    - 0 - 正常方向（0 度）
    - 1 - 顺时针方向（90 度）
    - 2 - 颠倒方向（180 度）
    - 3 - 逆时针方向（270 度）

可以在任何时候通过向 `/sys/class/graphics/fbcon` 中的以下两个属性之一发送相同的数字来改变角度：

    - rotate - 旋转活动控制台的显示
    - rotate_all - 旋转所有控制台的显示

只有当内核编译了帧缓冲控制台旋转支持时，控制台旋转才会可用。
注意：这只是控制台的旋转。任何其他使用帧缓冲的应用程序仍会保持其“正常”方向。实际上，底层的帧缓冲驱动程序对控制台旋转完全不知情。
5. fbcon=margin:<color>

此选项指定边距的颜色。边距是指屏幕右侧和底部未被文本使用的剩余区域，默认情况下，这些区域为黑色。“color”值是一个整数，具体取决于所使用的帧缓冲驱动程序。
6. fbcon=nodefer

如果内核编译了延迟帧缓冲控制台接管支持，则通常帧缓冲的内容（由固件/引导加载程序留下的）会一直保留到实际有文本输出到控制台为止。
此选项使 `fbcon` 立即绑定到 `fbdev` 设备。
7. fbcon=logo-pos:<location>

唯一的可能位置是 “center”（不带引号），指定后，启动标志将从默认的左上角位置移动到帧缓冲区的中心。如果由于多 CPU 而显示多个标志，整个标志行将作为一个整体进行移动。
8. fbcon=logo-count:<n>

值 'n' 覆盖启动标志的数量。0 禁用标志，而 -1 使用默认值，即在线 CPU 的数量。

C. 连接、断开和卸载

在介绍如何连接、断开和卸载帧缓冲控制台（framebuffer console）之前，先通过一个依赖关系图示来帮助理解：

控制台层（console layer），像大多数子系统一样，需要一个与硬件交互的驱动程序。因此，在 VGA 控制台中：

```
控制台 ---> VGA 驱动 ---> 硬件
```

假设 VGA 驱动可以被卸载，则首先需要将 VGA 驱动从控制台层解绑，然后才能卸载该驱动。如果 VGA 驱动仍绑定到控制台层，则无法卸载。更多信息请参见 `Documentation/driver-api/console.rst`。

对于帧缓冲控制台（fbcon）来说更为复杂，因为 fbcon 是控制台和驱动之间的中间层：

```
控制台 ---> fbcon ---> fbdev 驱动 ---> 硬件
```

如果 fbdev 驱动绑定到 fbcon，则无法卸载这些驱动；同样地，如果 fbcon 绑定到控制台层，则也无法卸载 fbcon。
因此，要卸载 fbdev 驱动，必须首先将 fbcon 从控制台层解绑，然后再将 fbdev 驱动从 fbcon 解绑。幸运的是，将 fbcon 从控制台层解绑时会自动将帧缓冲驱动从 fbcon 解绑。因此无需显式地将 fbdev 驱动从 fbcon 解绑。

那么我们如何将 fbcon 从控制台解绑呢？部分答案可以在 `Documentation/driver-api/console.rst` 中找到。总结如下：

向代表帧缓冲控制台驱动的 bind 文件写入一个值。假设 vtcon1 代表 fbcon，则：

```
echo 1 > /sys/class/vtconsole/vtcon1/bind - 将帧缓冲控制台连接到控制台层
echo 0 > /sys/class/vtconsole/vtcon1/bind - 将帧缓冲控制台从控制台层断开
```

如果 fbcon 已经从控制台层断开，则您的引导控制台驱动（通常是 VGA 文本模式）将接管。少数驱动（如 rivafb 和 i810fb）会为您恢复 VGA 文本模式。对于其他驱动，您必须在断开 fbcon 之前采取一些额外步骤以确保 VGA 文本模式正确恢复。以下是一个方法之一：

1. 下载或安装 vbetool。这个工具现在大部分发行版中都有包含，并且通常作为挂起/恢复工具的一部分。
2. 在内核配置中，确保 CONFIG_FRAMEBUFFER_CONSOLE 设置为 'y' 或 'm'。启用您喜欢的一个或多个帧缓冲驱动。
3. 启动到文本模式并以 root 用户身份运行：

   ```
   vbetool vbestate save > <vga 状态文件>
   ```

   上述命令将图形硬件寄存器的内容保存到 <vga 状态文件>。此步骤只需执行一次，因为状态文件可以重复使用。
4. 如果 fbcon 编译为模块，请加载 fbcon：

   ```
   modprobe fbcon
   ```

5. 现在要断开 fbcon：

   ```
   vbetool vbestate restore < <vga 状态文件> && \
   echo 0 > /sys/class/vtconsole/vtcon1/bind
   ```

6. 完成了，您已经回到 VGA 模式。如果您将 fbcon 编译为模块，则可以通过 'rmmod fbcon' 卸载它。
7. 重新绑定 fbcon：

       echo 1 > /sys/class/vtconsole/vtcon1/bind

8. 当 fbcon 解绑后，所有注册到系统的驱动程序也会解绑。这意味着 fbcon 和各个帧缓冲区驱动可以随意卸载或重新加载。重新加载驱动程序或 fbcon 将自动将控制台、fbcon 和驱动程序绑定在一起。如果在不解绑 fbcon 的情况下卸载所有驱动程序，则控制台将无法与 fbcon 绑定。

### 对于 vesafb 用户的注意事项：
=======================

不幸的是，如果你的启动行包含一个设置硬件为图形模式的 vga=xxx 参数（例如加载 vesafb 时），vgacon 将不会加载。相反，vgacon 会用 dummycon 替换默认的启动控制台，因此在解绑 fbcon 后你将看不到任何显示。你的机器仍然运行着，所以你可以重新绑定 vesafb。然而，要重新绑定 vesafb，你需要执行以下操作之一：

#### 方案一：

    a. 在解绑 fbcon 之前，执行以下命令：

	vbetool vbemode save > <vesa 状态文件> # 每个 vesafb 模式只需执行一次，此文件可重复使用

    b. 如步骤 5 所述解绑 fbcon。
c. 重新绑定 fbcon：

	vbetool vbestate restore < <vesa 状态文件> && \
	echo 1 > /sys/class/vtconsole/vtcon1/bind

#### 方案二：

    a. 在解绑 fbcon 之前，执行以下命令：

	echo <ID> > /sys/class/tty/console/bind

	vbetool vbemode get

    b. 记下模式编号。

    b. 如步骤 5 所述解绑 fbcon。
c. 重新绑定 fbcon：

	vbetool vbemode set <模式编号> && \
	echo 1 > /sys/class/vtconsole/vtcon1/bind

### 示例：
========

以下是两个示例 Bash 脚本，可以在 X86 平台上用于绑定或解绑帧缓冲区控制台驱动程序：

```
#!/bin/bash
# 解绑 fbcon

# 更改为实际的 vgastate 文件路径
# 或者使用 VGASTATE=$1 来指定运行时的状态文件
VGASTATE=/tmp/vgastate

# vbetool 的路径
VBETOOL=/usr/local/bin

for (( i = 0; i < 16; i++))
do
    if test -x /sys/class/vtconsole/vtcon$i; then
	if [ `cat /sys/class/vtconsole/vtcon$i/name | grep -c "frame buffer"` \
	     = 1 ]; then
	    if test -x $VBETOOL/vbetool; then
	       echo Unbinding vtcon$i
	       $VBETOOL/vbetool vbestate restore < $VGASTATE
	       echo 0 > /sys/class/vtconsole/vtcon$i/bind
	    fi
	fi
    fi
done
```

```
---------------------------------------------------------------------------
#!/bin/bash
# 绑定 fbcon

for (( i = 0; i < 16; i++))
do
    if test -x /sys/class/vtconsole/vtcon$i; then
	if [ `cat /sys/class/vtconsole/vtcon$i/name | grep -c "frame buffer"` \
	     = 1 ]; then
	  echo Unbinding vtcon$i
	  echo 1 > /sys/class/vtconsole/vtcon$i/bind
	fi
    fi
done
```

Antonino Daplas <adaplas@pol.net>
