### Adjunct Processor (AP) 设施

#### 引言
Adjunct Processor (AP) 设施是一种IBM Z加密设施，由三个AP指令和1至256张PCIe加密适配卡组成。AP设备为运行在IBM Z系统LPAR中的Linux系统所分配的所有CPU提供加密功能。AP适配卡通过AP总线暴露出来。vfio-ap的动机是利用VFIO中介设备框架使AP卡可供KVM客户机使用。这一实现很大程度上依赖于s390虚拟化设施，后者承担了大部分直接访问AP设备的繁重工作。

#### AP 架构概览
为了便于理解设计，我们首先定义一些术语：

* **AP适配器**

  AP适配器是可以在IBM Z中执行加密功能的适配卡。一个LPAR可以分配0到256个适配器。分配给运行Linux主机的LPAR的适配器将对Linux主机可用。每个适配器由0到255之间的数字标识；然而，最大适配器编号取决于机器型号和/或适配器类型。
  
  安装后，通过任何CPU执行的AP指令可以访问AP适配器。
  
  AP适配卡通过系统的激活配置文件（可通过HMC编辑）分配给特定的LPAR。当Linux主机系统在LPAR中启动时，AP总线会检测分配给LPAR的AP适配卡，并为每个分配的适配器创建一个sysfs设备。例如，如果适配器4和10（0x0a）被分配给LPAR，则AP总线会创建以下sysfs设备条目：
  
    /sys/devices/ap/card04
    /sys/devices/ap/card0a
    
  这些设备的符号链接也会在AP总线设备子目录中创建：
    
    /sys/bus/ap/devices/[card04]
    /sys/bus/ap/devices/[card0a]

* **AP域**

  适配器被划分为域。根据适配器类型和硬件配置，适配器最多可包含256个域。域由0到255之间的数字标识；然而，最大域编号取决于机器型号和/或适配器类型。域可以视为用于处理AP命令的一组硬件寄存器和内存。域可以配置一个安全私钥用于明文密钥加密。域可以根据其访问方式分为两类：
  
    * **使用域**：是通过AP指令来处理AP命令的目标域；
    * **控制域**：是通过发送到使用域的AP命令更改的域；例如，设置控制域的安全私钥。
  
  AP使用域和控制域通过系统的激活配置文件（可通过HMC编辑）分配给特定的LPAR。当Linux主机系统在LPAR中启动时，AP总线模块会检测分配给LPAR的AP使用域和控制域。每个使用域的域号和每个AP适配器的适配器号组合起来创建AP队列设备（参见下面的AP队列部分）。每个控制域的域号将表示为位掩码并存储在sysfs文件/sys/bus/ap/ap_control_domain_mask中。掩码中的位从最高有效位到最低有效位对应于域0-255。
  
* **AP队列**

  AP队列是将AP命令发送到特定适配器内的使用域的方式。AP队列由一个元组标识，该元组由AP适配器ID（APID）和AP队列索引（APQI）组成。APQI对应于适配器内部的特定使用域号。这个元组形成AP队列号（APQN），唯一标识一个AP队列。AP指令包含一个字段，其中包含APQN以标识要发送AP命令进行处理的AP队列。
  
  当AP总线模块加载时，AP总线将为从检测到的AP适配器和使用域号交叉乘积中得出的每个可能的APQN创建一个sysfs设备。例如，如果适配器4和10（0x0a）以及使用域6和71（0x47）被分配给LPAR，则AP总线会创建以下sysfs条目：
  
    /sys/devices/ap/card04/04.0006
    /sys/devices/ap/card04/04.0047
    /sys/devices/ap/card0a/0a.0006
    /sys/devices/ap/card0a/0a.0047
  
  这些设备的符号链接将在AP总线设备子目录中创建：
  
    /sys/bus/ap/devices/[04.0006]
    /sys/bus/ap/devices/[04.0047]
    /sys/bus/ap/devices/[0a.0006]
    /sys/bus/ap/devices/[0a.0047]

* **AP指令**：

  共有三种AP指令：

  * NQAP：将AP命令请求消息入队到队列中；
  * DQAP：从队列中出队AP命令响应消息；
  * PQAP：管理队列。
  
  AP指令标识处理AP命令的目标域；这必须是一个使用域之一。AP命令可能会修改不是使用域的某个域，但被修改的域必须是控制域之一。
让我们现在来看看如何解释在来宾上执行的 AP 指令被硬件所理解。

一个名为 Crypto 控制块（CRYCB）的卫星控制块连接到了我们的主要硬件虚拟化控制块上。CRYCB 包含一个 AP 控制块（APCB），该控制块有三个字段用于标识适配器、使用域和控制域，这些都分配给了 KVM 来宾：

* AP 掩码（APM）字段是一个位掩码，用于标识分配给 KVM 来宾的 AP 适配器。掩码中的每一位从左到右对应一个从 0 到 255 的 APID。如果某一位被设置，则对应的适配器对 KVM 来宾有效。
* AP 队列掩码（AQM）字段是一个位掩码，用于标识分配给 KVM 来宾的 AP 使用域。掩码中的每一位从左到右对应一个从 0 到 255 的 AP 队列索引（APQI）。如果某一位被设置，则对应的队列对 KVM 来宾有效。
* AP 域掩码字段是一个位掩码，用于标识分配给 KVM 来宾的 AP 控制域。ADM 位掩码控制哪些域可以通过来自来宾向使用域发送的 AP 命令请求消息进行更改。掩码中的每一位从左到右对应一个从 0 到 255 的域。如果某一位被设置，则对应的域可以由发送到使用域的 AP 命令请求消息修改。

