@echo off
setlocal enabledelayedexpansion

REM 配置文件
set PROJECT_ROOT=%~dp0
set VENV_DIR=%PROJECT_ROOT%venv
set SPEC_FILE=%PROJECT_ROOT%build_windows.spec

REM 输出颜色配置
set COLOR_SUCCESS=0A
set COLOR_ERROR=0C
set COLOR_INFO=0E

:check_python
REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :print_color %COLOR_ERROR% "错误: 未找到Python。请先安装Python 3.10或更高版本。"
    exit /b 1
)

call :print_color %COLOR_INFO% "检测到Python已安装。"

REM 提示安装GTK3运行时
echo.
call :print_color %COLOR_INFO% "重要提示：在Windows上运行此应用需要GTK3运行时环境！"
call :print_color %COLOR_INFO% "请从以下地址下载并安装GTK3运行时："
call :print_color %COLOR_INFO% "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases"
call :print_color %COLOR_INFO% "推荐安装32位或64位版本，与您的系统架构匹配。"
echo.

:setup_venv
REM 创建虚拟环境
if not exist "%VENV_DIR%" (
    call :print_color %COLOR_INFO% "创建Python虚拟环境..."
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        call :print_color %COLOR_ERROR% "创建虚拟环境失败。"
        exit /b 1
    )
    call :print_color %COLOR_SUCCESS% "虚拟环境创建成功。"
)

REM 激活虚拟环境
call :print_color %COLOR_INFO% "激活虚拟环境..."
call "%VENV_DIR%\Scripts\activate"

:install_deps
REM 升级pip
call :print_color %COLOR_INFO% "升级pip..."
python -m pip install --upgrade pip

REM 安装项目依赖
call :print_color %COLOR_INFO% "安装项目依赖..."
pip install -r "%PROJECT_ROOT%requirements.txt"
pip install pyinstaller

if %errorlevel% neq 0 (
    call :print_color %COLOR_ERROR% "安装依赖失败。"
    exit /b 1
)
call :print_color %COLOR_SUCCESS% "依赖安装成功。"

REM 已迁移到WeasyPrint，不再需要wkhtmltopdf
call :print_color %COLOR_SUCCESS% "项目已使用WeasyPrint替代wkhtmltopdf。"

:build_exe
REM 执行PyInstaller打包
call :print_color %COLOR_INFO% "开始打包应用程序..."

REM 首先尝试使用spec文件
if exist "%SPEC_FILE%" (
    pyinstaller "%SPEC_FILE%"
    if %errorlevel% neq 0 (
        call :print_color %COLOR_ERROR% "使用spec文件打包失败，尝试直接打包..."
        goto fallback_build
    )
) else (
    call :print_color %COLOR_INFO% "未找到spec文件，使用直接打包方式..."
    goto fallback_build
)

goto build_complete

:fallback_build
REM 备用打包命令
pyinstaller ^
    --noconfirm ^
    --windowed ^
    --name "CodeAuditX" ^
    --collect-submodules src.rules ^
    --collect-submodules src.parsers ^
    --collect-all src.core ^
    --hidden-import src.rules.rulesets ^
    --hidden-import src.parsers.python_parser ^
    --hidden-import src.parsers.c_cpp_parser ^
    --hidden-import src.parsers.javascript_parser ^
    --hidden-import src.parsers.php_parser ^
    --hidden-import src.parsers.go_parser ^
    --hidden-import src.parsers.java_parser ^
    --hidden-import weasyprint ^
    --hidden-import weasyprint.css ^
    --hidden-import weasyprint.html ^
    --hidden-import weasyprint.layout ^
    --hidden-import weasyprint.pdf ^
    --hidden-import gi ^
    --hidden-import gi.repository ^
    --hidden-import gi.repository.GObject ^
    --hidden-import gi.repository.Gio ^
    --hidden-import gi.repository.GLib ^
    --hidden-import pydyf ^
    --hidden-import cssselect2 ^
    --hidden-import html5lib ^
    --add-data "src/core;core" ^
    --add-data "src/parsers;parsers" ^
    --add-data "src/rules;rules" ^
    --add-data "src/ui;ui" ^
    --add-data "config;config" ^
    "src/main.py"

:build_complete
if %errorlevel% neq 0 (
    call :print_color %COLOR_ERROR% "打包失败。"
    exit /b 1
)

call :print_color %COLOR_SUCCESS% "打包完成！可执行文件位于 dist\CodeAuditX.exe"
call :print_color %COLOR_INFO% "使用说明："
call :print_color %COLOR_INFO% "1. 运行 dist\CodeAuditX.exe 启动应用"
call :print_color %COLOR_INFO% "2. 确保系统已安装GTK3运行时环境"
call :print_color %COLOR_INFO% "3. 项目使用WeasyPrint 55.0版本生成PDF报告"
call :print_color %COLOR_INFO% "4. 如果遇到gobject-2.0-0.dll加载失败，请确认GTK3运行时已正确安装"
call :print_color %COLOR_INFO% "5. 如需在ARM架构的Linux上运行，可能需要特别安装WeasyPrint 55.0及相关依赖"

exit /b 0

REM 打印带颜色的文本的辅助函数
:print_color
set color=%1
shift
set "text=%~1"
for /f "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
    set "DEL=%%a"
)
<nul set /p ".=%DEL%" > "%~2"
findstr /v /a:%color% /r "^$" "%~2" nul
<nul set /p ".=%DEL%"
echo %text%
goto :eof