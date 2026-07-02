-- WX6: 编码与字符清洗
-- practice_id=5, order_in_practice=6, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$编码与字符清洗$v$,
        'PRACTICE',
        6,
        $v$intermediate$v$,
        $v$## 字符编码的世界

## 1.1 ASCII 与扩展

最基础的字符编码 ASCII (American Standard Code) 用 7 bit 表示 128 个字符:
- 0-31: 控制字符 (TAB / NEWLINE / 回车 / BEL 等)
- 32-126: 可打印字符 (字母 / 数字 / 标点)
- 127: DEL

ASCII 之外, 各国/各行业扩展出多种编码: GB2312, GBK, GB18030, BIG5, Shift-JIS, Latin-1。

## 1.2 Unicode 与 UTF-8

Unicode 用一个码位空间统一表示全球字符 (10 万+ 字符)。**UTF-8** 是 Unicode 的字节级编码, 兼容 ASCII (0-127 字节相同), 中文等字符用 3 字节。

工程实务: 现代系统 99% 用 UTF-8 (Web 标准, JSON 标准, Python 3 默认)。GBK 等只在某些 Windows 历史文件出现。

## 1.3 BOM (Byte Order Mark)

UTF-8 BOM 是文件开头的 3 字节 (`﻿` Unicode 码位, EF BB BF 字节序列), 用来"标识这是 UTF-8"。

问题: BOM 在 JSON / CSV / 命令行输出时常常被误解析:
- JSON.parse(content) 会因为 BOM 失败 (BOM 不是合法 JSON 起始)
- CSV 第一行第一字段会多 3 字节
- 命令行 echo 文件会显示乱码

工程实务: 读文件后**第一件事**判断并去掉 BOM, 写文件**不要写** BOM。


## 控制字符与非 ASCII

## 2.1 控制字符的来源

ASCII 0-31 是控制字符, 历史上控制电传打字机, 现代意义不大。常见出现:
- **\\b (8)**: backspace, 用户输错时按
- **\\v (11)**: 垂直制表, 已废弃
- **\\x00 (0)**: NUL, 字符串结束符 (C 语言)
- **\\x07 (7)**: BEL, 蜂鸣
- **TAB (9), LF (10)**: 这两个是**有用的** (制表 / 换行), 通常保留

工程实务: 文本字段中混入控制字符是**极常见的脏数据**, 来源:
- 客户端复制粘贴 (Word 文档常含 vert tab)
- 传输错误 (UTF-8 解码失败留下 \\x00)
- 开发者调试代码遗留 (\\b, \\a)

清洗策略: 删除所有 ord < 32 的字符, 但保留 TAB (9) 和 LF (10)。

## 2.2 非 ASCII 字符的检测

非 ASCII = 字符的 ord > 127。包括:
- 中文: 4E00-9FFF (大部分)
- 日文: 3040-309F (Hiragana), 30A0-30FF (Katakana)
- 韩文: AC00-D7AF
- 各种符号: 全角, emoji 等

检测策略: 遍历每个字符 c, 统计 `ord(c) > 127` 的数量。

工程实务:
- 期望 ASCII 字段 (用户名 / ID / URL): 非 ASCII 全部要 reject 或转换 (拼音化)
- 文本字段 (姓名 / 描述): 非 ASCII 是正常的
- **不要 strict 全 ASCII**: 否则中文用户无法注册

## 2.3 全角与半角

中文输入法默认全角空格, 字符宽度是英文的两倍:
- "ＡＢＣ" (全角) vs "ABC" (半角)
- "，。" (全角标点) vs ",." (半角)

存储时混用全/半角会导致字符串比较失败。规范化: 全角 ASCII 范围 (FF01-FF5E) 转回半角 (减 0xFEE0 = 65248)。

本关只做"检测全 ASCII", 不做转换 (转换是更大主题)。


## BOM 检测与业务案例

## 3.1 BOM 检测

`text[0] == '\\ufeff'` 即可。Python 的 file.read() 默认不去掉 BOM, 需要手动检测+删除。

## 3.2 业务案例: 跨平台 CSV 数据清洗

