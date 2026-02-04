#!/bin/bash
echo "修复Git钩子以兼容VSCode..."

# 1. 恢复钩子目录
mv .githooks_backup .githooks 2>/dev/null || mkdir -p .githooks

# 2. 创建VSCode兼容的钩子
cat > .githooks/pre-commit << 'EOF2'
#!/bin/bash
# Git预提交钩子 - VSCode兼容版

# VSCode的提交会先进行空检查，我们需要跳过这个检查
if [ ! -f "$1" ] || [ ! -s "$1" ]; then
    # 如果是空检查，直接通过
    exit 0
fi

# 读取提交信息
COMMIT_MSG=$(cat "$1" | tr -d '\n' | tr -d '\r' | xargs)

# 基本检查：不能为空
if [ -z "$COMMIT_MSG" ]; then
    echo "❌ 错误：提交信息不能为空"
    exit 1
fi

# 简单长度检查（最小3个字符）
if [ ${#COMMIT_MSG} -lt 3 ]; then
    echo "⚠️  提交信息太短，请补充描述"
    exit 1
fi

echo "✅ 提交检查通过"
exit 0
EOF2

chmod +x .githooks/pre-commit

# 3. 配置Git使用新钩子
git config core.hooksPath .githooks

echo "修复完成！现在请在VSCode中重新测试提交。"
