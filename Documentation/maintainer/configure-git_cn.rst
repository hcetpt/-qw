配置 Git
===============

本章描述了维护者级别的 Git 配置。
在拉取请求中使用的带标签的分支（参见
文档/maintainer/pull-requests.rst）应该使用开发者的公共 GPG 密钥进行签名。可以通过向 `git tag` 传递 `-u <key-id>` 来创建已签名的标签。但是，因为你通常会在项目中使用相同的密钥，你可以在配置中设置它，并使用 `-s` 标志。要设置默认的 `key-id` ，请使用：

```shell
git config user.signingkey "keyname"
```

或者手动编辑你的 `.git/config` 或 `~/.gitconfig` 文件：

```shell
[user]
    name = Jane Developer
    email = jd@domain.org
    signingkey = jd@domain.org
```

你可能需要告诉 `git` 使用 `gpg2` ：

```shell
[gpg]
    program = /path/to/gpg2
```

你也可以告诉 `gpg` 使用哪个 `tty` （添加到你的 shell rc 文件中）：

```shell
export GPG_TTY=$(tty)
```


创建指向 lore.kernel.org 的提交链接
----------------------------------------

网站 https://lore.kernel.org 是所有与内核开发相关或影响内核开发的邮件列表通信的大档案库。在此处存储补丁归档是一种推荐的做法，当维护者将补丁应用到子系统树时，提供一个指向 lore 归档的 Link: 标签是个好主意，这样浏览提交历史的人可以找到相关的讨论和某个变更背后的理由。
Link: 标签看起来像这样：

```shell
Link: https://lore.kernel.org/r/<message-id>
```

你可以通过将以下钩子添加到你的 Git 中来配置它，使其在每次发出 `git am` 命令时自动发生：

```shell
$ git config am.messageid true
$ cat >.git/hooks/applypatch-msg <<'EOF'
#!/bin/sh
. git-sh-setup
perl -pi -e 's|^Message-I[dD]:\s*<?([^>]+)>?$|Link: https://lore.kernel.org/r/$1|g;' "$1"
test -x "$GIT_DIR/hooks/commit-msg" &&
    exec "$GIT_DIR/hooks/commit-msg" ${1+"$@"}
:
EOF
$ chmod a+x .git/hooks/applypatch-msg
```
