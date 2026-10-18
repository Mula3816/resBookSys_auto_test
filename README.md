# 餐厅订位系统 —— 接口 + UI 自动化测试

针对 `/mnt/restaurant-booking-system-master` 的双层自动化测试:
- **接口层**:覆盖认证、预定、用户管理、餐厅、桌台 5 模块 30 接口共 163 个用例
- **UI 层**:Playwright + POM 的 P0 冒烟用例 10 条(游客浏览/登录注册/预订链路/管理后台)
- 支持 CI、失败重试、并发执行与测试数据自动清理

## 目录结构

```
resBookSys_api_test/
├── config.py                 # 全局配置(服务地址、后端路径、链路日期等)
├── pytest.ini                # pytest 配置(报告 + 失败重试)
├── requirements.txt          # 测试依赖(CI 安装用)
├── conftest.py               # 公共 fixture:自动拉起后端、数据清理、三角色 token
├── .github/workflows/        # GitHub Actions CI:push/PR 自动跑全量用例
├── scripts/run_ci.sh         # 本地模拟 CI 全流程(支持串行/并发)
├── api/
│   ├── auth_api.py           # 认证模块接口封装(register/login/me/profile)
│   ├── reservations_api.py   # 预定模块接口封装(列表/详情/创建/状态/取消/付款/删除/统计)
│   ├── restaurants_api.py    # 餐厅模块接口封装(列表/统计/详情/可用性/增删改,支持图片上传)
│   ├── tables_api.py         # 桌台模块接口封装(列表/详情/可用性/增删改)
│   └── users_api.py          # 用户管理模块接口封装(列表/详情/改角色/删除/统计)
├── common/
│   ├── request_client.py     # HTTP 请求封装
│   ├── read_json_data.py     # JSON 用例数据读取(返回 参数+用例id)
│   ├── helpers.py            # fill_sentinels 占位符替换等辅助函数
│   └── db_cleaner.py         # 测试数据清理(会话级清理 + 链路用例自愈 + 上传文件清理)
├── data/
│   ├── accounts.json         # 预置测试账号(client/merchant/admin)
│   ├── auth/                 # 认证模块用例数据(login/register/me/profile)
│   ├── reservations/         # 预定模块用例数据
│   ├── restaurants/          # 餐厅模块用例数据
│   ├── tables/               # 桌台模块用例数据
│   └── users/                # 用户管理模块用例数据
├── case/
│   ├── test_login.py         # 认证模块用例(JSON 数据驱动 + 资料链路)
│   ├── test_reservations.py  # 预定模块用例(JSON 数据驱动 + 生命周期链路)
│   ├── test_restaurants.py   # 餐厅模块用例(JSON 数据驱动 + 开店链路/级联行为)
│   ├── test_tables.py        # 桌台模块用例(JSON 数据驱动)
│   └── test_users.py         # 用户管理用例(JSON 数据驱动 + 管理链路)
├── ui/                       # UI 自动化子项目(Playwright + POM)
│   ├── conftest.py           # 复用根 fixtures;自动拉起前端;按角色注入登录态
│   ├── pages/                # 页面对象(登录/注册/餐厅列表/详情/预订)
│   ├── case/                 # P0 冒烟用例(10 条)
│   └── pytest.ini            # 失败截图 + trace + 重试
└── report/
    ├── report.html           # 接口测试报告
    ├── ui_report.html        # UI 测试报告(ui/report/ 下)
    └── server.log            # 自动拉起后端时的运行日志
```

## 运行方式

```bash
cd /mnt/resBookSys_api_test
python3 -m pytest                          # 串行运行全部接口用例(生成报告)
python3 -m pytest -v                       # 详细输出
python3 -m pytest case/test_users.py       # 只跑用户管理模块
./scripts/run_ci.sh -n auto                # 并发运行(CI 全流程模拟)
./scripts/run_ci.sh                        # 本地模拟 CI 全流程(串行)
cd ui && python3 -m pytest                 # 运行 UI 用例(自动拉起前后端)
```

- 被测服务默认 `http://localhost:5000`,可用环境变量覆盖:
  `BASE_URL=http://127.0.0.1:5000 python3 -m pytest`
- 串行模式:后端未启动时 `conftest.py` 自动拉起,结束后自动关闭;
  已在运行则直接复用、不做干预。
- 并发模式(xdist):服务生命周期由 `run_ci.sh`/CI 管理,worker 只检查就绪;
  用例按模块分配在同一 worker(`--dist=loadscope`),避免链路用例相互竞争。
- 失败自动重试:`pytest.ini` 配置 `--reruns 1`,偶发失败自动重跑一次。

