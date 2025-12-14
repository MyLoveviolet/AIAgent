# scripts/preprocess_data.py
import json
from collections import defaultdict


def create_indexed_database(input_path, output_path):
    """
    将原始的成语列表JSON，处理为首字索引的JSON。

    Args:
        input_path: 原始idiom.json的路径
        output_path: 处理后的输出路径
    """
    # 1. 加载原始数据
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_idioms = json.load(f)  # 应是一个列表

    # 2. 创建索引字典：键为首字，值为该字开头的所有成语列表
    index_dict = defaultdict(list)

    for item in raw_idioms:
        # 确保是字典且包含'word'字段
        if isinstance(item, dict) and 'word' in item:
            idiom = item['word'].strip()
            if len(idiom) == 4:  # 确保是四字成语
                first_char = idiom[0]
                index_dict[first_char].append(idiom)

    # 3.（可选）对每个列表去重和排序
    for key in index_dict:
        index_dict[key] = sorted(list(set(index_dict[key])))

    # 4. 保存处理后的索引数据
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_dict, f, ensure_ascii=False, indent=2)

    print(f"处理完成！共处理 {len(raw_idioms)} 条数据，生成 {len(index_dict)} 个首字索引。")
    print(f"示例：以'一'开头的成语有 {len(index_dict.get('一', []))} 个。")


# 运行
if __name__ == "__main__":
    create_indexed_database(
        input_path="../data/raw/idiom.json",  # 你的原始文件路径
        output_path="../data/processed/indexed_idioms.json"
    )