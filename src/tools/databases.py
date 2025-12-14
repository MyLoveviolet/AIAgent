# src/tools/database.py
import json
import os


class ChengyuDatabase:
    def __init__(self, data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            self.indexed_data = json.load(f)
        # 🔴 关键优化：预先将列表转为集合
        self.indexed_sets = {
            char: set(idioms) for char, idioms in self.indexed_data.items()
        }

    def query_by_first_char(self, first_char, exclude_set=None):
        exclude_set = exclude_set or set()

        if first_char not in self.indexed_sets:
            return []

        # 🔴 使用集合差集运算：O(1)平均时间复杂度
        all_set = self.indexed_sets[first_char]
        available_set = all_set - exclude_set  # 集合差集，极快！

        return list(available_set)

    def contains(self, idiom):
        if not idiom or len(idiom) != 4:
            return False
        first_char = idiom[0]
        # 也优化存在性检查
        return idiom in self.indexed_sets.get(first_char, set())


# 全局实例（在应用启动时加载）
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/processed/indexed_idioms.json')
chengyu_db = ChengyuDatabase(DB_PATH)