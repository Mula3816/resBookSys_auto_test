"""读取 JSON 用例文件,用于数据驱动参数化"""
import json


def read_json_data(filename):
    """读取用例 JSON 文件。

    每条用例形如:
        {"description": "用例说明", "req_data": {...}, "status_code": 400, "message": "..."}

    返回 (参数元组列表, 用例说明列表),可直接用于 pytest.mark.parametrize:
        params, ids = read_json_data(path)
        pytest.mark.parametrize('req_data,status_code,message', params, ids=ids)
    """
    with open(filename, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    params = []
    ids = []
    for data in json_data:
        # description 仅作用例说明,按 key 弹出(不依赖字段顺序),
        # 剩余字段按 JSON 中的顺序组成参数元组
        ids.append(data.pop('description', None))
        params.append(tuple(data.values()))
    return params, ids