回想一下关于 AP 队列的描述，AP 指令包含一个 APQN 以标识要发送 AP 命令请求消息（NQAP 和 PQAP 指令）或从中接收命令回复消息（DQAP 指令）的 AP 队列。APQN 的有效性由通过 APM 和 AQM 计算得到的矩阵定义；它是所有分配的适配器编号（APM）与所有分配的队列索引（AQM）的笛卡尔积。例如，如果适配器 1 和 2 以及使用域 5 和 6 分配给了一个来宾，则 APQN (1,5)，(1,6)，(2,5) 和 (2,6) 将对来宾有效。

APQN 可以提供安全密钥功能——即每个域的私钥存储在适配器卡上——因此每个 APQN 必须最多分配给一个来宾或 Linux 主机。

**示例 1：有效的配置**

```
--------------------
来宾1: 适配器 1,2  域 5,6
来宾2: 适配器 1,2  域 7

这是有效的，因为两个来宾有一组唯一的 APQN：
   来宾1 有 APQN (1,5)，(1,6)，(2,5)，(2,6)；
   来宾2 有 APQN (1,7)，(2,7)
```

**示例 2：有效的配置**

```
--------------------
来宾1: 适配器 1,2 域 5,6
来宾2: 适配器 3,4 域 5,6

这也是有效的，因为两个来宾有一组唯一的 APQN：
   来宾1 有 APQN (1,5)，(1,6)，(2,5)，(2,6)；
   来宾2 有 APQN (3,5)，(3,6)，(4,5)，(4,6)
```

**示例 3：无效的配置**

```
--------------------
来宾1: 适配器 1,2  域 5,6
来宾2: 适配器 1    域 6,7

这是一个无效的配置，因为两个来宾都可以访问 APQN (1,6)
```

### 设计

设计引入了以下三个新对象：

1. AP 矩阵设备
2. VFIO AP 设备驱动程序（vfio_ap.ko）
3. VFIO AP 中介传递设备

#### VFIO AP 设备驱动程序

VFIO AP（vfio_ap）设备驱动程序具有以下目的：

1. 提供接口来为 KVM 来宾的安全使用保留 APQN
2. 设置 VFIO 中介设备接口来管理 vfio_ap 中介设备，并创建 sysfs 接口以分配适配器、使用域和控制域，这些构成了 KVM 来宾的矩阵
3. 在 KVM 来宾的 SIE 状态描述中引用的 CRYCB 所包含的 APCB 中配置 APM、AQM 和 ADM，以授予来宾访问 AP 设备矩阵的权限

#### 为 KVM 来宾的独占使用预留 APQN

下面的框图说明了预留 APQN 的机制：

```
					+------------------+
			 7 remove       |                  |
	   +--------------------> cex4queue driver |
	   |                    |                  |
	   |                    +------------------+
	   |
	   |
	   |                    +------------------+          +----------------+
	   |  5 register driver |                  | 3 create |                |
	   |   +---------------->   Device core    +---------->  matrix device |
	   |   |                |                  |          |                |
	   |   |                +--------^---------+          +----------------+
	   |   |                         |
	   |   |                         +-------------------+
	   |   | +-----------------------------------+       |
	   |   | |      4 register AP driver         |       | 2 register device
	   |   | |                                   |       |
  +--------+---+-v---+                      +--------+-------+-+
  |                  |                      |                  |
  |      ap_bus      +--------------------- >  vfio_ap driver  |
  |                  |       8 probe        |                  |
  +--------^---------+                      +--^--^------------+
  6 edit   |                                   |  |
    apmask |     +-----------------------------+  | 11 mdev create
    aqmask |     |           1 modprobe           |
  +--------+-----+---+           +----------------+-+         +----------------+
  |                  |           |                  |10 create|     mediated   |
  |      admin       |           | VFIO device core |--------->     matrix     |
  |                  +           |                  |         |     device     |
  +------+-+---------+           +--------^---------+         +--------^-------+
	 | |                              |                            |
	 | | 9 create vfio_ap-passthrough |                            |
	 | +------------------------------+                            |
	 +-------------------------------------------------------------+
		     12  assign adapter/domain/control domain
```

预留 AP 队列供 KVM 来宾使用的流程如下：

