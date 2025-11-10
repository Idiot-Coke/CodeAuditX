#!/bin/bash

# 帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo "选项:"
    echo "  --help, -h            显示帮助信息"
    echo "  --start, -s           启动应用程序"
    echo "  --test, -t            运行测试脚本"
    echo "  --install, -i         安装依赖项"
}

# 安装依赖项
install_deps() {
    echo "正在安装依赖项..."
    pip install -r requirements.txt
    echo "依赖项安装完成！"
}

# 启动应用程序
start_app() {
    echo "正在启动CodeAuditX..."
    python src/main.py
}

# 运行测试（已移除，因为测试脚本已整合到应用中）
run_tests() {
    echo "警告: 测试脚本已移除。建议通过应用程序界面进行功能测试。"
    python src/main.py
}

# 处理命令行参数
if [ $# -eq 0 ]; then
    # 无参数时默认启动应用
    start_app
    exit 0
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --start|-s)
            start_app
            exit 0
            ;;
        --test|-t)
            run_tests
            exit 0
            ;;
        --install|-i)
            install_deps
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    shift

done