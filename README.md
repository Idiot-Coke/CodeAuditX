# CodeAuditX

<div align="center">
  <strong>一个强大的多语言静态代码分析工具</strong>
  <p>提供全面的代码质量检查、许可证扫描和自定义规则支持</p>
</div>

## 项目概述

CodeAuditX是一个功能强大的静态代码分析工具，专为现代软件开发团队设计，能够帮助开发者提高代码质量、确保遵循最佳实践并识别潜在问题。通过对多种编程语言的支持，它为跨语言项目提供了统一的代码审查解决方案。

## 主要功能

- **多语言静态分析**：支持Python、JavaScript、Go、PHP、Java和C/C++等主流编程语言
- **代码质量检查**：检测代码风格问题、潜在错误和反模式
- **许可证扫描**：分析项目依赖的许可证合规性，识别潜在的许可冲突
- **自定义规则引擎**：通过配置文件轻松扩展和定制规则
- **详细报告生成**：使用WeasyPrint生成高质量PDF报告，包含违规详情和修复建议
- **跨平台支持**：支持Windows、macOS (Intel和Apple Silicon)和Linux平台
- **CI/CD集成**：可无缝集成到GitHub Actions和其他CI/CD流程中

## 支持的编程语言

- **Python**：使用pylint、flake8和pycodestyle进行代码分析
- **JavaScript**：使用esprima进行语法分析和规则检查
- **Go**：支持Go语言特有语法和最佳实践检查
- **PHP**：检查PHP代码风格和常见问题
- **Java**：分析Java代码结构和潜在问题
- **C/C++**：使用cpplint检查C/C++代码质量和风格

## 多平台支持

CodeAuditX支持以下平台，并通过GitHub Actions实现自动化构建：

- **Windows** (x86_64)：完整GUI支持
- **macOS** (x86_64)：针对Intel处理器优化
- **macOS** (arm64)：专为Apple Silicon处理器原生支持
- **Linux** (Ubuntu x86_64)：适合服务器环境使用

## 安装指南

### 使用虚拟环境（推荐）

我们提供了便捷的脚本来自动创建虚拟环境并安装所有依赖，避免与系统包产生冲突：

```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

设置完成后，使用以下命令运行项目：

```bash
./run_in_venv.sh
```

### 各平台安装详细说明

#### macOS 安装

1. **安装系统依赖**：
   ```bash
   # 使用Homebrew安装WeasyPrint所需的系统依赖
   brew install cairo pango gdk-pixbuf libffi
   ```

2. **使用便捷脚本**：
   ```bash
   # 直接运行我们提供的macOS依赖安装脚本
   chmod +x install_weasyprint_deps_macos.sh
   ./install_weasyprint_deps_macos.sh
   ```

3. **创建虚拟环境并安装依赖**：
   ```bash
   ./setup_venv.sh
   ```

#### Linux (Ubuntu/Debian) 安装

1. **安装系统依赖**：
   ```bash
   sudo apt-get update
   sudo apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
   ```

2. **创建虚拟环境并安装依赖**：
   ```bash
   ./setup_venv.sh
   ```

#### Windows 安装

1. **安装系统依赖**：
   - 使用Chocolatey安装GTK运行时：
     ```powershell
     choco install gtk-runtime
     ```
   - 或者从[GTK官方网站](https://www.gtk.org/download/windows.php)下载并安装GTK运行时

2. **使用Windows构建脚本**（推荐）：
   ```powershell
   # 以管理员权限运行PowerShell
   .\build_windows.bat
   ```

   该脚本会自动：
   - 创建虚拟环境
   - 安装所有Python依赖
   - 构建可执行文件

3. **手动安装**：
   ```powershell
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   .\venv\Scripts\activate
   
   # 升级pip并安装依赖
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 开发环境安装

如果您是开发者，想要修改或扩展项目，可以按照以下步骤设置开发环境：

```bash
# 克隆仓库
# git clone https://github.com/yourusername/CodeAuditX.git
# cd CodeAuditX

# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt

# 安装pyinstaller（用于打包）
pip install pyinstaller
```

## 使用指南

### 命令行使用

```bash
# 扫描单个文件
python -m src.main --scan path/to/file.py

# 扫描多个文件
python -m src.main --scan file1.py file2.js file3.go

# 扫描整个目录
python -m src.main --scan path/to/directory/

# 生成PDF报告
python -m src.main --scan path/to/code --output report.pdf

# 使用自定义规则
python -m src.main --scan path/to/code --config custom_rules.json

# 启用许可证扫描
python -m src.main --scan path/to/code --license-scan
```

### 使用Shell脚本

项目提供了便捷的运行脚本，可以直接使用：

```bash
chmod +x run.sh
./run.sh path/to/code
```

如果您使用虚拟环境，推荐使用：

```bash
./run_in_venv.sh
```

### 图形用户界面