1. 管理员加载 vfio_ap 设备驱动程序
2. vfio-ap 驱动程序在其初始化期间会向设备核心注册一个单一的“矩阵”设备。这将作为所有用于为来宾配置 AP 矩阵的 vfio_ap 中介设备的父设备
3. 设备核心创建 `/sys/devices/vfio_ap/matrix` 设备
4. vfio_ap 设备驱动程序会向 AP 总线注册类型为 10 及以上的 AP 队列设备（CEX4 及更新版本）。驱动程序将提供 vfio_ap 驱动程序的探测和移除回调接口。早于 CEX4 队列的设备不支持，以简化实现，避免不必要的复杂性，因为旧设备将在不久的将来退出服务，并且很少有旧系统可供测试。
5. AP总线将vfio_ap设备驱动程序注册到设备核心。
6. 管理员编辑AP适配器和队列掩码以预留AP队列供vfio_ap设备驱动程序使用。
7. AP总线从默认的zcrypt cex4queue驱动程序中移除为vfio_ap驱动程序预留的AP队列。
8. AP总线探测vfio_ap设备驱动程序以绑定为其预留的队列。
9. 管理员创建一个passthrough类型的vfio_ap中介设备以供虚拟机使用。
10. 管理员分配适配器、使用域和控制域以供虚拟机独占使用。
设置VFIO中介设备接口
-------------------------------
VFIO AP设备驱动程序利用VFIO中介设备核心驱动程序的通用接口来：

* 注册一个AP中介总线驱动程序，用于向VFIO组添加或从中移除一个vfio_ap中介设备。
* 创建和销毁一个vfio_ap中介设备。
* 将vfio_ap中介设备添加到AP中介总线驱动程序中或从中移除。
* 将vfio_ap中介设备添加到IOMMU组中或从中移除。

以下的高级块图展示了VFIO AP中介设备驱动程序的主要组件和接口：

```
   +-------------+
   |             |
   | +---------+ | mdev_register_driver() +--------------+
   | |  Mdev   | +<-----------------------+              |
   | |  bus    | |                        | vfio_mdev.ko |
   | | driver  | +----------------------->+              |<-> VFIO用户
   | +---------+ |    probe()/remove()    +--------------+    API
   |             |
   |  MDEV CORE  |
   |   MODULE    |
   |   mdev.ko   |
   | +---------+ | mdev_register_parent() +--------------+
   | |Physical | +<-----------------------+              |
   | | device  | |                        |  vfio_ap.ko  |<-> 矩阵
   | |interface| +----------------------->+              |    设备
   | +---------+ |       callback         +--------------+
   +-------------+
```

在vfio_ap模块初始化期间，矩阵设备通过'mdev_parent_ops'结构进行注册，该结构提供了用于管理中介矩阵设备的sysfs属性结构、mdev函数以及回调接口。
* sysfs属性结构：

  supported_type_groups
    VFIO中介设备框架支持创建用户自定义的中介设备类型。这些中介设备类型通过'supported_type_groups'结构指定，当设备注册到中介设备框架时，此过程会为注册设备下的每个中介设备类型创建sysfs结构。与设备类型一起提供的还有中介设备类型的sysfs属性。
VFIO AP设备驱动程序将注册一种用于passthrough设备的中介设备类型：

      /sys/devices/vfio_ap/matrix/mdev_supported_types/vfio_ap-passthrough

    只提供VFIO mdev框架所需的只读属性：

	... name
	... device_api
	... available_instances
	... device_api

    其中：

	* name:
	    指定中介设备类型的名称
	* device_api:
	    中介设备类型的API
	* available_instances:
	    可创建的vfio_ap中介passthrough设备的数量
	* device_api:
	    指定VFIO API
  mdev_attr_groups
    此属性组标识中介设备的用户自定义sysfs属性。当设备注册到VFIO中介设备框架时，'mdev_attr_groups'结构中标识的sysfs属性文件将在vfio_ap中介设备目录下创建。对于vfio_ap中介设备的sysfs属性包括：

    assign_adapter / unassign_adapter:
      仅写入属性，用于向vfio_ap中介设备分配/取消分配AP适配器。要分配/取消分配适配器，需将适配器的APID回显到相应的属性文件中。
assign_domain / unassign_domain:
      仅写入属性，用于向vfio_ap中介设备分配/取消分配AP使用域。要分配/取消分配一个域，需要将使用域的域号回显到相应的属性文件中。
matrix:
      显示从分配给vfio_ap中介设备的适配器和域号的笛卡尔积中得出的APQNs的只读文件。
guest_matrix:
      一个只读文件，用于显示从适配器和域编号的笛卡尔积中得出的APQN（适配器-域配对编号）。这些编号分别分配给了KVM客户机的CRYCB中的APM和AQM字段。这可能与绑定到vfio_ap中介设备的APQN不同，如果任何APQN没有引用绑定到vfio_ap设备驱动程序的队列设备（即，该队列不在主机的AP配置中）。
assign_control_domain / unassign_control_domain:
      用于分配/取消分配AP控制域到/from vfio_ap中介设备的写入只用属性。要分配/取消分配控制域，需要将要分配/取消分配的域的ID回显到相应的属性文件中。
control_domains:
      一个只读文件，用于显示分配给vfio_ap中介设备的控制域编号。
ap_config:
      一个可读写文件，当写入时，允许一次性替换vfio_ap中介设备的所有三个AP矩阵掩码。
提供三个掩码，一个用于适配器，一个用于域，还有一个用于控制域。如果给定的状态无法设置，则不对vfio-ap中介设备进行任何更改。
写入到ap_config的数据格式如下：
      {amask},{dmask},{cmask}\n

      \n 是换行符
amask、dmask 和 cmask 是掩码，用于标识应分配给中介设备的哪些适配器、域和控制域。
掩码的格式如下：
      0xNN..NN

      其中 NN..NN 是64个十六进制字符，代表一个256位的值
