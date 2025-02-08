#!/bin/bash

# 定义帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -i, --install     安装依赖"
    echo "  -g, --generate    生成图标"
    echo "  -c, --clean       清理生成的文件和目录"
    echo "  -s, --svg FILE    指定SVG源文件路径"
    echo "  -h, --help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  1. 安装所有依赖:"
    echo "     $0 -i"
    echo ""
    echo "  2. 使用默认SVG文件生成图标:"
    echo "     $0 -g"
    echo ""
    echo "  3. 指定SVG文件生成图标:"
    echo "     $0 -g -s custom_icon.svg"
    echo ""
    echo "  4. 同时安装依赖并生成图标:"
    echo "     $0 -i -g"
    echo ""
    echo "  5. 完整示例(自定义SVG):"
    echo "     $0 -g -s path/to/icon.svg"
}

# 默认值
INSTALL_DEPS=false
GENERATE_ICONS=false
CLEAN_FILES=false
SVG_FILE="icon.svg"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--install)
            INSTALL_DEPS=true
            shift
            ;;
        -c|--clean)
            CLEAN_FILES=true
            shift
            ;;
        -g|--generate)
            GENERATE_ICONS=true
            shift
            ;;
        -s|--svg)
            SVG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "错误: 未知参数 $1"
            show_help
            exit 1
            ;;
    esac
done

# 安装依赖
if [ "$INSTALL_DEPS" = true ]; then
    echo "正在安装依赖..."
    pip3 install pyinstaller
    pip3 install dmgbuild
    pip install Pillow
    pip install cairosvg
    brew install cairo
    brew install inkscape
fi

# 生成图标
if [ "$GENERATE_ICONS" = true ]; then
    echo "正在生成图标..."
    # 确保输出目录存在
    mkdir -p "icon.iconset"
    
    # 定义图标尺寸数组
    sizes=(16 32 64 128 256 512 1024)
    
    # 循环生成不同尺寸的图标
    for size in "${sizes[@]}"; do
        echo "生成 ${size}x${size} 图标..."
        inkscape --export-type=png --export-filename="icon.iconset/icon_${size}x${size}.png" -w $size -h $size "$SVG_FILE"
    done

    # 使用iconutil生成icns文件
    echo "正在生成icns文件..."
    iconutil -c icns icon.iconset
    echo "图标生成完成"
fi

# 清理文件和目录
if [ "$CLEAN_FILES" = true ]; then
    echo "正在清理文件和目录..."
    # 清理图标相关文件
    rm -rf "icon.iconset"
    rm -f "icon.icns"
    # 清理打包产物
    rm -rf "build"
    rm -rf "dist"
    rm -f "*.spec"
    rm -f "*.dmg"
    # 清理Python缓存文件
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    echo "清理完成"
fi

# 如果没有指定任何操作，显示帮助信息
if [ "$INSTALL_DEPS" = false ] && [ "$GENERATE_ICONS" = false ] && [ "$CLEAN_FILES" = false ]; then
    show_help
    exit 1
fi