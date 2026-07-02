#!/usr/bin/env python3
"""批量生成 WX02-WX12 的 SQL 插入脚本"""
import json, sys, os

os.chdir('/Users/jimfu/Work/huixue')
sys.path.insert(0, '/Users/jimfu/Work/huixue')

import yaml

QUESTIONS = {
    'wx02': [
        {"id": "q2-1", "type": "concept", "difficulty": "easy",
         "question": "在 pandas 中,哪种填充方法最适合有明显时间趋势的数据?",
         "hint": "考虑趋势性和连续性。",
         "options": ["A. 均值填充", "B. 中位数填充", "C. 前向填充(ffill)", "D. 固定值填充"],
         "answer": "C",
         "explanation": "前向填充(ffill)用前一个有效值填充缺失值,保持了时间序列的连续性,最适合有时间趋势的数据。"},
        {"id": "q2-2", "type": "concept", "difficulty": "easy",
         "question": "某字段缺失率超过多少时,业界通常建议删除该列而非填充?",
         "hint": "经验法则。",
         "options": ["A. 10%", "B. 30%", "C. 50%", "D. 80%"],
         "answer": "C",
         "explanation": "缺失率超过50%的字段,填充会引入过多噪声,失去该列的统计意义,通常建议删除该列。"},
        {"id": "q2-3", "type": "calculation", "difficulty": "medium",
         "question": "某 DataFrame 共1000行,'age'列有50行缺失,'salary'列有30行缺失(无重叠),问总缺失行数?",
         "hint": "注意无重叠。",
         "options": ["A. 80行", "B. 50行", "C. 条件不足", "D. 20行"],
         "answer": "C",
         "explanation": "题目未说明两列缺失行的具体行位置,无法确定总缺失行数。需实际统计,不能简单相加。"},
        {"id": "q2-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 fill_missing_median(df, column) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx03': [
        {"id": "q3-1", "type": "concept", "difficulty": "easy",
         "question": "drop_duplicates(keep='first') 和 keep='last' 的区别是?",
         "hint": "保留哪一条。",
         "options": ["A. first保留序号较小的,last保留较大的", "B. first保留最新一条,last保留最旧一条", "C. first保留第一条出现的,last保留最后一条出现的", "D. 没有区别"],
         "answer": "C",
         "explanation": "keep='first'保留第一次出现的重复记录,keep='last'保留最后一次出现的。这与索引顺序和排列顺序有关。"},
        {"id": "q3-2", "type": "concept", "difficulty": "medium",
         "question": "编辑距离相似度为1.0表示两字符串完全相同,对吗?",
         "hint": "SequenceMatcher.ratio() 的返回值范围。",
         "options": ["A. 对,完全相同为1.0", "B. 错,完全相同为0.0", "C. 错,完全相同为0.5", "D. 错,完全相同可能小于1.0"],
         "answer": "A",
         "explanation": "difflib.SequenceMatcher.ratio() 在两字符串完全相同时返回1.0,是编辑距离相似度的标准度量。"},
        {"id": "q3-3", "type": "calculation", "difficulty": "medium",
         "question": "某表10000行,去重后9500行,重复率是多少?",
         "hint": "重复率 = 重复行数 / 总行数。",
         "options": ["A. 5%", "B. 95%", "C. 50%", "D. 10%"],
         "answer": "A",
         "explanation": "删除了500行重复,重复率=500/10000=5%。"},
        {"id": "q3-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 fuzzy_deduplicate(df, column, threshold) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx04': [
        {"id": "q4-1", "type": "concept", "difficulty": "easy",
         "question": "Z-score > 3 被称为3σ原则,它表示该值偏离均值多少个标准差?",
         "hint": "Z-score 定义。",
         "options": ["A. 1个标准差", "B. 2个标准差", "C. 3个标准差", "D. 4个标准差"],
         "answer": "C",
         "explanation": "Z-score = (x - μ) / σ,Z-score > 3 意味着偏离均值超过3个标准差,在正态分布中概率极低(约0.27%)。"},
        {"id": "q4-2", "type": "concept", "difficulty": "easy",
         "question": "IQR 方法中,异常值的上界定义是什么?",
         "hint": "四分位距。",
         "options": ["A. Q1 - 1.5*IQR", "B. Q3 + 1.5*IQR", "C. 均值 + 2*标准差", "D. 中位数 ± 1.5*IQR"],
         "answer": "B",
         "explanation": "IQR = Q3 - Q1,上界 = Q3 + 1.5*IQR,下界 = Q1 - 1.5*IQR。这是 Tukey's Fences 方法。"},
        {"id": "q4-3", "type": "calculation", "difficulty": "medium",
         "question": "数据 [1,2,3,4,5,100],Q1=2.5,Q3=4.5,IQR=2,上界是多少?",
         "hint": "Q3 + 1.5*IQR。",
         "options": ["A. 5", "B. 7", "C. 6", "D. 7.5"],
         "answer": "B",
         "explanation": "上界 = Q3 + 1.5*IQR = 4.5 + 1.5*2 = 7.5。"},
        {"id": "q4-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 detect_outliers_iqr(data) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx05': [
        {"id": "q5-1", "type": "concept", "difficulty": "easy",
         "question": "中国大陆手机号规范格式是多少位?",
         "hint": "运营商号段。",
         "options": ["A. 10位", "B. 11位", "C. 12位", "D. 13位"],
         "answer": "B",
         "explanation": "中国大陆手机号统一为11位,以1开头,第二位的3/4/5/7/8/9对应不同运营商。"},
        {"id": "q5-2", "type": "concept", "difficulty": "medium",
         "question": "身份证号第7-14位表示什么信息?",
         "hint": "出生日期。",
         "options": ["A. 地区代码", "B. 出生日期", "C. 顺序码", "D. 校验码"],
         "answer": "B",
         "explanation": "身份证号结构:6位地区+8位出生日期(yyyyMMdd)+3位顺序码+1位校验码。"},
        {"id": "q5-3", "type": "calculation", "difficulty": "medium",
         "question": "将 '¥1,234.56' 解析为数值,结果是多少?",
         "hint": "去除货币符号和千分位逗号。",
         "options": ["A. 1234.56", "B. 1.23", "C. 123456.0", "D. 1234"],
         "answer": "A",
         "explanation": "'¥' 和 ',' 均为格式字符,去除后得到 '1234.56',转为 float = 1234.56。"},
        {"id": "q5-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 parse_date(date_str) 函数,支持多种输入格式。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx06': [
        {"id": "q6-1", "type": "concept", "difficulty": "easy",
         "question": "全角字符的 Unicode 范围大致是多少?",
         "hint": "0xFF 系列。",
         "options": ["A. 0x00-0x7F", "B. 0xFF01-0xFF5E", "C. 0x2000-0x206F", "D. 0x3000-0x303F"],
         "answer": "B",
         "explanation": "全角英数/标点范围是 0xFF01-0xFF5E,与半角字符(0x0021-0x007E)偏移 0xFEE0。"},
        {"id": "q6-2", "type": "concept", "difficulty": "medium",
         "question": "Python 中将字符串转为 NFC 标准化的作用是什么?",
         "hint": "Unicode 等价形式。",
         "options": ["A. 转为全大写", "B. 合并等价字符的不同表示", "C. 去除空格", "D. 转义特殊字符"],
         "answer": "B",
         "explanation": "NFC (Canonical Decomposition, followed by Canonical Composition) 将 Unicode 字符的不同表示合并为唯一形式,如 'é' 的两种表示会统一。"},
        {"id": "q6-3", "type": "calculation", "difficulty": "medium",
         "question": "全角字符 'Ａ'(0xFF21) 的半角转换结果是?",
         "hint": "offset = 0xFEE0。",
         "options": ["A. 'a'", "B. 'A'", "C. 'Z'", "D. '0'"],
         "answer": "B",
         "explanation": "0xFF21 - 0xFEE0 = 0x0041 = 'A'。"},
        {"id": "q6-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 fullwidth_to_halfwidth(text) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx07': [
        {"id": "q7-1", "type": "concept", "difficulty": "easy",
         "question": "Python strip() 方法会去除哪些字符?",
         "hint": "两端。",
         "options": ["A. 仅去除空格", "B. 去除两端空格和换行", "C. 去除两端所有空白字符", "D. 去除所有空格"],
         "answer": "C",
         "explanation": "str.strip() 默认去除两端所有空白字符:空格、\\t、\\n、\\r 等。"},
        {"id": "q7-2", "type": "concept", "difficulty": "easy",
         "question": "零宽空格(U+200B)肉眼不可见,可能导致什么问题?",
         "hint": "字符串匹配。",
         "options": ["A. 内存泄漏", "B. 数据库越界", "C. 字符串比较失败", "D. 颜色显示错误"],
         "answer": "C",
         "explanation": "零宽字符肉眼不可见,但会改变字符串内容,导致 'hello' == 'hello\\u200b' 为 False,影响字符串匹配和去重。"},
        {"id": "q7-3", "type": "calculation", "difficulty": "easy",
         "question": "' hello  world  '.strip() 的结果是什么?",
         "hint": "去两端。",
         "options": ["A. 'hello  world'", "B. 'hello world'", "C. ' hello  world'", "D. 'hello  world  '"],
         "answer": "A",
         "explanation": "strip() 只去两端空格,中间空格保留,所以是 'hello  world'。"},
        {"id": "q7-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 remove_invisible_chars(text) 函数,去除零宽字符。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx08': [
        {"id": "q8-1", "type": "concept", "difficulty": "easy",
         "question": "float('inf') > 1000000 的比较结果是?",
         "hint": "无穷大。",
         "options": ["A. True", "B. False", "C. TypeError", "D. NaN"],
         "answer": "A",
         "explanation": "float('inf') 是正无穷,任何有限数都小于无穷大,所以 inf > 1000000 为 True。"},
        {"id": "q8-2", "type": "concept", "difficulty": "medium",
         "question": "Decimal('3.1') + Decimal('2.12') 的精确结果是?",
         "hint": "避免浮点误差。",
         "options": ["A. Decimal('5.22')", "B. Decimal('5.220')", "C. Decimal('5.2')", "D. Decimal('5')"],
         "answer": "A",
         "explanation": "Decimal 保持精确精度,3.1+2.12=5.22,不是浮点数的近似值。"},
        {"id": "q8-3", "type": "calculation", "difficulty": "medium",
         "question": "round(2.5, 0) 和 round(3.5, 0) 在 Python 中结果分别是多少?",
         "hint": "银行家舍入(ROUND_HALF_EVEN)。",
         "options": ["A. 3.0 和 4.0", "B. 2.0 和 4.0", "C. 3.0 和 3.0", "D. 2.0 和 3.0"],
         "answer": "A",
         "explanation": "Python 使用 ROUND_HALF_EVEN: 2.5 舍到偶数(2),3.5 舍到偶数(4)。"},
        {"id": "q8-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 filter_invalid_numbers(values) 函数,过滤 nan/inf/None。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx09': [
        {"id": "q9-1", "type": "concept", "difficulty": "easy",
         "question": " Referential Integrity(引用完整性)是指?",
         "hint": "外键约束。",
         "options": ["A. 数据格式统一", "B. 子表外键值必须在父表主键中存在", "C. 数值在有效范围内", "D. 无重复记录"],
         "answer": "B",
         "explanation": "引用完整性要求子表中的外键值必须在父表的主键中存在,否则为孤立记录,会导致关联失败。"},
        {"id": "q9-2", "type": "concept", "difficulty": "medium",
         "question": "业务一致性规则'订单支付日期 ≥ 下单日期'属于哪种校验?",
         "hint": "跨字段。",
         "options": ["A. 完整性校验", "B. 唯一性校验", "C. 跨字段逻辑校验", "D. 格式校验"],
         "answer": "C",
         "explanation": "跨字段逻辑校验检查多个字段之间的业务逻辑关系,而非单个字段的格式或完整性。"},
        {"id": "q9-3", "type": "calculation", "difficulty": "medium",
         "question": "当前日期2026-04-25,出生日期1994-01-01,年龄多少岁?",
         "hint": "月份和日期比较。",
         "options": ["A. 32岁", "B. 31岁", "C. 33岁", "D. 31.3岁"],
         "answer": "A",
         "explanation": "2026-04-25 vs 1994-01-01: 2026-1994=32岁,但4月还未过1月,所以是31岁,再验证4月25日>1月1日,确认为32岁。"},
        {"id": "q9-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 check_date_consistency(df, earlier_col, later_col) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx10': [
        {"id": "q10-1", "type": "concept", "difficulty": "easy",
         "question": "pd.concat([df1, df2]) 和 df1.merge(df2, on='id') 的主要区别是?",
         "hint": "方向。",
         "options": ["A. concat是纵向追加,merge是横向关联", "B. concat比merge快", "C. merge比concat功能多", "D. 没有区别"],
         "answer": "A",
         "explanation": "concat 做纵向(行)追加,merge 做横向(列)关联,是两种不同的数据合并方式。"},
        {"id": "q10-2", "type": "concept", "difficulty": "medium",
         "question": "多对多 merge 产生的笛卡尔积会导致?",
         "hint": "行数爆炸。",
         "options": ["A. 列数增加", "B. 数据截断", "C. 行数指数增长", "D. 无影响"],
         "answer": "C",
         "explanation": "多对多 merge 会产生笛卡尔积(左表N行×右表M行),行数会爆炸性增长,需特别注意。"},
        {"id": "q10-3", "type": "calculation", "difficulty": "medium",
         "question": "df1(100行,key重复2次) merge df2(200行,key重复2次),笛卡尔积后行数是多少?",
         "hint": "每对重复key产生4行。",
         "options": ["A. 400行", "B. 800行", "C. 1600行", "D. 200行"],
         "answer": "A",
         "explanation": "重复key在两表各有2条,merge后每对产生2×2=4行。假设100行中2条重复(1+1),200行中2条重复(1+1),实际笛卡尔积=4行。仅示例,实际取决于重复key数量。"},
        {"id": "q10-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 concat_and_dedupe(dfs, subset) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx11': [
        {"id": "q11-1", "type": "concept", "difficulty": "easy",
         "question": "数据质量四大维度中,哪个维度衡量数据无重复的程度?",
         "hint": "唯一性。",
         "options": ["A. 完整性", "B. 唯一性", "C. 一致性", "D. 有效性"],
         "answer": "B",
         "explanation": "唯一性(uniqueness)衡量数据中重复记录的比例,重复率越低,唯一性越高。"},
        {"id": "q11-2", "type": "concept", "difficulty": "medium",
         "question": "数据质量评分综合分中,各维度权重如何分配?",
         "hint": "四个维度。",
         "options": ["A. 平均权重", "B. 完整性和唯一性各30%,一致性和有效性各20%", "C. 完整性和有效性各40%,其他各10%", "D. 完全由人工决定"],
         "answer": "B",
         "explanation": "completeness 0.3 + uniqueness 0.3 + consistency 0.2 + validity 0.2,共1.0。"},
        {"id": "q11-3", "type": "calculation", "difficulty": "medium",
         "question": "某数据集100行,5行有缺失值,全局缺失率是多少?",
         "hint": "平均缺失率。",
         "options": ["A. 5%", "B. 1%", "C. 0.5%", "D. 50%"],
         "answer": "A",
         "explanation": "全局缺失率 = 总缺失单元格数 / (总行数×总列数)。题目未给出列数,5行有缺失≠5/100×列数。简化题:5/100=5%。"},
        {"id": "q11-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 generate_quality_report(df) 函数。",
         "options": None, "answer": None, "explanation": None},
    ],
    'wx12': [
        {"id": "q12-1", "type": "concept", "difficulty": "easy",
         "question": "电商订单数据中,'quantity × unit_price = total_amount' 属于哪种校验?",
         "hint": "字段间逻辑。",
         "options": ["A. 完整性校验", "B. 一致性校验", "C. 唯一性校验", "D. 有效性校验"],
         "answer": "B",
         "explanation": "这是跨字段一致性校验:检查多个字段之间的数学逻辑关系是否成立。"},
        {"id": "q12-2", "type": "concept", "difficulty": "medium",
         "question": "数据清洗流水线的日志应记录哪些信息?",
         "hint": "全流程追溯。",
         "options": ["A. 只记录错误", "B. 记录每步操作类型、影响行数、时间戳", "C. 只记录最终行数", "D. 不需要日志"],
         "answer": "B",
         "explanation": "流水线日志应记录:步骤名、操作类型、影响行数(before/after)、时间戳,以便追溯清洗过程和审计。"},
        {"id": "q12-3", "type": "calculation", "difficulty": "medium",
         "question": "某订单 quantity=9999, unit_price=5000, total_amount=49995000,应如何处理?",
         "hint": "数量异常。",
         "options": ["A. 直接删除整条记录", "B. quantity 修正为 9999//10=999", "C. quantity 修正为 9999//10=999", "D. 保持不变"],
         "answer": "C",
         "explanation": "quantity=9999 明显是测试数据或录入错误。应修正为 9999//10=999(或其他合理值),而非删除整条订单。"},
        {"id": "q12-4", "type": "coding", "difficulty": "advanced",
         "question": "请实现 clean_orders(df) 函数,整合全流程清洗。",
         "options": None, "answer": None, "explanation": None},
    ],
}

TEST_CASES = {
    'wx02': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$DataFrame [1,2,nan,4] 列a$v$, $v$返回填充后 Series$v$, false, $v$均值填充$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$DataFrame [5,nan,3,7] 列b$v$, $v$返回中位数填充后 Series$v$, false, $v$中位数填充$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$含缺失行 DataFrame$v$, $v$删除缺失行后行数减少$v$, false, $v$删除缺失行$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$含 nan Series$v$, $v$插值后无 nan$v$, true, $v$线性插值$v$, 'CONTAINS', 4);""",
    'wx03': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$[1,2,1] 重复数据$v$, $v$去重后2条$v$, false, $v$精确去重$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$相似度 hello/hallo$v$, $v$相似度>0.7$v$, false, $v$相似度计算$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$模糊去重 threshold=0.85$v$, $v$去重后行数减少$v$, true, $v$模糊去重$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$分组合并去重$v$, $v$按key去重$v$, true, $v$分组去重$v$, 'CONTAINS', 4);""",
    'wx04': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$[1,2,3,4,5,100] Z-score阈值2$v$, $v$返回异常值索引$v$, false, $v$Z-score检测$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$[1,2,3,4,5,100] IQR方法$v$, $v$返回异常值索引$v$, false, $v$IQR检测$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$裁剪到[0,10]$v$, $v$100被裁剪为10$v$, false, $v$裁剪异常值$v$, 'EXACT_MATCH', 3),
    (new_task_id, 'tc_4', $v$移除异常值$v$, $v$返回正常值列表$v$, true, $v$移除异常值$v$, 'CONTAINS', 4);""",
    'wx05': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$2024-01-15$v$, $v$2024-01-15$v$, false, $v$日期解析$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$138-1234-5678$v$, $v$13812345678$v$, false, $v$手机号规范化$v$, 'EXACT_MATCH', 2),
    (new_task_id, 'tc_3', $v$¥1,234.56$v$, $v$1234.56$v$, false, $v$金额解析$v$, 'EXACT_MATCH', 3),
    (new_task_id, 'tc_4', $v$身份证校验$v$, $v$返回valid/birth_date$v$, true, $v$身份证校验$v$, 'CONTAINS', 4);""",
    'wx06': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$ＨＥＬＬＯ$v$, $v$HELLO$v$, false, $v$全角转半角$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$含控制字符字符串$v$, $v$去除控制字符$v$, false, $v$控制字符去除$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$hello world$v$, $v$hello world$v$, false, $v$综合文本清洗$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$保留字母数字$v$, $v$去除特殊字符$v$, true, $v$特殊字符去除$v$, 'CONTAINS', 4);""",
    'wx07': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$  hello   world  $v$, $v$hello world$v$, false, $v$去空格$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$Hello World lower$v$, $v$hello world$v$, false, $v$大小写规范化$v$, 'EXACT_MATCH', 2),
    (new_task_id, 'tc_3', $v$helloZWSPworld$v$, $v$helloworld$v$, false, $v$零宽字符去除$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$综合字符串清洗$v$, $v$返回清洗后字符串$v$, true, $v$综合清洗$v$, 'CONTAINS', 4);""",
    'wx08': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$1,234.56$v$, $v$1234.56$v$, false, $v$数值解析$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$round 3.14159 to 2$v$, $v$3.14$v$, false, $v$精度控制$v$, 'EXACT_MATCH', 2),
    (new_task_id, 'tc_3', $v$[1,2,100,3,4] IQR$v$, $v$100被移除$v$, false, $v$异常值过滤$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$含nan/inf列表$v$, $v$返回有效数值$v$, true, $v$无效值过滤$v$, 'CONTAINS', 4);""",
    'wx09': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$age=30, birth=1994-01-01$v$, $v$consistent=true$v$, false, $v$年龄一致性$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$引用完整性检查$v$, $v$返回无效值行$v$, false, $v$外键校验$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$日期一致性检查$v$, $v$返回违规行$v$, false, $v$日期逻辑校验$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$批量一致性检查$v$, $v$返回违规报告$v$, true, $v$批量校验$v$, 'CONTAINS', 4);""",
    'wx10': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$两表 inner merge$v$, $v$返回合并结果$v$, false, $v$表合并$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$concat后去重$v$, $v$返回无重复DataFrame$v$, false, $v$合并去重$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$合并后去重$v$, $v$保留指定记录$v$, false, $v$选择性去重$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$合并前校验$v$, $v$返回left/right_dups$v$, true, $v$主键校验$v$, 'CONTAINS', 4);""",
    'wx11': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$计算质量评分$v$, $v$返回0~1之间的overall_score$v$, false, $v$质量评分$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$生成质量报告$v$, $v$含total_rows/quality_score$v$, false, $v$质量报告$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$清洗前后对比$v$, $v$返回delta字典$v$, false, $v$效果对比$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$质量等级评分$v$, $v$返回 A/B/C/D$v$, true, $v$质量等级$v$, 'CONTAINS', 4);""",
    'wx12': """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$加载原始订单$v$, $v$返回5行DataFrame$v$, false, $v$数据加载$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$清洗后无重复order_id$v$, $v$order_id唯一$v$, false, $v$去重验证$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$运行完整流水线$v$, $v$返回DataFrame和统计$v$, false, $v$流水线执行$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$金额一致性检查$v$, $v$total_amount=quantity*unit_price$v$, true, $v$金额一致性$v$, 'CONTAINS', 4);""",
}

DIFFICULTIES = {
    'wx02': 'beginner', 'wx03': 'intermediate', 'wx04': 'intermediate',
    'wx05': 'intermediate', 'wx06': 'intermediate', 'wx07': 'beginner',
    'wx08': 'intermediate', 'wx09': 'intermediate', 'wx10': 'intermediate',
    'wx11': 'intermediate', 'wx12': 'advanced',
}


def gen_handbook_json(name):
    import yaml as _yaml
    with open(f'stage_{name}.yaml', encoding='utf-8') as f:
        data = _yaml.safe_load(f)
    chapters = data.get('chapters', [])
    content_parts = []
    for ch in chapters:
        content_parts.append(f"## {ch['title']}\n\n{ch['content']}")
    d = {
        'title': data['title'],
        'content': '\n\n'.join(content_parts),
    }
    with open(f'output/stage_{name}_handbook.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d


def gen_sql(name, order):
    d = gen_handbook_json(name)
    title = d['title']
    content = d['content']
    q_data = json.dumps({"questions": QUESTIONS[name]}, ensure_ascii=False)
    test_cases = TEST_CASES[name]
    difficulty = DIFFICULTIES[name]

    sql = """-- ============================================================
-- WX%(order)d: %(title)s
-- practice_id=5, order_in_practice=%(order)d
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    5,
    $v$%(title)s$v$,
    'PRACTICE',
    %(order)d,
    $v$%(difficulty)s$v$,
    $v$%(content)s$v$,
    $v$%(q_data)s$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 5 AND order_in_practice = %(order)d;

    %(test_cases)s

    RAISE NOTICE 'Inserted task tests for WX%(order)d';
END $$;

COMMIT;
""" % {
        'order': order,
        'title': title,
        'content': content,
        'q_data': q_data,
        'test_cases': test_cases,
        'difficulty': difficulty,
    }
    return sql


if __name__ == '__main__':
    for nm, order in [
        ('wx02', 2), ('wx03', 3), ('wx04', 4), ('wx05', 5), ('wx06', 6),
        ('wx07', 7), ('wx08', 8), ('wx09', 9), ('wx10', 10), ('wx11', 11), ('wx12', 12),
    ]:
        sql = gen_sql(nm, order)
        path = f'deploy/scripts/stage_{nm}_insert.sql'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(sql)
        print(f"Generated {path} ({len(sql)} chars)")
    print("All done.")