最左边（最高位序）的位表示适配器/域 0
为了查看表示您的mdev当前配置的一组掩码示例，只需使用 `cat` 命令查看 ap_config 文件。
设置大于系统允许的最大值的适配器编号或域编号会导致错误。
此属性旨在供自动化使用。最终用户最好使用各自适配器、域和控制域的分配/取消分配属性。

* 功能：

  创建：
    分配`ap_matrix_mdev`结构，该结构由vfio_ap驱动程序使用来：

    * 存储指向用于mdev客体的KVM结构的引用
    * 存储通过相应sysfs属性文件分配给适配器、域和控制域的AP矩阵配置
    * 存储可供客体使用的适配器、域和控制域的AP矩阵配置。不允许向客体提供访问那些不存在或未绑定到vfio_ap设备驱动程序的队列设备所对应的APQNs
  删除：
    释放vfio_ap中介设备的`ap_matrix_mdev`结构
    这仅在运行中的客体没有使用该mdev时才被允许

* 回调接口：

  打开设备(open_device)：
    vfio_ap驱动程序使用此回调来为矩阵mdev设备注册一个VFIO_GROUP_NOTIFY_SET_KVM通知器回调函数。打开设备回调由用户空间调用以将矩阵mdev设备的VFIO IOMMU组连接到MDEV总线。通过此回调提供对用于配置KVM客体的KVM结构的访问权限。
    KVM结构用于根据vfio_ap中介设备的sysfs属性文件定义配置客体对AP矩阵的访问权限。
  关闭设备(close_device)：
    取消注册矩阵mdev设备的VFIO_GROUP_NOTIFY_SET_KVM通知器回调函数，并重新配置客体的AP矩阵。
  输入输出控制(ioctl)：
    此回调处理由vfio框架定义的VFIO_DEVICE_GET_INFO和VFIO_DEVICE_RESET输入输出控制指令。
    配置客体的AP资源

------------------

配置KVM客体的AP资源将在调用VFIO_GROUP_NOTIFY_SET_KVM通知器回调时执行。当用户空间连接到KVM时会调用通知器函数。通过其APCB配置客体的AP资源，具体步骤如下：

* 设置与通过vfio_ap中介设备的“assign_adapter”接口分配的APID相对应的APM中的位
设置与通过其“assign_domain”接口分配给vfio_ap中介设备的域相对应的AQM中的位
设置与通过其“assign_control_domains”接口分配给vfio_ap中介设备的域dIDs相对应的ADM中的位

Linux设备模型不允许将未绑定到支持其传递的设备驱动程序的设备传递给KVM来宾。因此，没有引用绑定到vfio_ap设备驱动程序的队列设备的APQN不会被分配给KVM来宾的矩阵。然而，AP架构不提供从来宾矩阵中过滤个别APQN的方法，因此通过其sysfs“assign_adapter”，“assign_domain”和“assign_control_domain”接口分配给vfio_ap中介设备的适配器、域和控制域将在向来宾提供AP配置之前进行过滤：

* 将过滤掉那些分配给矩阵mdev但未同时分配给主机AP配置的适配器APID、域APQI以及控制域的域号
* 检查从分配给vfio_ap mdev的适配器APID和域APQI的笛卡尔积派生出的每个APQN，并且如果其中任何一个没有引用绑定到vfio_ap设备驱动程序的队列设备，则该适配器不会插入到来宾中（即，对应于其APID的来宾APCB中的APM中的位不会被设置）

AP的CPU模型特性
-----------------
AP堆栈依赖于AP指令的存在以及三个功能：AP设施测试（APFT）功能；AP查询配置信息（QCI）功能；以及AP队列中断控制功能。这些特性/功能通过以下CPU模型特性提供给KVM来宾：

1. ap：指示来宾是否安装了AP指令。此特性仅当主机上安装了AP指令时才会由KVM启用
2. apft：指示来宾可用APFT功能。此功能只能在主机上可用时（即，第15位设施位已设置）提供给来宾
3. apqci：指示来宾可用AP QCI功能。此功能只能在主机上可用时（即，第12位设施位已设置）提供给来宾
4. apqi：指示AP队列中断控制功能对来宾可用。此功能只能在主机上可用时（即，第65位设施位已设置）提供给来宾
注意：如果用户选择向QEMU指定不同于“host”的CPU模型，则需要显式启用CPU模型特性和功能；例如：

    `/usr/bin/qemu-system-s390x ... -cpu z13,ap=on,apqci=on,apft=on,apqi=on`

可以通过显式关闭它们来阻止来宾使用AP特性/功能；例如：

    `/usr/bin/qemu-system-s390x ... -cpu host,ap=off,apqci=off,apft=off,apqi=off`

注意：如果为来宾关闭APFT功能（apft=off），则来宾将看不到任何AP设备。在来宾上注册类型10及更新AP设备的zcrypt设备驱动程序（即，cex4card和cex4queue设备驱动程序）需要APFT功能来确定给定AP设备上安装的功能。如果来宾上未安装APFT功能，则由运行在来宾上的AP总线创建的任何适配器或域设备都不会得到创建，因为只有类型10及更新的设备可以配置供来宾使用。

