"""餐厅模块接口测试(与后端 routes/restaurants.js 对应)

- TestRestaurants:     无状态用例,JSON 数据驱动(data/restaurants/restaurants.json)
- TestRestaurantFlow:  链路用例(开店→建桌→改→删;删除级联行为观察)
"""
import pytest

from api.reservations_api import ReservationsApi
from api.restaurants_api import RestaurantsApi
from api.tables_api import TablesApi
from common.helpers import fill_sentinels
from common.read_json_data import read_json_data
from config import BASE_DIR, FLOW_RESERVATION_DATES

LIFECYCLE_DATE = FLOW_RESERVATION_DATES[0]

# 最小 PNG 文件头 + 填充内容(multer 只校验 mimetype,不校验图片内容)
FAKE_PNG = b'\x89PNG\r\n\x1a\n' + b'0' * 100


@pytest.fixture
def api():
    """餐厅模块接口对象"""
    return RestaurantsApi()


def _resolve_token(token, client_token, merchant_token, admin_token):
    """把 token 字段里的占位符替换为真实 token;游客(#guest#)替换为空"""
    return fill_sentinels({'token': token}, **{
        '#guest#': '',
        '#client_token#': client_token,
        '#merchant_token#': merchant_token,
        '#admin_token#': admin_token,
    })['token']


class TestRestaurants:
    """餐厅模块接口(无状态用例,JSON 数据驱动)"""

    data_path = f'{BASE_DIR}/data/restaurants/restaurants.json'
    cases, ids = read_json_data(data_path)

    @pytest.mark.parametrize('action,token,params,req_data,response',
                             cases, ids=ids)
    def test_restaurants(self, api, client_token, merchant_token, admin_token,
                         action, token, params, req_data, response):
        token = _resolve_token(token, client_token, merchant_token, admin_token)

        if action == 'list':
            resp = api.list(**params)
        elif action == 'get':
            resp = api.get(params['id'])
        elif action == 'stats':
            resp = api.stats(**{k: v for k, v in params.items() if k != 'id'})
        elif action == 'availability':
            resp = api.availability(
                params['id'], **{k: v for k, v in params.items() if k != 'id'})
        elif action == 'create':
            resp = api.create(req_data, token)
        elif action == 'update':
            resp = api.update(params['id'], req_data, token)
        elif action == 'delete':
            resp = api.delete(params['id'], token)
        else:
            raise ValueError(f'未知 action: {action}')

        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 200:
            check = response.get('check')
            if check == 'non_empty':
                assert body['pagination']['total'] >= 1
                assert len(body['restaurants']) >= 1
            elif check == 'empty':
                assert body['pagination']['total'] == 0
            elif check == 'limit_ok':
                assert len(body['restaurants']) == 1
            elif check == 'detail':
                assert body['id'] == params['id']
                assert isinstance(body['tables'], list)
            elif check == 'stats':
                assert 'total' in body and 'averageRating' in body
            elif check == 'availability':
                assert isinstance(body['availability'], list)
                assert len(body['availability']) >= 1
        else:
            # 400 参数校验失败:错误信息在 errors 数组;业务失败:在顶层 message 字段
            if 'errors' in body:
                actual_message = body['errors'][0]['msg']
            else:
                actual_message = body['message']
            assert actual_message == response['message'], resp.text