## CI 集成(GitHub Actions)

`.github/workflows/api-tests.yml` 在 push/PR 时,两个 job 并行:

- **api-tests**:检出两个仓库 → 装依赖 → 重建环境(`.env` → init-db → 种子)
  → 运行 163 个接口用例 → 归档报告
- **ui-tests**:装 Playwright 浏览器 → 重建环境 → 运行 10 条 UI 用例
  (conftest 自动拉起前后端)→ 归档报告与失败截图/trace

本地可用 `./scripts/run_ci.sh` 模拟接口层流程(已在全新数据库上验证通过)。

## 覆盖范围(163 个用例)

| 模块 | 接口 | 用例数据文件 | 场景 |
| --- | --- | --- | --- |
| 认证 | POST /api/auth/login | `data/auth/login.json` | 登录成功(client/merchant)、密码错误、用户不存在、邮箱格式非法(4 种)、密码为空/缺失、邮箱缺失、空请求体 |
| 认证 | POST /api/auth/register | `data/auth/register.json` | 注册成功并立即登录、商家角色注册、邮箱重复、邮箱/密码/姓名/角色/手机号非法、缺少必填字段 |
| 认证 | GET /api/auth/me | `data/auth/me.json` | 有效 token、无 token(401)、伪造 token(403) |
| 认证 | PUT /api/auth/profile | `data/auth/profile.json` | 同名更新、姓名/手机号非法、空请求体、鉴权;另有注册→改资料→查询链路 |
| 预定 | GET/POST/PUT/DELETE /api/reservations | `data/reservations/reservations.json` | 列表(三角色+筛选)、详情(越权 404/含历史)、创建(字段校验/桌台归属/容量/时段冲突/鉴权)、改状态、取消、付款、删除、统计;另有全生命周期与取消流程两个链路用例 |
| 餐厅 | GET/POST/PUT/DELETE /api/restaurants | `data/restaurants/restaurants.json` | 列表(菜系/搜索/评分/分页)、统计、详情含桌台、可用时段、创建(13 项字段校验/权限)、更新、删除;另有开店链路(含图片上传)与删除级联行为观察两个链路用例 |
| 桌台 | GET/POST/PUT/DELETE /api/tables | `data/tables/tables.json` | 列表(按餐厅/状态/编号搜索)、详情、可用时段(含不可用时段校验)、创建(编号重复/类型/状态/归属越权)、更新、删除(有有效预订保护) |
| 用户管理 | GET/PUT/DELETE /api/users | `data/users/users.json` | 列表(筛选/搜索/权限)、详情(含预订数)、改角色(自改禁止/非法值)、删除(自删禁止/有有效预订禁止)、统计;另有注册→查询→改角色→删除链路用例 |
| UI 层 | 前端页面(P0 冒烟) | `ui/case/*.py` | 游客浏览(首页/列表/筛选/搜索/详情)、登录(成功/密码错误)、注册、预订核心链路(查时段→选时段→确认→我的预订)、取消交互(prompt)、管理后台冒烟(admin/merchant) |

## 说明

- 每个用例 JSON 的结构为 `{description, action, token, params, req_data, response}`:
  `description` 用于测试报告中的用例 id,`action` 指定调用的接口,
  `token/params/req_data` 为请求要素,`response` 为期望的状态码/消息/检查项。
- 用例数据中的占位符会在运行时替换:
  - `#unique_email#` → 随机邮箱,保证注册用例可重复执行
  - `#client_token#` / `#merchant_token#` / `#admin_token#` → 三角色真实 token
    (见 `conftest.py`,登录一次、会话内复用)
- 预置账号密码见 `data/accounts.json`(注意 admin 密码为 `admin123`,
  商家 owner 密码为 `owner123`,其余为 `password123`)。
- 测试数据自动清理:
  - 串行模式:会话开始前清残留、结束后清测试数据(链路预订按日期、
    `auto_test_%` 用户),跑多少次数据库都保持干净;
  - 并发模式:会话级清理跳过(避免 worker 竞争),链路用例自带"自愈"
    (运行前直连清理自己日期上的残留预订),注册用例用随机邮箱天然不冲突;
  - 说明:链路预订在 pending 状态下无法通过 API 删除(接口只允许删
    completed/cancelled),因此自愈采用直连 SQLite 清理。
- 说明:统计接口 `GET /stats/dashboard` 虽注册在 `GET /:id` 之后,
  但 `:id` 只匹配单段路径,`/stats/dashboard` 是两段,不会被抢先匹配,
  实测两个统计接口均正常返回 200(已纳入用例覆盖)。
