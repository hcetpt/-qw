关于sunxi时钟系统的常见问题解答
====================================

本文档包含了一些人们经常询问的有关sunxi时钟系统的信息，以及必要的ASCII艺术图。

**问：**为什么主24MHz振荡器可以被关闭？这不会破坏系统吗？

**答：**24MHz振荡器允许关闭以节省电力。确实，如果随意地关闭它，系统将停止运行，但通过正确的步骤，可以在保持系统运行的同时关闭它。考虑这个简化的挂起示例：

在系统运行时，你会看到如下结构：

```
24MHz         32kHz
  |           
 PLL1         
  \           
   \_ CPU Mux
        |     
      [CPU]   
```

当你准备挂起时，你将CPU Mux切换到32kHz振荡器：

```
24MHz         32kHz
  |            |
 PLL1          |
               /
         CPU Mux _/
           |     
         [CPU]   
```

最后，你可以关闭主振荡器：

```
                   32kHz
                     |
                     |
                    /
         CPU Mux _/
           |     
         [CPU]
```

**问：**我在哪里可以了解更多关于sunxi时钟的信息？

**答：**linux-sunxi维基有一个页面记录了时钟寄存器，你可以在以下网址找到它：

        http://linux-sunxi.org/A10/CCM

当前最权威的信息来源是Allwinner发布的ccmu驱动程序，你可以在以下网址找到它：

        https://github.com/linux-sunxi/linux-sunxi/tree/sunxi-3.0/arch/arm/mach-sun4i/clock/ccmu