CodeAuditX提供了直观的图形用户界面，您可以通过以下方式启动：

```bash
# 通过虚拟环境运行GUI
./run_in_venv.sh

# 或者直接运行（如果已安装依赖）
python src/main.py
```

在GUI中，您可以：
- 通过文件浏览器选择要扫描的文件或目录
- 配置扫描选项和规则
- 查看实时扫描结果
- 生成并保存PDF报告
- 使用规则编辑器自定义扫描规则

## PDF报告生成

CodeAuditX使用`WeasyPrint`库生成高质量PDF报告，该库提供了更好的跨平台兼容性和输出质量。

### 主要优势
- 纯Python实现，无需外部二进制文件
- 更好的跨平台兼容性，支持Windows、macOS和Linux
- 支持现代CSS特性，提供更美观的报告格式
- 简化的构建和部署流程

### 报告内容
生成的PDF报告包含：
- 项目扫描摘要（违规总数、文件数、通过/失败统计）
- 详细的违规列表，按严重程度排序
- 每个违规的行号、代码片段和修复建议
- 许可证合规性分析（如果启用）
- 按语言和规则类型的违规分布图表

## 配置

### 自定义规则
您可以在`config/custom_rules.json`文件中定义自定义规则。该工具在运行时会自动加载这些规则。

自定义规则示例：
```json
{
  "python": [
    {
      "id": "CUSTOM001",
      "pattern": "print\\(.*\\)",
      "message": "避免使用print语句进行调试",
      "severity": "warning"
    }
  ],
  "javascript": [
    {
      "id": "CUSTOM002",
      "pattern": "console\\.log\\(.*\\)",
      "message": "避免提交包含console.log的代码",
      "severity": "error"
    }
  ]
}
```

### 许可证规则
许可证扫描规则位于`src/core/config/license_rules.json`文件中，您可以根据项目需求自定义许可证兼容性规则。

## GitHub Actions 自动构建

CodeAuditX通过GitHub Actions实现了完整的自动化构建流程，支持四个平台的构建：

- Ubuntu x86_64
- Windows x86_64
- macOS 13 x86_64 (Intel)
- macOS 14 arm64 (Apple Silicon)

### 构建流程

1. **触发条件**：推送到仓库或手动触发
2. **环境准备**：
   - 安装Python 3.10
   - 安装各平台特定的系统依赖
   - 安装Python依赖包
3. **构建过程**：
   - 使用PyInstaller构建单文件可执行程序
   - 包含所有必要的数据文件和隐藏导入
   - 针对各平台添加特定配置
4. **产物上传**：
   - 自动将构建产物作为GitHub Actions Artifacts上传
   - 命名格式：`CodeAuditX-{操作系统}-{架构}`

### 手动触发构建

您可以通过GitHub仓库页面的Actions选项卡手动触发构建，这样可以在不推送代码的情况下测试构建过程。

## 故障排除

### 常见问题

#### WeasyPrint相关错误
- **症状**：报告生成失败，出现类似`Could not load library cairo`的错误
- **解决方案**：确保已正确安装所有系统依赖，按照安装指南中的步骤操作

#### PyInstaller打包问题
- **症状**：打包成功但运行时缺少模块
- **解决方案**：检查是否正确包含了所有隐藏导入，特别是WeasyPrint相关模块

#### Windows构建错误
- **症状**：在Windows上构建时出现DLL错误
- **解决方案**：确保已安装GTK运行时，并且版本兼容

#### macOS NSImage断言失败
- **症状**：在macOS上运行时出现NSImage相关断言错误
- **解决方案**：确保已安装pyobjc包，可以通过`pip install pyobjc`安装

### 日志和调试

运行时添加`--verbose`参数可以启用详细日志输出，有助于排查问题：

```bash
python -m src.main --scan path/to/code --verbose
```

## 贡献指南

我们欢迎社区贡献！如果您想为CodeAuditX做出贡献，请遵循以下步骤：

1. **Fork** 项目仓库
2. **Clone** 您的fork到本地
   ```bash
   git clone https://github.com/YOUR_USERNAME/CodeAuditX.git
   cd CodeAuditX
   ```
3. **创建** 一个新的功能分支
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **开发** 您的功能或修复
5. **测试** 您的更改
6. **提交** 您的更改
   ```bash
   git commit -m "Add some amazing feature"
   ```
7. **Push** 到分支
   ```bash
   git push origin feature/amazing-feature
   ```
8. **创建** 一个Pull Request

### 代码风格指南

- 遵循PEP 8规范（Python代码）
- 使用有意义的变量和函数名
- 添加清晰的注释
- 编写单元测试

## 许可证

CodeAuditX项目采用MIT许可证。详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- GitHub Issues：在项目仓库中创建issue
- 电子邮件：[project_email@example.com]（请替换为实际邮箱）

## 致谢

感谢所有为CodeAuditX项目做出贡献的开发者和用户！