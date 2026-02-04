#!/bin/bash
echo "=== VSCode Git问题诊断 ==="
echo ""

# 1. 检查当前目录
echo "1. 当前目录: $(pwd)"
echo ""

# 2. 检查钩子状态
echo "2. Git钩子状态:"
ls -la .githooks/ 2>/dev/null || echo "无.githooks目录"
echo ""

# 3. 临时禁用钩子测试
echo "3. 临时禁用钩子..."
mv .githooks .githooks_backup 2>/dev/null || echo "无钩子目录"
echo ""

# 4. 现在去VSCode测试
echo "4. 请执行以下测试："
echo "   a. 在VSCode左侧点击「源代码管理」图标（第三个图标）"
echo "   b. 随便修改一个文件"
echo "   c. 在「消息」框中输入：测试提交"
echo "   d. 点击「✓ 提交」按钮"
echo ""
echo "5. 测试结果："
echo "   - 如果成功，说明是钩子问题"
echo "   - 如果失败，说明是VSCode配置问题"
echo ""
echo "诊断完成。按Ctrl+C退出此脚本。"
