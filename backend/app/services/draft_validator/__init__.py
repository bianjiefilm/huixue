"""草稿校验服务：结构/安全校验 + 对抗攻击验证 + 5 条红线检查。

对齐《慧学AI升级方案-v2.md》第九章、第十五章。

本包只做校验/攻击门禁本身，不涉及 AI 生成、不涉及草稿 CRUD API，
不修改任何现有评测执行路径 (backend/app/services/code_executor.py 等)。
"""

from .attack_engine import AttackEngine, check_redlines, run_attack_matrix

__all__ = ["AttackEngine", "check_redlines", "run_attack_matrix"]