class TestRestaurantFlow:
    """餐厅模块链路用例(状态有依赖,数据自清理)"""

    def test_restaurant_lifecycle(self, merchant_token, unique_name):
        """开店(带图片上传) → 详情 → 建桌台 → 改桌台 → 可用性 → 改店 → 删桌台 → 删店 → 404"""
        api = RestaurantsApi()
        tables_api = TablesApi()

        # 1. 商家开店(multipart 图片上传,归属自动为商家本人)
        resp = api.create({
            'name': unique_name,
            'description': '接口自动化测试创建的餐厅描述',
            'cuisine_type': '中餐',
            'address': '北京市朝阳区测试路 1 号',
            'phone': '13800138000',
            'email': 'test@test.com',
            'opening_time': '11:00',
            'closing_time': '23:00',
            'capacity': 100,
            'status': 'active',
        }, merchant_token,
            files={'image': ('test.png', FAKE_PNG, 'image/png')})
        assert resp.status_code == 201, resp.text
        restaurant_id = resp.json()['restaurantId']

        # 2. 详情:新店无桌台,归属为商家本人(id=2)
        resp = api.get(restaurant_id)
        assert resp.status_code == 200, resp.text
        detail = resp.json()
        assert detail['tables'] == []
        assert detail['owner_id'] == 2
        assert detail['image'].startswith('/uploads/')

        # 3. 商家在自己店里建桌台
        resp = tables_api.create(
            {'restaurant_id': restaurant_id, 'table_number': 'T-01',
             'capacity': 4}, merchant_token)
        assert resp.status_code == 201, resp.text
        table_id = resp.json()['tableId']

        # 4. 修改桌台容量并校验
        resp = tables_api.update(table_id, {'capacity': 6}, merchant_token)
        assert resp.status_code == 200, resp.text
        resp = tables_api.get(table_id)
        assert resp.json()['table']['capacity'] == 6

        # 5. 新桌台无预订,任意日期全天可用
        resp = tables_api.availability(table_id, date='2026-12-25')
        assert resp.status_code == 200, resp.text
        assert resp.json()['availability']

        # 6. 修改餐厅描述
        resp = api.update(restaurant_id,
                          {'description': '更新后的餐厅描述,用于验证更新接口'},
                          merchant_token)
        assert resp.status_code == 200, resp.text

        # 7. 删除桌台(无预订,可删)
        resp = tables_api.delete(table_id, merchant_token)
        assert resp.status_code == 200, resp.text

        # 8. 删除餐厅 → 详情 404
        resp = api.delete(restaurant_id, merchant_token)
        assert resp.status_code == 200, resp.text
        resp = api.get(restaurant_id)
        assert resp.status_code == 404

    def test_delete_restaurant_cascades_reservations(self, admin_token,
                                                     client_token, unique_name):
        """行为观察:删除餐厅会级联删除其预订(与桌台的删除保护不一致)

        当前后端删除餐厅时没有"存在有效预订"保护,预订随餐厅被级联删除。
        此用例固化当前真实行为;若产品后续为餐厅删除增加保护,
        该用例会失败并提示行为变更,起到回归哨兵的作用。
        """
        api = RestaurantsApi()
        tables_api = TablesApi()
        reservations_api = ReservationsApi()

        # 管理员开店 → 建桌台
        resp = api.create({
            'name': unique_name,
            'description': '接口自动化测试创建的餐厅描述',
            'cuisine_type': '中餐',
            'address': '北京市朝阳区测试路 1 号',
            'phone': '13800138000',
            'email': 'test@test.com',
            'opening_time': '11:00',
            'closing_time': '23:00',
            'capacity': 100,
            'status': 'active',
        }, admin_token)
        assert resp.status_code == 201, resp.text
        restaurant_id = resp.json()['restaurantId']

        resp = tables_api.create(
            {'restaurant_id': restaurant_id, 'table_number': 'T-01',
             'capacity': 4}, admin_token)
        assert resp.status_code == 201, resp.text
        table_id = resp.json()['tableId']

        # 客户预订该桌台
        resp = reservations_api.create({
            'restaurant_id': restaurant_id, 'table_id': table_id,
            'reservation_date': LIFECYCLE_DATE, 'reservation_time': '19:00',
            'party_size': 4
        }, client_token)
        assert resp.status_code == 201, resp.text
        reservation_id = resp.json()['reservationId']

        # 管理员删除餐厅 → 预订被级联删除,查详情 404
        resp = api.delete(restaurant_id, admin_token)
        assert resp.status_code == 200, resp.text
        resp = reservations_api.get(reservation_id, client_token)
        assert resp.status_code == 404
