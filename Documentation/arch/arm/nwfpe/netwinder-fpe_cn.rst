===== 当前状态 =====

以下描述了NetWinder的浮点数模拟器的当前状态。
在以下内容中，使用了特定的术语来描述浮点数指令。这些术语遵循ARM手册中的约定：
::

  <S|D|E> = <单精度|双精度|扩展精度>，没有默认值
  {P|M|Z} = {向正无穷舍入, 向负无穷舍入, 向零舍入}，
            默认 = 向最接近的数值舍入

注意：括在{}中的项目是可选的。

浮点协处理器数据传输指令（CPDT）
--------------------------------------

LDF/STF - 加载和存储浮点数

<LDF|STF>{条件}<S|D|E> Fd, Rn  
<LDF|STF>{条件}<S|D|E> Fd, [Rn, #<表达式>]{!}  
<LDF|STF>{条件}<S|D|E> Fd, [Rn], #<表达式>  

这些指令已经完全实现。

LFM/SFM - 加载和存储多个浮点数

形式1语法：
<LFM|SFM>{条件}<S|D|E> Fd, <计数>, [Rn]  
<LFM|SFM>{条件}<S|D|E> Fd, <计数>, [Rn, #<表达式>]{!}  
<LFM|SFM>{条件}<S|D|E> Fd, <计数>, [Rn], #<表达式>  

形式2语法：
<LFM|SFM>{条件}<FD,EA> Fd, <计数>, [Rn]{!}  

这些指令已经完全实现。它们将三个字的数据从每个浮点寄存器加载/存储到指令指定的内存位置。内存中的格式可能与其他实现不兼容，特别是与实际硬件不同。ARM手册中对此有明确说明。

浮点协处理器寄存器传输指令（CPRT）
----------------------------------------

转换、读写状态/控制寄存器指令

FLT{条件}<S,D,E>{P,M,Z} Fn, Rd          将整数转换为浮点数  
FIX{条件}{P,M,Z} Rd, Fn                 将浮点数转换为整数  
WFS{条件} Rd                            写入浮点状态寄存器  
RFS{条件} Rd                            读取浮点状态寄存器  
WFC{条件} Rd                            写入浮点控制寄存器  
RFC{条件} Rd                            读取浮点控制寄存器  

FLT/FIX已经完全实现  
RFS/WFS已经完全实现  
RFC/WFC已经完全实现。RFC/WFC是仅限于监督模式的指令，并且目前会检查CPU模式，如果不是从监督模式调用，则触发非法指令陷阱。

比较指令

CMF{条件} Fn, Fm        浮点数比较  
CMFE{条件} Fn, Fm       带异常的浮点数比较  
CNF{条件} Fn, Fm        反转浮点数比较  
CNFE{条件} Fn, Fm       带异常的反转浮点数比较  

这些指令已经完全实现。

浮点协处理器数据指令（CPDT）
---------------------------------

二元操作：

ADF{条件}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#值> - 加法  
SUF{条件}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#值> - 减法  
RSF{条件}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#值> - 反向减法  
MUF{条件}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#值> - 乘法  
DVF{条件}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#值> - 除法  
RDV{条件}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#值> - 反向除法  

这些指令已经完全实现。
这些指令已完全实现：FML{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - 快速乘法
FDV{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - 快速除法
FRD{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - 快速逆向除法

它们使用与非快速版本相同的算法。因此，在本实现中，其性能等同于MUF/DVF/RDV指令。根据ARM手册，这是可以接受的。手册指出这些指令仅对单精度操作数定义，在实际的FPA11硬件上不支持双精度或扩展精度操作数。当前模拟器不检查请求的权限条件，并执行所请求的操作
RMF{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - IEEE取余

这已经完全实现。
单目运算：

MVF{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 移动
MNF{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 取反后移动

这些已经完全实现
ABS{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 绝对值
SQT{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 平方根
RND{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 四舍五入

这些已经完全实现
URD{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 非规范化四舍五入
NRM{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 规范化

这些已实现。URD使用与RND指令相同的代码实现。由于URD不能返回非规范化数字，NRM实际上成为空操作（NOP）。
库调用：

POW{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - 幂
RPW{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - 逆幂
POL{cond}<S|D|E>{P,M,Z} Fd, Fn, <Fm,#value> - 极角（反正切）

LOG{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 以10为底的对数
LGN{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 以e为底的对数
EXP{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 指数
SIN{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 正弦
COS{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 余弦
TAN{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 正切
ASN{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 反正弦
ACS{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 反余弦
ATN{cond}<S|D|E>{P,M,Z} Fd, <Fm,#value> - 反正切

这些未实现。目前编译器没有发出这些指令，而是通过libc中的例程处理。这些功能并非由FPA11硬件直接支持，而是由浮点支持代码处理。未来版本中应该实现这些功能。
信号处理：

信号已被实现。但是Rebel.com生成的当前ELF内核存在一个bug，阻止模块生成SIGFPE信号。这是由于未能正确将fp_current别名到内核变量current_set[0]造成的。
随此分发提供的内核（vmlinux-nwfpe-0.93）修复了此问题，并且直接集成了当前版本的模拟器。使用该内核时，无需加载任何浮点模块即可运行。它作为技术演示提供给那些依赖于信号进行浮点工作的用户。但严格来说，不一定需要使用模块。
可以加载一个模块（无论是Russell King提供的还是本分发中的模块），以替代内建在内核中的模拟器的功能。
