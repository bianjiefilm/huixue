-- NN10 (task_id=103) function_call task_tests — 30 条

BEGIN;

DELETE FROM task_tests WHERE task_id=103;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (103, 'fc_rnn_zero_input_zero_hidden', $${"function": "rnn_single_step", "args": [[0.0], [0.0], [[1.0]], [[1.0]], [0.0]], "kwargs": {}}$$, $${"result": [0.0], "tolerance": 0.0001}$$, false, 'function_call', 1),
  (103, 'fc_rnn_unit_input', $${"function": "rnn_single_step", "args": [[1.0], [0.0], [[1.0]], [[1.0]], [0.0]], "kwargs": {}}$$, $${"result": [0.7615941559557649], "tolerance": 0.0001}$$, true, 'function_call', 2),
  (103, 'fc_rnn_with_hidden', $${"function": "rnn_single_step", "args": [[0.0], [2.0], [[1.0]], [[0.5]], [0.0]], "kwargs": {}}$$, $${"result": [0.7615941559557649], "tolerance": 0.0001}$$, true, 'function_call', 3),
  (103, 'fc_rnn_two_dim', $${"function": "rnn_single_step", "args": [[1.0, 1.0], [0.0, 0.0], [[1.0, 0.0], [0.0, 1.0]], [[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0]], "kwargs": {}}$$, $${"result": [0.7615941559557649, 0.7615941559557649], "tolerance": 0.0001}$$, true, 'function_call', 4),
  (103, 'fc_rnn_with_bias', $${"function": "rnn_single_step", "args": [[0.0], [0.0], [[1.0]], [[1.0]], [5.0]], "kwargs": {}}$$, $${"result": [0.9999092042625951], "tolerance": 0.0001}$$, true, 'function_call', 5),
  (103, 'fc_rnn_raises_on_dim_mismatch', $${"function": "rnn_single_step", "args": [[1.0, 2.0], [0.0], [[1.0]], [[1.0]], [0.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (103, 'fc_rnn_raises_on_empty', $${"function": "rnn_single_step", "args": [[], [], [], [], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (103, 'fc_rnn_raises_on_non_list', $${"function": "rnn_single_step", "args": ["ab", [0.0], [[1.0]], [[1.0]], [0.0]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (103, 'fc_lstm_basic', $${"function": "lstm_gates", "args": [[1.0], [0.0], [[[0.5], [0.3]], [[0.5], [0.3]], [[0.5], [0.3]], [[0.5], [0.3]]], [[0.0], [0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"result": [[0.6224593312018546], [0.6224593312018546], [0.6224593312018546], [0.46211715726000974]], "tolerance": 0.0001}$$, false, 'function_call', 9),
  (103, 'fc_lstm_different_gates', $${"function": "lstm_gates", "args": [[1.0], [0.0], [[[1.0], [0.0]], [[0.0], [0.0]], [[2.0], [0.0]], [[1.0], [0.0]]], [[0.0], [0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"result": [[0.7310585786300049], [0.5], [0.8807970779778823], [0.7615941559557649]], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (103, 'fc_lstm_with_h_prev', $${"function": "lstm_gates", "args": [[0.0], [2.0], [[[0.0], [1.0]], [[0.0], [1.0]], [[0.0], [1.0]], [[0.0], [1.0]]], [[0.0], [0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"result": [[0.8807970779778823], [0.8807970779778823], [0.8807970779778823], [0.9640275800758169]], "tolerance": 0.0001}$$, true, 'function_call', 11),
  (103, 'fc_lstm_with_bias', $${"function": "lstm_gates", "args": [[0.0], [0.0], [[[0.0], [0.0]], [[0.0], [0.0]], [[0.0], [0.0]], [[0.0], [0.0]]], [[1.0], [1.0], [1.0], [1.0]]], "kwargs": {}}$$, $${"result": [[0.7310585786300049], [0.7310585786300049], [0.7310585786300049], [0.7615941559557649]], "tolerance": 0.0001}$$, true, 'function_call', 12),
  (103, 'fc_lstm_raises_on_wrong_W_count', $${"function": "lstm_gates", "args": [[1.0], [0.0], [[[0.5], [0.3]], [[0.5], [0.3]], [[0.5], [0.3]]], [[0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (103, 'fc_lstm_raises_on_dim_mismatch', $${"function": "lstm_gates", "args": [[1.0, 2.0], [0.0], [[[0.5], [0.3]], [[0.5], [0.3]], [[0.5], [0.3]], [[0.5], [0.3]]], [[0.0], [0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (103, 'fc_lstm_raises_on_non_list', $${"function": "lstm_gates", "args": ["ab", [0.0], [[[0.5]], [[0.5]], [[0.5]], [[0.5]]], [[0], [0], [0], [0]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (103, 'fc_gru_basic', $${"function": "gru_gates", "args": [[1.0], [0.0], [[[0.5], [0.0]], [[0.5], [0.0]], [[0.5], [0.0]]], [[0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"result": [[0.6224593312018546], [0.6224593312018546], [0.46211715726000974]], "tolerance": 0.0001}$$, false, 'function_call', 16),
  (103, 'fc_gru_with_hidden_no_reset', $${"function": "gru_gates", "args": [[0.0], [1.0], [[[0.0], [1.0]], [[0.0], [0.0]], [[0.0], [1.0]]], [[0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"result": [[0.7310585786300049], [0.5], [0.46211715726000974]], "tolerance": 0.0001}$$, true, 'function_call', 17),
  (103, 'fc_gru_zero_input_and_hidden', $${"function": "gru_gates", "args": [[0.0], [0.0], [[[0.0], [0.0]], [[0.0], [0.0]], [[0.0], [0.0]]], [[0.0], [0.0], [0.0]]], "kwargs": {}}$$, $${"result": [[0.5], [0.5], [0.0]], "tolerance": 0.0001}$$, true, 'function_call', 18),
  (103, 'fc_gru_with_bias', $${"function": "gru_gates", "args": [[0.0], [0.0], [[[0.0], [0.0]], [[0.0], [0.0]], [[0.0], [0.0]]], [[1.0], [1.0], [1.0]]], "kwargs": {}}$$, $${"result": [[0.7310585786300049], [0.7310585786300049], [0.7615941559557649]], "tolerance": 0.0001}$$, true, 'function_call', 19),
  (103, 'fc_gru_raises_on_wrong_W_count', $${"function": "gru_gates", "args": [[1.0], [0.0], [[[0.5]], [[0.5]]], [[0], [0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (103, 'fc_gru_raises_on_dim_mismatch', $${"function": "gru_gates", "args": [[1.0, 2.0], [0.0], [[[0.5]], [[0.5]], [[0.5]]], [[0], [0], [0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (103, 'fc_gru_raises_on_non_list', $${"function": "gru_gates", "args": ["ab", [0.0], [[[0.5]], [[0.5]], [[0.5]]], [[0], [0], [0]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22),
  (103, 'fc_trunc_within_max', $${"function": "compute_sequence_length_after_truncate", "args": [50, 100], "kwargs": {}}$$, $${"result": 50}$$, false, 'function_call', 23),
  (103, 'fc_trunc_exceeds_max', $${"function": "compute_sequence_length_after_truncate", "args": [200, 100], "kwargs": {}}$$, $${"result": 100}$$, true, 'function_call', 24),
  (103, 'fc_trunc_equal', $${"function": "compute_sequence_length_after_truncate", "args": [100, 100], "kwargs": {}}$$, $${"result": 100}$$, true, 'function_call', 25),
  (103, 'fc_trunc_zero_seq', $${"function": "compute_sequence_length_after_truncate", "args": [0, 100], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 26),
  (103, 'fc_trunc_one_seq', $${"function": "compute_sequence_length_after_truncate", "args": [1, 100], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 27),
  (103, 'fc_trunc_raises_on_negative_seq', $${"function": "compute_sequence_length_after_truncate", "args": [-1, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (103, 'fc_trunc_raises_on_zero_max', $${"function": "compute_sequence_length_after_truncate", "args": [50, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (103, 'fc_trunc_raises_on_non_int', $${"function": "compute_sequence_length_after_truncate", "args": [50.5, 100], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 30);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=103 GROUP BY task_id;

COMMIT;