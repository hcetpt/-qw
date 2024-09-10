=============================
NFSv4.1 服务器实现
=============================

对小版本 1 的服务器支持可以通过 `/proc/fs/nfsd/versions` 控制文件进行控制。读取此文件返回的字符串输出将包含 "+4.1" 或 "-4.1"，相应地表示启用或禁用。

目前，默认情况下已启用了对小版本 1 的服务器支持。可以在运行时通过向 `/proc/fs/nfsd/versions` 控制文件写入字符串 "-4.1" 来禁用它。需要注意的是，为了写入此控制文件，必须先停止 nfsd 服务。你可以使用 `rpc.nfsd` 命令来完成这一操作；详见 `rpc.nfsd(8)` 手册页。
（警告：较旧的服务器会将 "+4.1" 和 "-4.1" 分别解释为 "+4" 和 "-4"。因此，旨在同时适用于新旧内核的代码必须在开启或关闭版本 4 支持之前先开启或关闭 4.1 版本支持；`rpc.nfsd` 命令正确地实现了这一点。）

nfsd 中的 NFSv4 小版本 1（NFSv4.1）实现基于 RFC 5661。

从 NFSv4.1 的众多新功能中，当前实现主要关注于必须实现的 NFSv4.1 会话功能，提供“恰好一次”的语义以及更好地控制和调整每个客户端分配的资源。

下表摘自 NFSv4.1 文档，列出了小版本 1 中必须实现（REQ）、可选（OPT）以及必须不实现的 NFSv4.0 操作（MNI）。第一列表示当前 Linux 服务器实现中尚未支持的操作。

可选特性及其缩写如下：

- **pNFS** 并行 NFS
- **FDELG** 文件委托
- **DDELG** 目录委托

以下缩写表示 Linux 服务器实现的状态：
- **I** 已实现的 NFSv4.1 操作
- **NS** 不支持
- **NS\*** 未实现的可选功能
### 操作
==========

| 实现状态 | 操作       | REQ, REC, OPT 或 NMI | 特性 (REQ, REC 或 OPT) | 定义         |
|:-----------------------:|:----------------------:|:---------------------:|:---------------------------:|:----------------:|
|                        | ACCESS                 | REQ                  |                            | 第 18.1 节 |
| I                      | BACKCHANNEL_CTL        | REQ                  |                            | 第 18.33 节 |
| I                      | BIND_CONN_TO_SESSION   | REQ                  |                            | 第 18.34 节 |
|                        | CLOSE                  | REQ                  |                            | 第 18.2 节 |
|                        | COMMIT                 | REQ                  |                            | 第 18.3 节 |
|                        | CREATE                 | REQ                  |                            | 第 18.4 节 |
| I                      | CREATE_SESSION         | REQ                  |                            | 第 18.36 节 |
| NS*                    | DELEGPURGE             | OPT                  | FDELG (REQ)                | 第 18.5 节 |
|                        | DELEGRETURN            | OPT                  | FDELG, DDELG, pNFS (REQ)   | 第 18.6 节 |
| I                      | DESTROY_CLIENTID       | REQ                  |                            | 第 18.50 节 |
| I                      | DESTROY_SESSION        | REQ                  |                            | 第 18.37 节 |
| I                      | EXCHANGE_ID            | REQ                  |                            | 第 18.35 节 |
| I                      | FREE_STATEID           | REQ                  |                            | 第 18.38 节 |
|                        | GETATTR                | REQ                  |                            | 第 18.7 节 |
| I                      | GETDEVICEINFO          | OPT                  | pNFS (REQ)                 | 第 18.40 节 |
| NS*                    | GETDEVICELIST          | OPT                  | pNFS (OPT)                 | 第 18.41 节 |
|                        | GETFH                  | REQ                  |                            | 第 18.8 节 |
| NS*                    | GET_DIR_DELEGATION     | OPT                  | DDELG (REQ)                | 第 18.39 节 |
| I                      | LAYOUTCOMMIT           | OPT                  | pNFS (REQ)                 | 第 18.42 节 |
| I                      | LAYOUTGET              | OPT                  | pNFS (REQ)                 | 第 18.43 节 |
| I                      | LAYOUTRETURN           | OPT                  | pNFS (REQ)                 | 第 18.44 节 |
|                        | LINK                   | OPT                  |                            | 第 18.9 节 |
|                        | LOCK                   | REQ                  |                            | 第 18.10 节 |
|                        | LOCKT                  | REQ                  |                            | 第 18.11 节 |
|                        | LOCKU                  | REQ                  |                            | 第 18.12 节 |
|                        | LOOKUP                 | REQ                  |                            | 第 18.13 节 |
|                        | LOOKUPP                | REQ                  |                            | 第 18.14 节 |
|                        | NVERIFY                | REQ                  |                            | 第 18.15 节 |
|                        | OPEN                   | REQ                  |                            | 第 18.16 节 |
| NS*                    | OPENATTR               | OPT                  |                            | 第 18.17 节 |
|                        | OPEN_CONFIRM           | MNI                  |                            | 无             |
|                        | OPEN_DOWNGRADE         | REQ                  |                            | 第 18.18 节 |
|                        | PUTFH                  | REQ                  |                            | 第 18.19 节 |
|                        | PUTPUBFH               | REQ                  |                            | 第 18.20 节 |
|                        | PUTROOTFH              | REQ                  |                            | 第 18.21 节 |
|                        | READ                   | REQ                  |                            | 第 18.22 节 |
|                        | READDIR                | REQ                  |                            | 第 18.23 节 |
|                        | READLINK               | OPT                  |                            | 第 18.24 节 |
|                        | RECLAIM_COMPLETE       | REQ                  |                            | 第 18.51 节 |
|                        | RELEASE_LOCKOWNER      | MNI                  |                            | 无             |
|                        | REMOVE                 | REQ                  |                            | 第 18.25 节 |
|                        | RENAME                 | REQ                  |                            | 第 18.26 节 |
|                        | RENEW                  | MNI                  |                            | 无             |
|                        | RESTOREFH              | REQ                  |                            | 第 18.27 节 |
|                        | SAVEFH                 | REQ                  |                            | 第 18.28 节 |
|                        | SECINFO                | REQ                  |                            | 第 18.29 节 |
| I                      | SECINFO_NO_NAME        | REC                  | pNFS 文件布局 (REQ)       | 第 18.45 节，第 13.12 节 |
| I                      | SEQUENCE               | REQ                  |                            | 第 18.46 节 |
|                        | SETATTR                | REQ                  |                            | 第 18.30 节 |
|                        | SETCLIENTID            | MNI                  |                            | 无             |
|                        | SETCLIENTID_CONFIRM    | MNI                  |                            | 无             |
| NS                     | SET_SSV                | REQ                  |                            | 第 18.47 节 |
| I                      | TEST_STATEID           | REQ                  |                            | 第 18.48 节 |
|                        | VERIFY                 | REQ                  |                            | 第 18.31 节 |
| NS*                    | WANT_DELEGATION        | OPT                  | FDELG (OPT)                | 第 18.49 节 |
|                        | WRITE                  | REQ                  |                            | 第 18.32 节 |

