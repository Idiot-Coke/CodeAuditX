#!/bin/bash

# macOS WeasyPrint系统依赖安装脚本
echo "开始安装WeasyPrint在macOS上所需的系统依赖..."

# 检查Homebrew是否已安装
if ! command -v brew &> /dev/null; then
    echo "错误: 未找到Homebrew。请先安装Homebrew，然后再运行此脚本。"
    echo "安装Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# 安装WeasyPrint所需的系统依赖
echo "使用Homebrew安装cairo, pango, gdk-pixbuf和libffi..."
brew install cairo pango gdk-pixbuf libffi

# 检查安装是否成功
if [ $? -eq 0 ]; then
    echo "系统依赖安装成功！"
    
    # 检查虚拟环境是否存在
    if [ -d "venv" ]; then
        echo "\n重新安装WeasyPrint以确保正确链接系统依赖..."
        source venv/bin/activate
        pip uninstall -y weasyprint
        pip install weasyprint
        
        if [ $? -eq 0 ]; then
            echo "\nWeasyPrint重新安装成功！"
            echo "\n现在您可以尝试运行项目了:"
            echo "  ./run_in_venv.sh"
            echo "或手动:"
            echo "  source venv/bin/activate"
            echo "  python src/main.py"
        else
            echo "\nWeasyPrint重新安装失败，请检查错误信息。"
        fi
    else
        echo "\n未找到虚拟环境。请先运行setup_venv.sh创建虚拟环境:"
        echo "  ./setup_venv.sh"
    fi
else
    echo "系统依赖安装失败，请检查错误信息。"
    exit 1
fi