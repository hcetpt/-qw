```bash
# 小脚本，用于就地刷新内核特性支持状态

对于 Documentation/features/*/*/arch-support.txt 中的每个文件 F_FILE：
F=$(grep "^#         Kconfig:" "$F_FILE" | cut -c26-)

#
# 每个特性 F 由一个对 (O, K) 标识，其中 'O' 可以是空字符串（表示 'nop'）或 "not"（逻辑取反运算符 '!'）；其他运算符不支持
#
O=""
K=$F
如果 [[ "$F" 以 ! 开头 ]]; then
    O="not"
    K=$(echo $F | sed -e 's/^!//g')
fi

#
# 特性 F := (O, K) 是 '有效' 的当且仅当某个架构的 Kconfig 文件中包含 K
#
# 注意该定义导致了 'O = ""' 和 'O = "not"' 两种情况之间的 '不对称性'。例如，F 可能是无效的，如果：
#
# [情况 'O = ""']
#   1) 没有架构提供对 F 的支持，
#   2) K 不存在（例如，被重命名或拼写错误）；
#
# [情况 'O = "not"']
#   3) 所有架构都提供了对 F 的支持，
#   4) 如同 (2)
#
# 采用此定义（从而保持这种不对称性）的原因是：
#
#       我们希望能够 '检测' (2)（或 (4)）
#
# (1) 和 (3) 可能进一步警告开发人员 K 可以被移除
#
F_VALID="false"
对于每个 arch/*/ 目录 ARCH_DIR：
    K_FILES=$(find $ARCH_DIR -name "Kconfig*")
    K_GREP=$(grep "$K" $K_FILES)
    如果 [ ! -z "$K_GREP" ]; then
        F_VALID="true"
        break
    fi
done
如果 [ "$F_VALID" = "false" ]; then
    printf "WARNING: '%s' is not a valid Kconfig\n" "$F"
fi

T_FILE="$F_FILE.tmp"
grep "^#" $F_FILE > $T_FILE
echo "    -----------------------" >> $T_FILE
echo "    |         arch |status|" >> $T_FILE
echo "    -----------------------" >> $T_FILE
对于每个 arch/*/ 目录 ARCH_DIR：
    ARCH=$(echo $ARCH_DIR | sed -e 's/^arch//g' | sed -e 's/\///g')
    K_FILES=$(find $ARCH_DIR -name "Kconfig*")
    K_GREP=$(grep "$K" $K_FILES)
    #
    # 根据以下规则更新 (O, K) 的架构支持状态值
    #
    #   - ("", K) 被 '给定架构支持'，如果该架构的 Kconfig 文件包含 K；
    #
    #   - ("not", K) 被 '给定架构支持'，如果该架构的 Kconfig 文件不包含 K；
    #
    #   - 否则：保留先前的状态值（如果有），默认为 '尚未支持'
    #
    # 注意根据这些规则，无效特性可能会被更新/修改
    #
    如果 [ "$O" = "" ] 并且 [ ! -z "$K_GREP" ]; then
        printf "    |%12s: |  ok  |\n" "$ARCH" >> $T_FILE
    elif [ "$O" = "not" ] 并且 [ -z "$K_GREP" ]; then
        printf "    |%12s: |  ok  |\n" "$ARCH" >> $T_FILE
    else
        S=$(grep -v "^#" "$F_FILE" | grep " $ARCH:")
        如果 [ ! -z "$S" ]; then
            echo "$S" >> $T_FILE
        else
            printf "    |%12s: | TODO |\n" "$ARCH" >> $T_FILE
        fi
    fi
done
echo "    -----------------------" >> $T_FILE
mv $T_FILE $F_FILE
done
```

这个脚本用于检查并更新内核特性支持状态，并记录哪些特性在不同架构中是否被支持。