示例
======
现在我们通过一个示例来说明如何使KVM来宾能够访问AP功能。在这个示例中，我们将展示如何配置三个来宾，以便在这些来宾上执行lszcrypt命令时会显示如下结果：

来宾1
------
=========== ===== ============
CARD.DOMAIN 类型  模式
=========== ===== ============
05          CEX5C CCA-Coproc
05.0004     CEX5C CCA-Coproc
05.00ab     CEX5C CCA-Coproc
06          CEX5A 加速器
06.0004     CEX5A 加速器
06.00ab     CEX5A 加速器
=========== ===== ============

来宾2
------
=========== ===== ============
CARD.DOMAIN 类型  模式
=========== ===== ============
05          CEX5C CCA-Coproc
05.0047     CEX5C CCA-Coproc
05.00ff     CEX5C CCA-Coproc
=========== ===== ============

来宾3
------
=========== ===== ============
CARD.DOMAIN 类型  模式
=========== ===== ============
06          CEX5A 加速器
06.0047     CEX5A 加速器
06.00ff     CEX5A 加速器
=========== ===== ============

以下是步骤：

1. 在Linux主机上安装vfio_ap模块。vfio_ap模块的依赖链为：
   * iommu
   * s390
   * zcrypt
   * vfio
   * vfio_mdev
   * vfio_mdev_device
   * KVM

   要构建vfio_ap模块，内核构建必须配置以下Kconfig元素：
   * IOMMU_SUPPORT
   * S390
   * AP
   * VFIO
   * KVM

   如果使用make menuconfig选择以下内容以构建vfio_ap模块：

     -> 设备驱动程序
	-> IOMMU硬件支持
	   select S390 AP IOMMU支持
	-> VFIO非特权用户空间驱动框架
	   -> 中介设备驱动框架
	      -> VFIO驱动程序用于中介设备
     -> I/O子系统
	-> VFIO支持AP设备

2. 安全地保护将由三个来宾使用的AP队列，以便主机无法访问它们。为了保护它们，有两个sysfs文件指定了标记APQN范围子集的掩码，这些子集仅可供默认AP队列设备驱动程序使用。所有其他剩余的APQNs都可用于任何其他设备驱动程序。目前，vfio_ap设备驱动程序是唯一的非默认设备驱动程序。包含这些掩码的sysfs文件的位置为：

     `/sys/bus/ap/apmask`
     `/sys/bus/ap/aqmask`

   `apmask`是一个256位掩码，标识一组AP适配器ID（APID）。从左到右，掩码中的每一位对应于0-255之间的APID。如果设置了某一位，则APID属于标记为仅可供默认AP队列设备驱动程序使用的APQN子集的一部分。
`aqmask`是一个256位的掩码，用于标识一组AP队列索引（APQI）。掩码中的每一位，从左至右，对应于0-255范围内的一个APQI。如果某一位被设置，则该APQI属于标记为仅对默认AP队列设备驱动程序可用的子集。

APID对应位设置的笛卡尔积和APQI对应位设置的笛卡尔积构成了仅能被主机默认设备驱动程序使用的AP队列编号（APQN）的子集。所有其他APQN可供非默认设备驱动程序（例如vfio_ap驱动程序）使用。

以以下掩码为例：

      apmask:
      0x7d00000000000000000000000000000000000000000000000000000000000000

      aqmask:
      0x8000000000000000000000000000000000000000000000000000000000000000

这些掩码表示：

   * 适配器1、2、3、4、5和7可用于主机默认设备驱动程序。
* 域0可用于主机默认设备驱动程序。

   * 仅对默认主机设备驱动程序可用的APQN子集包括：

     (1,0), (2,0), (3,0), (4,0), (5,0) 和 (7,0)

   * 所有其他APQN均可供非默认设备驱动程序使用。
分配给Linux主机的每个AP队列设备的APQN将由AP总线根据默认AP队列设备驱动程序可用的APID和APQI所构成的笛卡尔积进行检查。如果检测到匹配项，则只会探测默认AP队列设备驱动程序；否则，会探测vfio_ap设备驱动程序。

默认情况下，两个掩码设置为保留所有APQN供默认AP队列设备驱动程序使用。有两种方式可以更改默认掩码：

   1. 可以通过向sysfs掩码文件写入字符串来编辑sysfs掩码文件，格式有两种：

      * 绝对十六进制字符串开头为0x（例如"0x12345678"），用以设置掩码。如果提供的字符串比掩码短，则在右侧填充0；例如，指定掩码值为0x41相当于指定：

	   0x4100000000000000000000000000000000000000000000000000000000000000

	请注意掩码是从左至右读取的，因此上述掩码标识了设备号1和7（01000001）。
如果字符串比掩码长，则操作将以错误（EINVAL）终止。
* 掩码中个别的位可以通过指定要切换的位号列表进行打开或关闭。每个位号字符串前必须加上加号（+）或减号（-）以指示相应的位是要打开（+）还是关闭（-）。一些有效值是：

	   - "+0"    打开第0位
	   - "-13"   关闭第13位
	   - "+0x41" 打开第65位
	   - "-0xff" 关闭第255位

	以下示例：

	      +0,-6,+0x47,-0xf0

	打开第0位和第71位（0x47）

	关闭第6位和第240位（0xf0）

	请注意未在列表中指定的位保持不变。
