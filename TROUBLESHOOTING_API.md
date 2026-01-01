# API Quota 问题排查指南

## 🔍 问题症状

```
❌ Failed to process JD
429 You exceeded your current quota
Quota exceeded for metric: generate_content_free_tier_requests
model: gemini-2.0-flash-exp
```

---

## 🎯 根本原因

### 问题 1: 使用了实验性模型

**当前配置** (有问题):
```python
MATCHING_LLM_MODEL = "gemini-2.0-flash-exp"  # 实验性模型,配额极低
```

**原因**:
- `gemini-2.0-flash-exp` 是实验性模型
- 免费层配额非常低 (每天可能只有几次调用)
- 容易超出限制

### 问题 2: JSON 解析错误

```
Failed to parse JSON: Expecting ',' delimiter
```

**原因**: LLM 返回的 JSON 格式不规范,通常在配额用完后返回错误消息而非 JSON

---

## ✅ 解决方案

### 方案 1: 更换为稳定模型 (推荐)

#### 步骤 1: 运行诊断脚本

```bash
python diagnose_api.py
```

这会测试所有可用模型并推荐最佳选择。

#### 步骤 2: 更新 config.py

打开 `config.py`,将模型改为稳定版本:

```python
# 推荐配置
RESUME_LLM_MODEL = "gemini-2.0-flash-lite"  # 或 gemini-1.5-flash
JD_LLM_MODEL = "gemini-2.0-flash-lite"
MATCHING_LLM_MODEL = "gemini-2.0-flash-lite"
```

**可用模型对比**:

| 模型 | 配额 | 速度 | 质量 | 推荐度 |
|------|------|------|------|--------|
| `gemini-2.0-flash-lite` | 高 | 快 | 良好 | ⭐⭐⭐⭐⭐ |
| `gemini-1.5-flash` | 高 | 快 | 良好 | ⭐⭐⭐⭐ |
| `gemini-1.5-pro` | 中 | 中等 | 优秀 | ⭐⭐⭐ |
| `gemini-2.0-flash-exp` | 极低 | 快 | 实验性 | ⭐ (不推荐) |

---

### 方案 2: 等待配额重置

如果你已经超出配额:

1. **每日配额**: 在 UTC 午夜重置 (北京时间早上 8:00)
2. **每分钟配额**: 等待 1 分钟后重试
3. **检查配额**: https://ai.dev/usage?tab=rate-limit

**等待时间**: 错误信息会显示:
```
Please retry in 54.932908769s
```

---

### 方案 3: 升级到付费计划

**免费层限制**:
- gemini-2.0-flash-exp: 每天 ~15 次请求
- gemini-1.5-flash: 每天 1500 次请求
- gemini-1.5-pro: 每天 50 次请求

**付费计划**:
- 访问: https://ai.google.dev/pricing
- 按使用量付费,通常很便宜
- 更高的配额和优先级

---

## 🛠️ 快速修复步骤

### 立即修复 (5 分钟)

1. **备份当前配置**:
   ```bash
   copy config.py config.py.backup
   ```

2. **更新模型配置**:
   ```python
   # 在 config.py 中修改
   RESUME_LLM_MODEL = "gemini-2.0-flash-lite"
   JD_LLM_MODEL = "gemini-2.0-flash-lite"
   MATCHING_LLM_MODEL = "gemini-2.0-flash-lite"
   ```

3. **重启应用**:
   ```bash
   streamlit run app.py
   ```

4. **测试**:
   - 上传一份简历
   - 输入一个 JD
   - 进行匹配

---

## 📊 诊断工具

### 1. 运行 API 诊断

```bash
python diagnose_api.py
```

**输出示例**:
```
✓ API Key found: AIzaSy...abc123
Testing model: gemini-2.0-flash-lite
✓ Model works: gemini-2.0-flash-lite

Testing model: gemini-2.0-flash-exp
❌ QUOTA EXCEEDED: gemini-2.0-flash-exp

RECOMMENDATION:
Update config.py to use: gemini-2.0-flash-lite
```

### 2. 检查错误日志

