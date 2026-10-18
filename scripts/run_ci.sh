#!/usr/bin/env bash
# 本地模拟 CI 全流程(与 .github/workflows/api-tests.yml 步骤一致)
# 用法:
#   ./scripts/run_ci.sh              # 串行(生成报告)
#   ./scripts/run_ci.sh -n auto      # 并发(快速反馈,服务由本脚本管理)
set -euo pipefail
cd "$(dirname "$0")/.."

BACKEND_DIR="${BACKEND_DIR:-/mnt/restaurant-booking-system-master/backend}"
BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "==> 1/5 安装测试依赖"
pip3 install -r requirements.txt -q

echo "==> 2/5 准备后端(.env + 依赖)"
[ -f "$BACKEND_DIR/.env" ] || cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
[ -d "$BACKEND_DIR/node_modules" ] || (cd "$BACKEND_DIR" && npm install)
mkdir -p "$BACKEND_DIR/uploads"   # multer 上传目录(应用启动不会自动创建)

echo "==> 3/5 启动后端服务"
if python3 -c "import urllib.request; urllib.request.urlopen('$BASE_URL/api/health', timeout=2)" 2>/dev/null; then
    echo "    服务已在运行,直接复用"
else
    (cd "$BACKEND_DIR" && nohup node server.js > /tmp/backend_ci.log 2>&1 &)
    for i in $(seq 1 30); do
        python3 -c "import urllib.request; urllib.request.urlopen('$BASE_URL/api/health', timeout=2)" 2>/dev/null && break
        sleep 1
    done
fi
trap 'pkill -f "node server.js" 2>/dev/null || true' EXIT

echo "==> 4/5 运行接口测试"
# 并发模式(-n)加 --dist=loadscope:同模块用例在同一 worker 串行,
# 保证两个链路用例(共享清理日期)不并发执行
if [[ "$*" == *"-n"* ]]; then
    set -- "$@" --dist=loadscope
fi
BASE_URL="$BASE_URL" BACKEND_DIR="$BACKEND_DIR" python3 -m pytest "$@"

echo "==> 5/5 收尾"
echo "报告: report/report.html"
