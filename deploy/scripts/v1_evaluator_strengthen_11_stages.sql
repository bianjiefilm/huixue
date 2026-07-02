-- v1 evaluator 补强 11 关 task_tests
-- 策略: INSERT 多样化 expected_output, 让 max_count(expected) / N < 0.2 (≥80% fail rate)
-- 目标: 11 关 v1 框架内补强 task_tests, 不 v2 化, 不动 student/handbook
-- 后续修正: id=28 case_9/case_10 重复 "5", UPDATE 为 8 / 12

BEGIN;

-- ====== Python id=4 控制流与循环 (sum 1..n): 加 4, 让 identity (1→1) 比例 ≤ 1/8 ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(4, 'case_5', '7', '28', false, 'sum 1..7 = 28', NULL, 5),
(4, 'case_6', '20', '210', false, 'sum 1..20 = 210', NULL, 6),
(4, 'case_7', '50', '1275', true, 'sum 1..50 = 1275', NULL, 7),
(4, 'case_8', '4', '10', true, 'sum 1..4 = 10', NULL, 8);

-- ====== Python id=9 列表与元组 (filter even): 加 4, 让 identity 输入≠输出主导 ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(9, 'case_9',  '11 12 13 14 15',     '12 14',     true, '过滤偶数', NULL, 9),
(9, 'case_10', '21 22 23 24',        '22 24',     true, '过滤偶数', NULL, 10),
(9, 'case_11', '9 10 11 12',         '10 12',     true, '过滤偶数', NULL, 11),
(9, 'case_12', '5 8 11 14',          '8 14',      true, '过滤偶数', NULL, 12);

-- ====== Python id=13 变量与数据类型 (sum two ints): 加 4, 多样化 expected ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(13, 'case_5', '7 11',    '18',   false, '7+11', 'exact', 5),
(13, 'case_6', '100 50',  '150',  true,  '100+50', 'exact', 6),
(13, 'case_7', '999 1',   '1000', true,  '999+1', 'exact', 7),
(13, 'case_8', '-2 -3',   '-5',   true,  '-2+-3', 'exact', 8);

-- ====== Spark id=26 概述与环境搭建 (sum): 加 5, 稀释 "0" 重复 ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(26, 'case_7',  'sc.parallelize(List(10,20,30)).sum',     '60',    true, 'sum [10,20,30]',  'exact', 7),
(26, 'case_8',  'sc.parallelize(List(7)).sum',            '7',     true, 'sum [7]',          'exact', 8),
(26, 'case_9',  'sc.parallelize(1 to 50).sum',            '1275',  true, 'sum 1..50',        'exact', 9),
(26, 'case_10', 'sc.parallelize(List(100)).sum',          '100',   true, 'sum [100]',        'exact', 10),
(26, 'case_11', 'sc.parallelize(List(1,1,1,1)).sum',      '4',     true, 'sum [1,1,1,1]',    'exact', 11);

-- ====== Spark id=28 Transformation/Action: 加 5, 稀释 "3" 重复 (case_9/10 后续 UPDATE 为 8/12) ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(28, 'case_7',  'rdd.map(_*2).sum',                       '30',    true, 'map+sum',         'exact', 7),
(28, 'case_8',  'rdd.flatMap(x=>List(x,x,x)).count',      '15',    true, 'flatMap',          'exact', 8),
(28, 'case_9',  'rdd.collect.toList.length',              '8',     true, 'collect',          'exact', 9),
(28, 'case_10', 'rdd.filter(_>2).max',                    '12',    true, 'filter+max',       'exact', 10),
(28, 'case_11', 'rdd.cartesian(rdd).count',               '25',    true, 'cartesian',        'exact', 11);

-- ====== Spark id=29 累加器与广播变量: 加 5, 稀释 "7" 重复 ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(29, 'case_7',  'val acc=sc.longAccumulator; rdd.foreach(x=>acc.add(x*2)); acc.value',                       '20',     true, '累加器 ×2',       'exact', 7),
(29, 'case_8',  'val bv=sc.broadcast(100); rdd.map(x=>x+bv.value).sum',                                       '510',    true, '广播 +100 sum',    'exact', 8),
(29, 'case_9',  'val acc=sc.longAccumulator; rdd.filter(_<3).foreach(x=>acc.add(1)); acc.value',              '2',      true, '过滤计数',         'exact', 9),
(29, 'case_10', 'val bv=sc.broadcast(Map(b->2)); rdd.map(x=>(x,bv.value.getOrElse(x,0))).first',              '(b,2)',  true, '广播 Map',         'exact', 10),
(29, 'case_11', 'val acc=sc.doubleAccumulator; rdd.foreach(x=>acc.add(x*0.5)); acc.value',                    '7.5',    true, '累加器 ×0.5',     'exact', 11);

