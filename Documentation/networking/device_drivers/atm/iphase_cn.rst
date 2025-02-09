### SPDX 许可证标识符: GPL-2.0

==================================
ATM (i)Chip IA Linux 驱动程序源代码
==================================

			      请先阅读

--------------------------------------------------------------------------------

			开始前请阅读！

--------------------------------------------------------------------------------

#### 描述
这是Interphase PCI ATM (i)Chip IA Linux驱动程序源代码发布的README文件。该驱动程序具有以下特性和限制：

- 支持单一的VPI（VPI值为0）
- 对于服务器板卡（带有512K控制内存）支持4K个VC，对于客户端板卡（带有128K控制内存）支持1K个VC
- 支持UBR、ABR和CBR服务类别
- 仅支持AAL5
- 支持在VC上设置PCR
- 支持系统中的多个适配器
- 支持所有版本的Interphase ATM PCI (i)Chip适配卡，包括x575（OC3，控制内存128K、512K，包内存128K、512K和1M）、x525（UTP25）和x531（DS3和E3）。详情请参阅 [http://www.iphase.com/](http://www.iphase.com/)
- 仅支持x86平台
- 支持SMP
开始之前
================


安装
------------

1. 在系统中安装适配器

   要在系统中安装ATM适配器，请按照以下步骤操作：
   a. 以root身份登录
   b. 关闭系统并切断电源
   c. 在系统中安装一个或多个ATM适配器
   d. 将每个适配器连接到ATM交换机上的端口。如果适配器在系统启动时正确连接到交换机，则适配器前面板上的绿色“Link”（链接）LED将亮起
   e. 开启电源并启动系统
2. [ 已删除 ]

3. 重建内核以支持ABR

   [ a. 和 b. 已删除 ]

   c. 重新配置内核，通过"make menuconfig"或"make xconfig"选择Interphase ia驱动程序
   d. 重建内核、可加载模块和ATM工具
   e. 安装新构建的内核和模块，并重启系统
4. 如果ia驱动程序是作为模块构建的，则加载适配器硬件驱动程序（ia驱动程序）

   a. 以root身份登录
b. 切换目录到 `/lib/modules/<kernel-version>/atm`
c. 运行 `"insmod suni.o; insmod iphase.o"`  
    适配器前面板上的黄色“状态”LED将在驱动程序加载到系统中时闪烁
d. 要验证“ia”驱动程序是否成功加载，请运行以下命令：  

      `cat /proc/atm/devices`

    如果驱动程序成功加载，该命令的输出将类似于以下几行：  

      ```
      Itf Type    ESI/"MAC"addr AAL(TX,err,RX,err,drop) ..
      0   ia      xxxxxxxxx  0 ( 0 0 0 0 0 )  5 ( 0 0 0 0 0 )
      ```

    您也可以检查系统日志文件`/var/log/messages`中的与ATM驱动程序相关的信息。
5. Ia 驱动程序配置

5.1 适配器缓冲区的配置
    (i)Chip 板有三种不同的数据包RAM大小变体：128K、512K 和 1M。RAM 大小决定了缓冲区的数量和缓冲区大小。默认的缓冲区大小和数量设置如下：

    | 总RAM大小 | Rx RAM大小 | Tx RAM大小 | Rx 缓冲区大小 | Tx 缓冲区大小 | Rx 缓冲区计数 | Tx 缓冲区计数 |
    |---------|----------|----------|------------|------------|------------|------------|
    | 128K    | 64K      | 64K      | 10K        | 10K        | 6          | 6          |
    | 512K    | 256K     | 256K     | 10K        | 10K        | 25         | 25         |
    | 1M      | 512K     | 512K     | 10K        | 10K        | 51         | 51         |

    这些设置在大多数环境中应该都能很好地工作，但可以通过输入以下命令进行更改：  

    `insmod <IA_DIR>/ia.o IA_RX_BUF=<RX_CNT> IA_RX_BUF_SZ=<RX_SIZE> \  
            IA_TX_BUF=<TX_CNT> IA_TX_BUF_SZ=<TX_SIZE>`  

    其中：
    
    - RX_CNT = 接收缓冲区的数量（范围为1-128）
    - RX_SIZE = 接收缓冲区的大小（范围为48-64K）
    - TX_CNT = 发送缓冲区的数量（范围为1-128）
    - TX_SIZE = 发送缓冲区的大小（范围为48-64K）

    1. 发送和接收缓冲区的大小必须是4的倍数
    2. 应当注意，发送和接收缓冲区所需的内存小于或等于适配器总的数据包内存
5.2 开启ia调试跟踪

    当使用CONFIG_ATM_IA_DEBUG标志构建ia驱动程序时，如果需要，驱动程序可以提供更多调试信息。有一个位掩码变量IADebugFlag控制跟踪输出。您可以在iphase.h中找到IADebugFlag的位图
    可以通过insmod命令行选项开启调试跟踪，例如，“insmod iphase.o IADebugFlag=0xffffffff”可以在加载驱动程序的同时开启所有调试信息
6. 使用ttcp_atm和PVC测试Ia驱动程序

   对于PVC设置，测试机器可以直接连接或者通过交换机连接。如果通过交换机连接，则必须为PVC配置交换机
a. 对于UBR测试：

    在计划接收数据的测试机器上，输入：  

    `ttcp_atm -r -a -s 0.100`

    在另一台测试机器上，输入：  

    `ttcp_atm -t -a -s 0.100 -n 10000`

    运行`ttcp_atm -h`以显示ttcp_atm工具的更多选项。
b. 对于ABR测试：

      这与UBR测试相同，但增加了一个命令选项：

	 -Pabr:max_pcr=<xxx>

      其中：

	     xxx = 最大峰值单元速率，取值范围为170 - 353207
此选项必须在两台机器上都设置。
c. 对于CBR测试：

      这与UBR测试相同，但增加了一个命令选项：

	 -Pcbr:max_pcr=<xxx>

      其中：

	     xxx = 最大峰值单元速率，取值范围为170 - 353207
此选项只能在发送机器上设置。
未解决的问题
==============

联系方式
---------

::

     客户支持：
	 美国：	电话：	(214) 654-5555
			传真：	(214) 654-5500
			电子邮件：	intouch@iphase.com
	 欧洲：	电话：	33 (0)1 41 15 44 00
			传真：	33 (0)1 41 15 12 13
     万维网：	http://www.iphase.com
     匿名FTP：	ftp.iphase.com
