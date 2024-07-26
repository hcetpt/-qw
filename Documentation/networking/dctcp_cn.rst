SPDX 许可证标识符: GPL-2.0

======================
DCTCP（数据中心传输控制协议）
======================

DCTCP 是对用于数据中心网络的TCP拥塞控制算法的一种增强，并利用数据中心网络中的显式拥塞通知（ECN）向终端主机提供多位反馈。要在终端主机上启用它，请执行以下命令：

  sysctl -w net.ipv4.tcp_congestion_control=dctcp
  sysctl -w net.ipv4.tcp_ecn_fallback=0 （可选）

运行DCTCP的所有数据中心网络中的交换机必须支持ECN标记，并且在达到定义的交换机缓冲区阈值时进行配置以执行标记。对于DCTCP，交换机上的默认ECN标记阈值启发式规则是在1Gbps下为20个数据包（30KB），在10Gbps下为65个数据包（约100KB），但可能需要进一步仔细调整。
更多细节，请参见以下文档：

论文：

该算法在以下两篇SIGCOMM/SIGMETRICS论文中进行了更详细的描述：

 i) Mohammad Alizadeh, Albert Greenberg, David A. Maltz, Jitendra Padhye,
    Parveen Patel, Balaji Prabhakar, Sudipta Sengupta, 和 Murari Sridharan:

      “数据中心传输控制协议（DCTCP）”，《数据中心网络会议》

      ACM SIGCOMM会议论文集, 新德里, 2010
http://simula.stanford.edu/~alizade/Site/DCTCP_files/dctcp-final.pdf
    http://www.sigcomm.org/ccr/papers/2010/October/1851275.1851192

ii) Mohammad Alizadeh, Adel Javanmard, 和 Balaji Prabhakar:

      “DCTCP分析：稳定性、收敛性和公平性”
      ACM SIGMETRICS会议论文集, 圣何塞, 2011
http://simula.stanford.edu/~alizade/Site/DCTCP_files/dctcp_analysis-full.pdf

IETF信息草案：

  http://tools.ietf.org/html/draft-bensley-tcpm-dctcp-00

DCTCP网站：

  http://simula.stanford.edu/~alizade/Site/DCTCP.html