2. 还可以在启动时通过内核命令行参数更改掩码：

	 ap.apmask=0xffff ap.aqmask=0x40

	 这将创建如下掩码：

	    apmask:
	    0xffff000000000000000000000000000000000000000000000000000000000000

	    aqmask:
	    0x4000000000000000000000000000000000000000000000000000000000000000

	 结果形成两个池：

	    默认驱动程序池：适配器0-15，域1
	    备选驱动程序池：适配器16-255，域0、2-255

   **注意：**
   更改掩码使得一个或多个APQN从vfio_ap中介设备（见下文）中移除会导致错误（EBUSY）。一条消息会被记录到内核环形缓冲区中，可通过'dmesg'命令查看。输出会标识出标记为“正在使用”的每个APQN以及它所分配的vfio_ap中介设备；例如：

   用户空间不得重新分配已分配给62177883-f1bb-47f0-914d-32a22e3a8804的队列05.0054
   用户空间不得重新分配已分配给cef03c3c-903d-4ecc-9a83-40694cb8aee4的队列04.0054

为我们的示例保护APQN
-----------------------------------
为了确保AP队列05.0004、05.0047、05.00ab、05.00ff、06.0004、06.0047、06.00ab和06.00ff由vfio_ap设备驱动程序使用，可以通过以下任一命令将对应的APQN从默认掩码中移除：

      echo -5,-6 > /sys/bus/ap/apmask

      echo -4,-0x47,-0xab,-0xff > /sys/bus/ap/aqmask

   或者设置掩码如下：

      echo 0xf9ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff \
      > apmask

      echo 0xf7fffffffffffffffeffffffffffffffffffffffffeffffffffffffffffffffe \
      > aqmask

这将使AP队列05.0004、05.0047、05.00ab、05.00ff、06.0004、06.0047、06.00ab和06.00ff绑定到vfio_ap设备驱动程序。vfio_ap设备驱动程序的sysfs目录现在将包含指向绑定到它的AP队列设备的符号链接：

     /sys/bus/ap
     ... [drivers]
     ...... [vfio_ap]
     ......... [05.0004]
     ......... [05.0047]
     ......... [05.00ab]
     ......... [05.00ff]
     ......... [06.0004]
     ......... [06.0047]
     ......... [06.00ab]
     ......... [06.00ff]

请注意，只有类型10及更新版本的适配器（即CEX4及以后版本）可以绑定到vfio_ap设备驱动程序。这样做的原因是简化实现，避免因支持未来几年即将退役的老设备而使设计变得复杂，并且对于这类老设备而言，测试系统已经很少。
因此，管理员必须注意仅保护那些可以绑定到 vfio_ap 设备驱动程序的 AP 队列。特定 AP 队列设备的设备类型可以从其父卡的 sysfs 目录中读取。例如，要查看队列 05.0004 的硬件类型：

```
cat /sys/bus/ap/devices/card05/hwtype
```

为了能够绑定到 vfio_ap 设备驱动程序，hwtype 必须为 10 或更高（CEX4 或更新版本）。
3. 创建三个来宾所需的中介设备以配置 AP 矩阵，并为来宾使用 vfio_ap 驱动程序提供接口：

```
/sys/devices/vfio_ap/matrix/
--- [mdev_supported_types]
------ [vfio_ap-passthrough] （直接传递 vfio_ap 中介设备类型）
--------- create
--------- [devices]
```

为了创建三个来宾所需的中介设备：

```
uuidgen > create
uuidgen > create
uuidgen > create
```

或者

```
echo $uuid1 > create
echo $uuid2 > create
echo $uuid3 > create
```

这将在 [devices] 子目录中创建三个名为 UUID 的中介设备，这些 UUID 写入了 create 属性文件。我们将它们称为 $uuid1、$uuid2 和 $uuid3，创建后 sysfs 目录结构如下：

```
/sys/devices/vfio_ap/matrix/
--- [mdev_supported_types]
------ [vfio_ap-passthrough]
--------- [devices]
------------ [$uuid1]
-------------- assign_adapter
-------------- assign_control_domain
-------------- assign_domain
-------------- matrix
-------------- unassign_adapter
-------------- unassign_control_domain
-------------- unassign_domain

------------ [$uuid2]
-------------- assign_adapter
-------------- assign_control_domain
-------------- assign_domain
-------------- matrix
-------------- unassign_adapter
-------------- unassign_control_domain
-------------- unassign_domain

------------ [$uuid3]
-------------- assign_adapter
-------------- assign_control_domain
-------------- assign_domain
-------------- matrix
-------------- unassign_adapter
-------------- unassign_control_domain
-------------- unassign_domain
```

**注：**除非使用 mdevctl 工具来创建并持久化 vfio_ap 中介设备，否则这些设备不会在重启后保留。
4. 现在，管理员需要为中介设备 $uuid1（对应于 Guest1）、$uuid2（对应于 Guest2）和 $uuid3（对应于 Guest3）配置矩阵。
这是 Guest1 的矩阵配置方式：

```
echo 5 > assign_adapter
echo 6 > assign_adapter
echo 4 > assign_domain
echo 0xab > assign_domain
```

