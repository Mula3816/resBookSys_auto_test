"""全局配置"""
import os


# 测试项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 被测后端服务地址(可用环境变量 BASE_URL 覆盖)
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# 后端源码目录(自动拉起服务时使用,可用环境变量 BACKEND_DIR 覆盖)
BACKEND_DIR = os.getenv(
    'BACKEND_DIR', '/mnt/restaurant-booking-system-master/backend')

# 认证模块路由前缀
AUTH_PATH = '/api/auth'

# 服务健康检查接口
HEALTH_PATH = '/api/health'

# 自动拉起服务后等待其就绪的超时时间(秒)
SERVER_START_TIMEOUT = 30

# 测试数据文件
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 链路用例使用的预订日期(与数据清理 fixture 保持一致,统一在此管理)
FLOW_RESERVATION_DATES = ('2026-12-20', '2026-12-21')

# UI 预订链路用例的日期
UI_BOOKING_DATE = '2026-12-22'

# 数据清理覆盖的全部测试预订日期(API 链路 + UI 链路)
CLEANUP_RESERVATION_DATES = FLOW_RESERVATION_DATES + (UI_BOOKING_DATE,)

# 被测数据库路径(测试数据自动清理用)
TEST_DB_PATH = os.path.join(BACKEND_DIR, 'database', 'restaurant.db')

# 被测系统的图片上传目录(multer 落盘位置,清理测试上传文件用)
UPLOADS_DIR = os.path.join(BACKEND_DIR, 'uploads')

# 后端服务运行日志(自动拉起时写入)
SERVER_LOG = os.path.join(BASE_DIR, 'report', 'server.log')

# ---- UI 自动化(ui/ 子项目) ----

# 前端 dev 服务地址与源码目录
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
FRONTEND_DIR = os.getenv(
    'FRONTEND_DIR', '/mnt/restaurant-booking-system-master/frontend')

# 前端服务运行日志(自动拉起时写入)
UI_SERVER_LOG = os.path.join(BASE_DIR, 'report', 'ui_server.log')