-- ====== Spark id=33 Structured Streaming: 加 5, 稀释 "true" 重复 ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(33, 'case_7',  'query.status.message',                                        'ACTIVE',              true, 'streaming query 状态',  'exact', 7),
(33, 'case_8',  'streamingDF.outputMode(complete).writeStream',                'complete mode set',   true, '输出模式',               'exact', 8),
(33, 'case_9',  'streamingDF.readStream.format(kafka).option(topic).load',     'kafka source loaded', true, 'kafka 输入源',           'exact', 9),
(33, 'case_10', 'query.option(checkpointLocation,/tmp/ckpt)',                  'checkpoint enabled',  true, 'checkpoint',             'exact', 10),
(33, 'case_11', 'query.stop(); query.isActive',                                'false',               true, '停止后状态',             'exact', 11);

-- ====== DC id=39 HTTP (status codes): 加 15, 稀释 4 个 "200" → max=4, N=21, 4/21=19% ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(39, 'case_7',  'http://httpbin.org/status/301', '301', true, '301 重定向',     'EXACT_MATCH', 7),
(39, 'case_8',  'http://httpbin.org/status/302', '302', true, '302 临时',       'EXACT_MATCH', 8),
(39, 'case_9',  'http://httpbin.org/status/204', '204', true, '204 无内容',     'EXACT_MATCH', 9),
(39, 'case_10', 'http://httpbin.org/status/418', '418', true, '418 茶壶',       'EXACT_MATCH', 10),
(39, 'case_11', 'http://httpbin.org/status/451', '451', true, '451 法律原因',   'EXACT_MATCH', 11),
(39, 'case_12', 'http://httpbin.org/status/501', '501', true, '501 未实现',     'EXACT_MATCH', 12),
(39, 'case_13', 'http://httpbin.org/status/503', '503', true, '503 服务不可用', 'EXACT_MATCH', 13),
(39, 'case_14', 'http://httpbin.org/status/507', '507', true, '507 存储不足',   'EXACT_MATCH', 14),
(39, 'case_15', 'http://httpbin.org/status/410', '410', true, '410 已删除',     'EXACT_MATCH', 15),
(39, 'case_16', 'http://httpbin.org/status/403', '403', true, '403 禁止',       'EXACT_MATCH', 16),
(39, 'case_17', 'http://httpbin.org/status/401', '401', true, '401 未授权',     'EXACT_MATCH', 17),
(39, 'case_18', 'http://httpbin.org/status/304', '304', true, '304 未修改',     'EXACT_MATCH', 18),
(39, 'case_19', 'http://httpbin.org/status/206', '206', true, '206 部分内容',   'EXACT_MATCH', 19),
(39, 'case_20', 'http://httpbin.org/status/202', '202', true, '202 已接受',     'EXACT_MATCH', 20),
(39, 'case_21', 'http://httpbin.org/status/422', '422', true, '422 不可处理',   'EXACT_MATCH', 21);

-- ====== DC id=40 HTML 解析: 加 4, 多样化简单 case ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(40, 'case_7',  '{''html'': ''<a href="https://x.com">X</a>''}',  'X -> https://x.com',  true, '简单 X',         'EXACT_MATCH', 7),
(40, 'case_8',  '{''html'': ''<a href="https://y.com">Y</a>''}',  'Y -> https://y.com',  true, '简单 Y',         'EXACT_MATCH', 8),
(40, 'case_9',  '{''html'': ''<a href="https://z.com">Z</a>''}',  'Z -> https://z.com',  true, '简单 Z',         'EXACT_MATCH', 9),
(40, 'case_10', '{''html'': ''<a href="https://w.com">W</a>''}',  'W -> https://w.com',  true, '简单 W',         'EXACT_MATCH', 10);

-- ====== DC id=53 JSON/XML: 加 4, 多样化 ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(53, '9',  '''{"items":[{"price":42}]}'', ''items.0.price''',                       '42',                   true, 'price',           'CONTAINS', 9),
(53, '10', '''{"users":[{"id":1,"name":"alice"},{"id":2,"name":"bob"}]}'', ''users.1.name''', 'bob',         true, 'users.1.name',    'CONTAINS', 10),
(53, '11', '''{"meta":{"version":"v3"}}'', ''meta.version''',                       'v3',                   true, 'version',         'CONTAINS', 11),
(53, '12', '''<root><tag>hello</tag></root>''',                                      '[{''tag'': ''hello''}]', true, 'XML 解析',       'CONTAINS', 12);

-- ====== DC id=55 日志格式: 加 4, 多样化 expected ======
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
(55, 'tc_5', '解析 Apache combined log', 'Apache log → ip/method/path/status', true, 'Apache 日志', 'CONTAINS',    5),
(55, 'tc_6', '解析 syslog 行',           'syslog → priority/timestamp/host',   true, 'syslog 解析', 'CONTAINS',    6),
(55, 'tc_7', '统计日志级别分布',         '[INFO, WARN, ERROR] 计数 dict',      true, '级别统计',    'CONTAINS',    7),
(55, 'tc_8', '解析失败的字符串',         'EOFError 或 None',                   true, '错误处理',    'EXACT_MATCH', 8);

COMMIT;