场景: 公司从合作方接收 CSV 文件, 来源多样:
- Windows Excel 导出: GBK 编码 + UTF-8 BOM
- Mac Numbers 导出: UTF-8 无 BOM
- Linux 命令行生成: UTF-8 无 BOM
- 老旧系统: Shift-JIS / Latin-1

接收方流水线:
1. **判断编码**: chardet 库或 BOM 检测 (本关 BOM 部分)
2. **去 BOM** (本关检测): 第 1 字符 `\\ufeff` → 跳过
3. **去控制字符** (本关): 删除 ord < 32 (除 TAB/LF), 防止数据库导入失败
4. **检测非 ASCII** (本关): 统计中文/日韩字符比例
5. **格式归一化** (复习 WX05): 字段格式统一
6. **入库**

工程数字: 1 万 CSV 文件中, 约 30% 含 BOM, 5% 含控制字符, 2% 编码错误需要回退。

## 3.3 工程口诀

- **读文件先判 BOM**: 否则 JSON / CSV 解析失败
- **写文件不写 BOM**: UTF-8 不需要, 反而出错
- **控制字符全删, 除了 TAB 和 LF**: 保留可见空白
- **非 ASCII 检测看场景**: 用户名严, 文本字段松
- **现代用 UTF-8, 历史用 GBK / Shift-JIS**: 接收任何编码先转 UTF-8

## 3.4 编码错误的诊断

常见症状:
- 中文显示成 "ä¸­æ–‡" → UTF-8 字节被当 Latin-1 解析
- 中文显示成 "????" → 编码无法表示该字符 (如 ASCII)
- 字段被截断 → 多字节字符在边界被截

诊断: 用十六进制查看原始字节, 对照编码表反推。本关不实现诊断, 是更高级专题。

$v$,
        $v${"questions": [{"id": "q06-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx06.py 中的 4 个函数; 评测以 test_wx06.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_cna_one_in_4$v$, $v$cna one in 4$v$, false, $v$cna one in 4$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_cna_two_in_5$v$, $v$cna two in 5$v$, false, $v$cna two in 5$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_cna_one_in_5$v$, $v$cna one in 5$v$, false, $v$cna one in 5$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_cna_four_in_6$v$, $v$cna four in 6$v$, false, $v$cna four in 6$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_cna_two_emojis$v$, $v$cna two emojis$v$, false, $v$cna two emojis$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_cna_raises_on_non_string$v$, $v$cna raises on non string$v$, false, $v$cna raises on non string$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_rcc_remove_bell$v$, $v$rcc remove bell$v$, false, $v$rcc remove bell$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_rcc_remove_null$v$, $v$rcc remove null$v$, false, $v$rcc remove null$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_rcc_remove_vt$v$, $v$rcc remove vt$v$, false, $v$rcc remove vt$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_rcc_mixed_keep_remove$v$, $v$TAB+LF 保留, BEL 去掉$v$, false, $v$TAB+LF 保留, BEL 去掉$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_rcc_keep_only_visible$v$, $v$rcc keep only visible$v$, false, $v$rcc keep only visible$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_rcc_raises_on_non_string$v$, $v$rcc raises on non string$v$, true, $v$rcc raises on non string$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_ipa_only_chinese$v$, $v$ipa only chinese$v$, true, $v$ipa only chinese$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_ipa_japanese$v$, $v$ipa japanese$v$, true, $v$ipa japanese$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_ipa_emoji_only$v$, $v$ipa emoji only$v$, true, $v$ipa emoji only$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_ipa_korean$v$, $v$ipa korean$v$, true, $v$ipa korean$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_ipa_raises_on_non_string$v$, $v$ipa raises on non string$v$, true, $v$ipa raises on non string$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_bom_starts_with_bom$v$, $v$bom starts with bom$v$, true, $v$bom starts with bom$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_bom_in_middle$v$, $v$bom in middle$v$, true, $v$bom in middle$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_bom_at_end$v$, $v$bom at end$v$, true, $v$bom at end$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_bom_two_in_middle$v$, $v$bom two in middle$v$, true, $v$bom two in middle$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_bom_raises_on_non_string$v$, $v$bom raises on non string$v$, true, $v$bom raises on non string$v$, NULL, 22)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