同样可以使用 assign_control_domain sysfs 文件来分配控制域。
如果配置适配器、域或控制域时出现错误，可以使用 unassign_xxx 文件来取消分配适配器、域或控制域。
为了显示 Guest1 的矩阵配置：

```
cat matrix
```

为了显示将被分配给 Guest1 的矩阵：

```
cat guest_matrix
```

这是 Guest2 的矩阵配置方式：

```
echo 5 > assign_adapter
echo 0x47 > assign_domain
echo 0xff > assign_domain
```

这是 Guest3 的矩阵配置方式：

```
echo 6 > assign_adapter
echo 0x47 > assign_domain
echo 0xff > assign_domain
```

为了成功分配一个适配器：

* 指定的适配器编号必须表示从 0 到系统配置的最大适配器编号之间的值。如果指定的适配器编号高于最大值，则操作将以错误（ENODEV）终止。
**注：**可以通过 sysfs /sys/bus/ap/ap_max_adapter_id 属性文件获取最大适配器编号。
* 每个 APQN 来自所分配适配器的 APID 与先前分配的域的 APQIs 的笛卡尔乘积：
    - 必须仅对 vfio_ap 设备驱动程序可用，如 sysfs /sys/bus/ap/apmask 和 /sys/bus/ap/aqmask 属性文件中所指定。如果有任何一个 APQN 被主机设备驱动程序预留，则操作将以错误（EADDRNOTAVAIL）终止。
    - 不得已分配给另一个 vfio_ap 中介设备。如果有任何一个 APQN 已分配给另一个 vfio_ap 中介设备，则操作将以错误（EBUSY）终止。
    - 在编辑 sysfs /sys/bus/ap/apmask 和 sys/bus/ap/aqmask 属性文件期间不得分配，否则操作可能以错误（EBUSY）终止。
为了成功分配一个域：

   * 指定的域编号必须表示从 0 到系统配置的最大域编号之间的值。如果指定的域编号大于最大值，操作将以错误（ENODEV）终止。
注意：可以通过 sysfs 的 `/sys/bus/ap/ap_max_domain_id` 属性文件获取最大域编号。
* 通过被分配域的 APQI 和之前分配的适配器的 APID 的笛卡尔积得出的每个 APQN：

     - 只能为 vfio_ap 设备驱动程序所用，如 sysfs 的 `/sys/bus/ap/apmask` 和 `/sys/bus/ap/aqmask` 属性文件中所指定。如果有任何一个 APQN 被主机设备驱动程序预留，则操作将以错误（EADDRNOTAVAIL）终止。
- 不得分配给另一个由 vfio_ap 中介的设备。如果有任何一个 APQN 已经分配给了另一个由 vfio_ap 中介的设备，则操作将以错误（EBUSY）终止。
- 在编辑 sysfs 的 `/sys/bus/ap/apmask` 和 `/sys/bus/ap/aqmask` 属性文件时不得进行分配，否则操作可能会以错误（EBUSY）终止。

为了成功分配一个控制域：

   * 指定的域编号必须表示从 0 到系统配置的最大域编号之间的值。如果指定的控制域编号大于最大值，操作将以错误（ENODEV）终止。

5. 启动 Guest1:: 

     `/usr/bin/qemu-system-s390x` ... `-cpu host,ap=on,apqci=on,apft=on,apqi=on` \
	 `-device vfio-ap,sysfsdev=/sys/devices/vfio_ap/matrix/$uuid1` ...
   
6. 启动 Guest2:: 

     `/usr/bin/qemu-system-s390x` ... `-cpu host,ap=on,apqci=on,apft=on,apqi=on` \
	 `-device vfio-ap,sysfsdev=/sys/devices/vfio_ap/matrix/$uuid2` ...

7. 启动 Guest3:: 

     `/usr/bin/qemu-system-s390x` ... `-cpu host,ap=on,apqci=on,apft=on,apqi=on` \
	 `-device vfio-ap,sysfsdev=/sys/devices/vfio_ap/matrix/$uuid3` ...

当虚拟机关闭时，可以移除 vfio_ap 中介的设备。
使用我们的示例，要移除中介设备 $uuid1（通过 vfio_ap）：

```
/sys/devices/vfio_ap/matrix/
   --- [mdev_supported_types]
   ------ [vfio_ap-passthrough]
   --------- [devices]
   ------------ [$uuid1]
   --------------- remove
```

```
echo 1 > remove
```

这将移除矩阵 mdev 设备的所有 sysfs 结构，包括 mdev 设备本身。为了重新创建和重新配置矩阵 mdev 设备，必须再次执行从步骤 3 开始的所有步骤。注意，如果仍在运行使用 vfio_ap mdev 的客户机，则移除操作会失败。
不需要移除 vfio_ap mdev，但如果在 Linux 主机的剩余生命周期中没有客户机会使用它，则可能想要移除它。如果移除了 vfio_ap mdev，可能还需要重新配置为默认驱动程序预留的适配器和队列池。
热插拔支持：
=============
可以通过将适配器、域或控制域分配给客户机正在使用的 vfio_ap 中介设备来实现在运行中的 KVM 客户机中进行热插拔，前提是满足以下条件：