### 回调操作
===================

| 实现状态 | 操作               | REQ, REC, OPT 或 NMI | 特性 (REQ, REC 或 OPT) | 定义         |
|:-----------------------:|:-------------------------:|:---------------------:|:---------------------------:|:---------------:|
|                        | CB_GETATTR               | OPT                  | FDELG (REQ)                | 第 20.1 节 |
| I                      | CB_LAYOUTRECALL          | OPT                  | pNFS (REQ)                 | 第 20.3 节 |
| NS*                    | CB_NOTIFY                | OPT                  | DDELG (REQ)                | 第 20.4 节 |
| NS*                    | CB_NOTIFY_DEVICEID       | OPT                  | pNFS (OPT)                 | 第 20.12 节 |
| NS*                    | CB_NOTIFY_LOCK           | OPT                  |                            | 第 20.11 节 |
| NS*                    | CB_PUSH_DELEG            | OPT                  | FDELG (OPT)                | 第 20.5 节 |
|                        | CB_RECALL                | OPT                  | FDELG, DDELG, pNFS (REQ)   | 第 20.2 节 |
| NS*                    | CB_RECALL_ANY            | OPT                  | FDELG, DDELG, pNFS (REQ)   | 第 20.6 节 |
| NS                     | CB_RECALL_SLOT           | REQ                  |                            | 第 20.8 节 |
| NS*                    | CB_RECALLABLE_OBJ_AVAIL  | OPT                  | DDELG, pNFS (REQ)          | 第 20.7 节 |
| I                      | CB_SEQUENCE              | OPT                  | FDELG, DDELG, pNFS (REQ)   | 第 20.9 节 |
| NS*                    | CB_WANTS_CANCELLED       | OPT                  | FDELG, DDELG, pNFS (REQ)   | 第 20.10 节 |

### 实现说明
=====================

**SSV:**
  规范声称这是强制性的，但实际上我们不知道有任何实现，因此目前忽略它。服务器在 EXCHANGE_ID 中返回 NFS4ERR_ENCR_ALG_UNSUPP，这应该是未来兼容的。

**GSS 在后通道中:**
  理论上是必需的，但并未广泛实现（特别是当前的 Linux 客户端不请求它）。我们在 CREATE_SESSION 中返回 NFS4ERR_ENCR_ALG_UNSUPP。

**DELEGPURGE:**
  只对支持 CLAIM_DELEGATE_PREV 和/或 CLAIM_DELEG_PREV_FH 的服务器强制性（允许客户端在重启后保留委托）。因此我们现在不需要实现它。

**EXCHANGE_ID:**
  实现 ID 被忽略。

**CREATE_SESSION:**
  后通道属性被忽略。

**SEQUENCE:**
  不支持动态槽表重新协商（可选）。

**非标准复合限制:**
  不支持需要同时包含 ca_maxrequestsize 请求和 ca_maxresponsesize 响应的会话前通道 RPC 复合操作，因此我们可能无法兑现我们在 CREATE_SESSION 前通道协商中所做的承诺。
详见：http://wiki.linux-nfs.org/wiki/index.php/Server_4.0_and_4.1_issues
