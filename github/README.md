# FX-RV32 GitHub 仓库管理

## 仓库信息

| 项目 | 内容 |
|------|------|
| 仓库地址 | https://github.com/News111234/FX-RV32 |
| SSH 地址 | `git@github.com:News111234/FX-RV32.git` |
| 默认分支 | `master` |
| 本地路径 | `/home/yifengxin/FX-RV32_RemoveM_Custom` |
| 创建日期 | 2026-06-08 |

---

## 一、仓库建立方式（记录）

### 1. 本地初始化

```bash
cd /home/yifengxin/FX-RV32_RemoveM_Custom
git init
git config user.name "Yi Fengxin"
git config user.email "1596215367@qq.com"
```

### 2. 创建 .gitignore

排除编译产物（Verilator `obj_dir/`、Modelsim `work/`、Vivado `.runs/` 等）、个人文件（`.docx` 面试文档等）、Python 缓存。

### 3. SSH Key 配置

由于 WSL 环境中 HTTPS 443 端口不可用，采用 SSH 方式连接 GitHub：

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "1596215367@qq.com" -f ~/.ssh/id_ed25519

# 添加 GitHub 主机密钥
ssh-keyscan github.com >> ~/.ssh/known_hosts

# 将公钥上传到 GitHub（浏览器操作）
# https://github.com/settings/keys → New SSH Key
```

### 4. 推送

```bash
git remote add origin git@github.com:News111234/FX-RV32.git
git push -u origin master
```

---

## 二、日常更新流程

### 快速更新（改了文件就推）

```bash
cd /home/yifengxin/FX-RV32_RemoveM_Custom

# 1. 查看改了哪些文件
git status

# 2. 将所有改动加入暂存
git add -A

# 3. 提交（写明改了什么）
git commit -m "描述你的改动"

# 4. 推送到 GitHub
git push
```

### 一行搞定（改动不多时）

```bash
cd /home/yifengxin/FX-RV32_RemoveM_Custom && git add -A && git commit -m "更新" && git push
```

---

## 三、常见场景

### 场景 1：修改了某个文件，想上传

```bash
cd /home/yifengxin/FX-RV32_RemoveM_Custom
git add core/exu/alu.v          # 只添加改动的文件
git commit -m "fix: 修复 ALU AUIPC bug，使用正确的 PC 值"
git push
```

### 场景 2：新增了文件/文件夹

```bash
git add path/to/new_file.v      # 添加新文件
git commit -m "feat: 添加 xxx 模块"
git push
```

### 场景 3：删除了一些文件

```bash
git add -A                       # -A 会自动跟踪删除操作
git commit -m "chore: 清理无用文件"
git push
```

### 场景 4：改了多个文件，想分开提交

```bash
git add core/exu/alu.v
git commit -m "fix: 修复 AUIPC bug"
git add doc/auipc_bug_analysis.md
git commit -m "doc: 更新 AUIPC bug 分析文档"
git push
```

### 场景 5：刚才的提交写错了，想改 commit message

```bash
git commit --amend -m "新的 commit message"
git push --force-with-lease     # 注意：只有你自己用这个仓库时才安全
```

### 场景 6：查看提交历史

```bash
git log --oneline -10            # 最近 10 条，简洁模式
git log --oneline --graph        # 带分支图
```

---

## 四、commit message 建议

英文或中文都行，推荐格式：

```
<类型>: <简短描述>

类型可选：
  feat     新功能
  fix      修 bug
  doc      文档更新
  refactor 重构（不改变功能）
  chore    杂项（清理、配置等）
  test     测试相关

示例：
  feat: 添加硬件乘法器模块
  fix: 修复 load-use 停顿重复执行 bug
  doc: 更新 README 外设寄存器映射表
  refactor: 优化 forwarding_unit 转发优先级
```

---

## 五、注意事项

1. **推送前先 `git status`** — 确认没有不该提交的文件（如面试文档、临时文件）
2. **不要提交编译产物** — `.gitignore` 已配置排除 `obj_dir/`、`work/`、`*.dcp` 等，新增编译产物目录时记得更新 `.gitignore`
3. **大文件 (>1MB)** — 尽量不要提交二进制大文件到 Git，考虑用 Git LFS 或其他方式管理
4. **敏感信息** — 绝对不要提交密码、token、私钥等
5. **SSH 连接测试** — 如果推送失败，先测试 SSH：
   ```bash
   ssh -T git@github.com    # 应显示 "Hi News111234! ..."
   ```