* 适配器、域或控制域也必须分配给主机的 AP 配置
* 每个从由被分配的适配器的 APID 和被分配的域的 APQIs 组成的笛卡尔积得出的 APQN 必须引用绑定到 vfio_ap 设备驱动程序的队列设备
* 要热插拔一个域，每个从由被分配的域的 APQI 和被分配的适配器的 APIDs 组成的笛卡尔积得出的 APQN 必须引用绑定到 vfio_ap 设备驱动程序的队列设备
可以通过从 vfio_ap 中介设备取消分配适配器、域或控制域来实现从运行中的 KVM 客户机的热拔除。
为 KVM 客户机超额预分配 AP 队列：
======================================
超额预分配在此定义为向不引用主机的 AP 配置中的 AP 设备的 vfio_ap 中介设备分配适配器或域。这里的理念是当适配器或域变得可用时，它将自动地通过使用其分配的 vfio_ap 中介设备热插拔进入 KVM 客户机，只要插入它后产生的每个新的 APQN 都引用了绑定到 vfio_ap 设备驱动程序的队列设备。
限制：
======
对于使用 AP 设备的客户机，不支持无系统管理员干预下的在线迁移。在 KVM 客户机可以迁移之前，必须移除 vfio_ap 中介设备。不幸的是，在中介设备正被 KVM 客户机使用时无法手动移除它（即 `echo 1 > /sys/devices/vfio_ap/matrix/$UUID/remove`）。如果客户机是由 QEMU 模拟的，可以通过两种方式之一将其 mdev 热拔除：

1. 如果 KVM 客户机是用 libvirt 启动的，你可以通过以下命令热拔除 mdev：

   ```
   virsh detach-device <guestname> <path-to-device-xml>
   ```

   例如，要从名为 'my-guest' 的客户机热拔除 mdev 62177883-f1bb-47f0-914d-32a22e3a8804：

   ```
   virsh detach-device my-guest ~/config/my-guest-hostdev.xml
   ```

   `my-guest-hostdev.xml` 文件内容如下：

   ```xml
   <hostdev mode='subsystem' type='mdev' managed='no' model='vfio-ap'>
     <source>
       <address uuid='62177883-f1bb-47f0-914d-32a22e3a8804'/>
     </source>
   </hostdev>
   ```

   或者使用以下命令：

   ```
   virsh qemu-monitor-command <guest-name> --hmp "device-del <device-id>"
   ```

   例如，要从名为 'my-guest' 的客户机热拔除标识符为 'id=hostdev0' 的 vfio_ap 中介设备：

   ```
   virsh qemu-monitor-command my-guest --hmp "device_del hostdev0"
   ```

2. 可以通过附加 qemu 监视器到客户机并使用以下 qemu 监视器命令来热拔除 vfio_ap 中介设备：

   ```
   (QEMU) device-del id=<device-id>
   ```

   例如，要热拔除启动时通过 'id=hostdev0' 指定的 vfio_ap 中介设备：

   ```
   (QEMU) device-del id=hostdev0
   ```

完成 KVM 客户机的在线迁移后，可以通过以下两种方式之一将 AP 配置恢复到目标系统上的 KVM 客户机：

1. 如果 KVM 客户机是用 libvirt 启动的，你可以通过以下 virsh 命令热插拔矩阵中介设备：

   ```
   virsh attach-device <guestname> <path-to-device-xml>
   ```

   例如，要将 mdev 62177883-f1bb-47f0-914d-32a22e3a8804 热插拔到名为 'my-guest' 的客户机：

   ```
   virsh attach-device my-guest ~/config/my-guest-hostdev.xml
   ```

   `my-guest-hostdev.xml` 文件内容如下：

   ```xml
   <hostdev mode='subsystem' type='mdev' managed='no' model='vfio-ap'>
     <source>
       <address uuid='62177883-f1bb-47f0-914d-32a22e3a8804'/>
     </source>
   </hostdev>
   ```

   或者使用以下命令：

   ```
   virsh qemu-monitor-command <guest-name> --hmp "device_add vfio-ap,sysfsdev=<path-to-mdev>,id=<device-id>"
   ```

   例如，要将标识符为 62177883-f1bb-47f0-914d-32a22e3a8804 的 vfio_ap 中介设备热插拔到名为 'my-guest' 的客户机，并设置设备标识符为 hostdev0：

   ```
   virsh qemu-monitor-command my-guest --hmp "device_add vfio-ap,sysfsdev=/sys/devices/vfio_ap/matrix/62177883-f1bb-47f0-914d-32a22e3a8804,id=hostdev0"
   ```

2. 可以通过附加 qemu 监视器到客户机并使用以下 qemu 监视器命令来热插拔 vfio_ap 中介设备：

   ```
   (qemu) device_add "vfio-ap,sysfsdev=<path-to-mdev>,id=<device-id>"
   ```

   例如，要将标识符为 62177883-f1bb-47f0-914d-32a22e3a8804 的 vfio_ap 中介设备热插拔到客户机，并设置设备标识符为 hostdev0：

   ```
   (QEMU) device-add "vfio-ap,sysfsdev=/sys/devices/vfio_ap/matrix/62177883-f1bb-47f0-914d-32a22e3a8804,id=hostdev0"
   ```