```bash
# Windows
type logs\errors_20260101.log | findstr "ERROR"

# 或直接查看
notepad logs\errors_20260101.log
```

查找关键错误:
- `429` - 配额超出
- `404` - 模型不存在
- `JSON parsing failed` - LLM 返回格式错误

---

## 🔄 预防措施

### 1. 使用缓存 (已实现)

系统已内置缓存,但可以调整:

```python
# config.py
ENABLE_CACHE = True  # 启用缓存
CACHE_MAX_AGE_DAYS = 30  # 缓存保留 30 天
```

### 2. 批量处理控制

处理大量简历时:

```python
# 分批处理,避免短时间大量调用
batch_size = 10  # 每次处理 10 份
delay_seconds = 2  # 每批之间等待 2 秒
```

### 3. 监控使用量

定期检查:
- https://ai.dev/usage?tab=rate-limit
- 查看 `logs/` 目录的错误日志

---

## 🚨 常见错误及解决

### 错误 1: 429 Quota Exceeded

```
❌ 429 You exceeded your current quota
```

**解决**:
1. 立即切换到 `gemini-2.0-flash-lite`
2. 或等待配额重置
3. 或升级到付费计划

---

### 错误 2: JSON Parsing Failed

```
❌ Failed to parse JSON: Expecting ',' delimiter
```

**原因**: 通常是 API 配额用完后返回错误消息而非 JSON

**解决**:
1. 检查是否超出配额
2. 切换模型
3. 优化 prompt (已优化)

---

### 错误 3: Model Not Found

```
❌ 404 Model not found: gemini-2.5-flash
```

**原因**: 模型名称错误或已废弃

**解决**: 使用经过验证的模型名称:
- `gemini-2.0-flash-lite` ✓
- `gemini-1.5-flash` ✓
- `gemini-1.5-pro` ✓

---

## 📈 性能优化建议

### 当前配置优化

```python
# 推荐配置 (已更新)
RESUME_LLM_MODEL = "gemini-2.0-flash-lite"     # 快速,配额高
JD_LLM_MODEL = "gemini-2.0-flash-lite"         # 快速,配额高
MATCHING_LLM_MODEL = "gemini-2.0-flash-lite"   # 快速,配额高

# 高质量但配额较低 (可选)
RESUME_LLM_MODEL = "gemini-1.5-pro"
JD_LLM_MODEL = "gemini-1.5-flash"
MATCHING_LLM_MODEL = "gemini-1.5-flash"
```

### 混合策略 (高级)

```python
# 简历解析用 Pro (质量优先)
RESUME_LLM_MODEL = "gemini-1.5-pro"

# JD 解析用 Flash (速度优先)
JD_LLM_MODEL = "gemini-1.5-flash"

# 匹配用 Lite (配额优先)
MATCHING_LLM_MODEL = "gemini-2.0-flash-lite"
```

---

## ✅ 验证修复

修复后,测试以下功能:

1. **上传简历**:
   ```
   ✓ Resume processed successfully
   ```

2. **输入 JD**:
   ```
   ✓ Job description analyzed
   ```

3. **匹配候选人**:
   ```
   ✓ Found 5 matching candidates
   ```

4. **检查日志**:
   ```bash
   # 应该没有 429 错误
   type logs\errors_20260101.log
   ```

---

## 📞 需要帮助?

1. **运行诊断**: `python diagnose_api.py`
2. **查看日志**: `logs/errors_*.log`
3. **检查配额**: https://ai.dev/usage
4. **文档**: https://ai.google.dev/gemini-api/docs/rate-limits

---

## 📝 总结

### 问题根源
- 使用了配额极低的实验性模型 (`gemini-2.0-flash-exp`)

### 解决方案
- 切换到 `gemini-2.0-flash-lite` (配额高,速度快)

### 预防措施
- 使用稳定模型
- 监控使用量
- 启用缓存

---

**现在就修复**:
```bash
# 1. 运行诊断
python diagnose_api.py

# 2. 已自动更新 config.py 为 gemini-2.0-flash-lite

# 3. 重启应用
streamlit run app.py
```

✅ 问题解决!
