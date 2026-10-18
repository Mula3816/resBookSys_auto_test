"""测试公共辅助函数"""


def fill_sentinels(data: dict, **mapping) -> dict:
    """把 data 中的占位符(如 #unique_email#)替换为实际值

    例:fill_sentinels({'email': '#unique_email#'}, **{'#unique_email#': 'a@b.com'})
    → {'email': 'a@b.com'}
    """
    return {k: (mapping[v] if isinstance(v, str) and v in mapping else v)
            for k, v in data.items()}
