#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抢课助手打包脚本
用于将Python程序打包成可执行的exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示进度"""
    print(f"\n{'='*50}")
    print(f"正在执行: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*50}")
    
    try:
        # 使用gbk编码处理中文输出
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding='gbk', errors='ignore')
        print("✅ 执行成功!")
        if result.stdout:
            print("输出:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 执行失败: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False

def main():
    print("🚀 开始打包抢课助手...")
    
    # 检查源文件是否存在
    source_file = "absolute/path/to/抢课助手2.1.1.py"
    if not os.path.exists(source_file):
        print(f"❌ 源文件不存在: {source_file}")
        return False
    
    # 清理之前的构建文件
    print("\n🧹 清理之前的构建文件...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除: {dir_name}")
    
    # 删除spec文件
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.remove(spec_file)
        print(f"已删除: {spec_file}")
    
    # 使用PyInstaller打包
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",  # 打包成单个exe文件
        "--windowed",  # 不显示控制台窗口（可选）
        "--name=抢课助手",  # 指定exe文件名
        "--icon=favicon.ico",  # 使用图标文件（如果存在）
        "--add-data=favicon.ico;.",  # 包含图标文件
        "--hidden-import=playwright",
        "--hidden-import=playwright.sync_api",
        "--hidden-import=playwright._impl",
        "--collect-all=playwright",
        f'"{source_file}"'
    ]
    
    # 检查图标文件是否存在，如果不存在则移除相关参数
    if not os.path.exists("favicon.ico"):
        pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if not cmd.startswith("--icon") and not cmd.startswith("--add-data")]
    
    cmd_str = " ".join(pyinstaller_cmd)
    
    if not run_command(cmd_str, "使用PyInstaller打包程序"):
        print("❌ 打包失败!")
        return False
    
    # 检查生成的exe文件
    exe_path = os.path.join("dist", "抢课助手.exe")
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)  # 转换为MB
        print(f"\n🎉 打包成功!")
        print(f"📁 exe文件位置: {os.path.abspath(exe_path)}")
        print(f"📊 文件大小: {file_size:.2f} MB")
        
        # 创建使用说明
        readme_content = """
抢课助手 使用说明
================

1. 运行要求:
   - Windows 10/11 系统
   - 需要联网使用
   - 首次运行可能需要较长时间启动

2. 使用方法:
   - 双击 "抢课助手.exe" 运行程序
   - 按照程序提示输入用户名和密码
   - 选择课程类型并输入课程名称
   - 程序将自动搜索并尝试选课

3. 注意事项:
   - 使用前请退出正在登录的选课系统
   - 程序可能因网络问题而报错，重新运行即可
   - 账号密码输错时请重新运行程序

4. 问题反馈:
   - 如有问题请联系开发者
   

5. 免责声明:
   - 本程序仅用于学习交流使用
   - 请勿滥用此软件
   - 使用本程序产生的任何后果由用户自行承担
"""
        
        with open("dist/使用说明.txt", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print("📝 已生成使用说明文件: dist/使用说明.txt")
        
        return True
    else:
        print("❌ 未找到生成的exe文件!")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✨ 打包完成! 可以在 dist 文件夹中找到可执行文件。")
    else:
        print("\n💥 打包失败! 请检查错误信息并重试。")
    
    input("\n按 Enter 键退出...")
