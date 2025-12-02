#!/bin/bash
# -*- coding: utf-8 -*-
"""
设置虚拟环境并安装项目依赖，避免与系统包冲突
"""

echo "=== 设置项目虚拟环境 ==="

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "当前Python版本: $PYTHON_VERSION"

# 删除已存在的虚拟环境（可选）
if [ -d "venv" ]; then
    echo "删除已存在的虚拟环境..."
    rm -rf venv
fi

# 创建新的虚拟环境
echo "创建虚拟环境 venv..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 更新pip
echo "更新pip..."
pip install --upgrade pip

# 安装项目依赖
echo "安装项目依赖..."
pip install -r requirements.txt

# 检查安装状态
echo "\n=== 安装状态检查 ==="
pip show weasyprint

# 创建启动脚本
echo "\n=== 创建项目启动脚本 ==="
cat > run_in_venv.sh << 'EOF'
#!/bin/bash
# 激活虚拟环境并运行项目
source venv/bin/activate
python src/main.py
EOF

chmod +x run_in_venv.sh

echo "\n=== 设置完成 ==="
echo "请使用以下命令运行项目："
echo "./run_in_venv.sh"
echo "\n或者手动激活虚拟环境："
echo "source venv/bin/activate"
echo "python src/main.py"
echo "\n注意：使用虚拟环境可以避免与系统包的依赖冲突。"