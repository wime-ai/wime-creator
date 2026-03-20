---
name: wime-api
description: WIME AI 电商创作平台 OpenAPI。提供两个核心能力：1）抠图 — 上传本地图片（或 URL）自动抠图，返回透明背景图 URL；2）商拍图 — 自动抠图后生成多张 AI 商拍图。触发场景：用户提到抠图、商拍图、商品图、WIME、电商图片处理时激活。
---

# WIME OpenAPI

电商 AI 创作平台，提供两个核心 Skill。

## 图片来源判断（通用前置步骤）

用户输入可能是 **本地路径** 或 **URL**，两种情况统一处理为 mediaId：

```
判断用户输入:
  ├─ 本地路径 (如 /Users/.../image.jpg)
  │    → uploadImage → mediaId
  │
  └─ URL (以 http:// 或 https:// 开头)
       → 下载到本地临时文件 (/tmp/wime_download_xxx.jpg)
       → uploadImage → mediaId
       → 清理临时文件
```

**URL 下载注意事项：**
- 用 `requests.get(url, timeout=30)` 下载，保存到 `/tmp/` 下临时文件
- 从 URL 路径或 Content-Type 推断文件扩展名（默认 `.jpg`）
- 上传完成后删除临时文件
- 下载失败时直接报错，不做重试

## Skill 1：抠图

**触发词：** 抠图、去背景、透明背景、matting

**流程：** 获取图片 → 上传获取 mediaId → 调用抠图 → 返回透明背景图 URL + 图片描述

```
用户提供本地图片路径或 URL
  → [图片来源判断] → mediaId
  → cutout (mediaId) → { imageUrl, imageCaption }
```

**步骤：**
1. 判断用户输入是本地路径还是 URL（见「图片来源判断」），统一获取 `mediaId`（签名时 body 为空）
2. 调用 `cutout` 传入 `mediaId`，同步返回 `imageUrl`（抠图结果）和 `imageCaption`（图片描述）

**输出给用户：** imageUrl + imageCaption

详见 `references/upload-image.md` 和 `references/cutout.md`。

## Skill 2：商拍图

**触发词：** 商拍图、商品图、AI 商拍、产品摄影

**流程：** 获取图片 → 抠图 → 裁剪非透明区域 → 重新上传裁剪图 → 商拍图生成（4 张）→ 流式返回结果

```
用户提供本地图片路径或 URL
  → [图片来源判断] → mediaId₁
  → cutout(mediaId₁) → cutoutUrl + imageCaption
  → crop_alpha_bbox(cutoutUrl) → 本地裁剪图 (cropped.png)
  → uploadImage(cropped.png) → mediaId₂
  → cutout(mediaId₂) → croppedCutoutUrl（紧凑抠图）
  → draw (picList 使用 croppedCutoutUrl) → taskItemIds
  → getResultByBatchId 轮询 → 出一张返回一张
```

**步骤：**
1. **上传原图获取 mediaId₁**：判断用户输入是本地路径还是 URL（见「图片来源判断」），统一获取 `mediaId₁`
   - 如果用户输入是 URL，同时保留原始 URL 作为 `sourceImageUrl`
   - 如果用户输入是本地路径，上传后原图没有公开 URL，`sourceImageUrl` 后续用裁剪抠图 URL 兜底
2. **首次抠图**：调用 `cutout` 传入 `mediaId₁`，获取 `cutoutUrl` 和 `imageCaption`
3. **裁剪非透明区域**：使用 `scripts/crop_alpha.py` 的 `crop_alpha_bbox(cutoutUrl)` 下载抠图结果，裁剪出非透明像素的最小外接矩形，保存到本地临时文件。这一步去除抠图结果中多余的透明边距，让主体占满画面
4. **重新上传裁剪图获取 mediaId₂**：将裁剪后的本地 PNG 通过 `uploadImage` 上传，获取 `mediaId₂` 及裁剪后的宽高
5. **二次抠图获取干净 URL**：调用 `cutout` 传入 `mediaId₂`，获取 `croppedCutoutUrl`（紧凑的抠图 URL，用于 draw 接口）
6. **构建 `draw` 请求**：
   - `aiStyle`: True
   - `num`: 4
   - `promptAi`: ""（留空，由模型自动生成）
   - `randomStyle`: True
   - `seed`: 0
   - `picList`: 使用 `croppedCutoutUrl` 作为 `imageUrl`，原图 URL 作为 `sourceImageUrl`（本地路径时用 `croppedCutoutUrl` 兜底），**宽高使用裁剪后的尺寸**，位置和缩放按以下规则计算：

### picList 位置与缩放规则

根据**商品图裁剪后的宽高比**判断横竖版，分别计算缩放和位置：

```python
canvas_w, canvas_h = 1024, 1024  # 画布尺寸
img_w, img_h = crop_up_w, crop_up_h  # 裁剪后上传的商品尺寸

if img_w >= img_h:
    # 横版/方图商品：商品宽度 = 画布宽度 × 60%
    scale = (canvas_w * 0.6) / img_w
else:
    # 竖版商品：商品高度 = 画布高度 × 80%
    scale = (canvas_h * 0.8) / img_h

# 安全 clamp：缩放后商品不能超出画布任意一边
scale = min(scale, canvas_w / img_w, canvas_h / img_h)

# 水平方向：居中
left = (canvas_w - img_w * scale) / 2

# 垂直方向：总空白区域中，上方占 65%，下方占 35%
total_v_blank = canvas_h - img_h * scale
top = total_v_blank * 0.65
```

注意：判断横竖版的依据是**商品图裁剪后的 img_w vs img_h**，不是画布尺寸。缩放后需要 clamp 确保商品不超出画布边界。
7. 提交后获得多个 `taskItemId`
8. 轮询 `getResultByBatchId`，**每完成一张立即输出**，不等全部完成
9. **清理**：删除本地临时裁剪文件

### 裁剪脚本用法

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
# 或者用绝对路径 append
from crop_alpha import crop_alpha_bbox

# 从抠图 URL 裁剪
cropped_path, (crop_w, crop_h) = crop_alpha_bbox(cutout_url, "/tmp/wime_cropped.png")
# cropped_path: 裁剪后本地文件路径
# crop_w, crop_h: 裁剪后图片尺寸，用于 picList 的 width/height
```

### 轮询状态码（实测）

| taskStatus | 含义 |
|------------|------|
| 0 | **需区分：调度延迟 vs 真正失败**（见下方判定逻辑） |
| 1 | 执行中（未出图） |
| 2 | **完成**（result 字段有值） |
| 3 | 执行中 |
| 4 | 排队中 |

**判断完成的条件：** `taskStatus == 2 且 result 非空`。

**⚠️ taskStatus=0 的判定逻辑：**

任务生命周期中 `status=0` 有两种含义，需要根据任务是否**曾经被调度过**来区分：

1. **从未被调度过**（从提交到现在一直是 0，没出现过 1/3/4）：
   - 可能只是调度器延迟，多等几轮（建议容忍 ≥5 次）
   - 连续超过阈值仍为 0 → 判定为调度失败

2. **曾经被调度过**（历史上出现过 status=1/3/4，说明已进入执行流程）：
   - 又回到 0 → **立即判定为执行失败**（风控拦截、模型异常等）
   - 不需要等多次，因为正常流程不会从执行中回退到 0

实现要点：用 `was_scheduled` 标记跟踪每个任务是否曾出现过 1/3/4 状态。

**输出给用户：** 每张图完成时立即返回结果 URL

详见 `references/photo-shoot.md`。

---

## 环境

| 环境 | Base URL | 说明 |
|------|----------|------|
| 生产 | `https://openapi.wime-ai.com` | 线上环境（AK/SK 待配置） |

默认使用生产环境。

## 认证

所有请求需携带 `Authorization` header，由 `scripts/wime_auth.py` 生成。

签名算法：两步 HMAC-SHA256，详见脚本。

## ⚠️ 签名与请求体一致性

签名和实际发送的 HTTP body 必须逐字节一致。

```python
# ✅ 正确：用签名时同一份 body_str 发送
body_str = json.dumps(body, separators=(',',':'), sort_keys=True, ensure_ascii=False)
auth = sign(ak, sk, ts, 1800, 'POST', path, body=body_str)
resp = requests.post(url, headers={...}, data=body_str.encode('utf-8'))

# ❌ 错误：json= 序列化与签名不一致 → 验签失败
resp = requests.post(url, headers={...}, json=body)
```

图片上传 (multipart/form-data) 签名时 body 传 None。

## 接口参考

| 文件 | 说明 |
|------|------|
| `references/upload-image.md` | 图片上传 |
| `references/cutout.md` | 抠图 |
| `references/photo-shoot.md` | 商拍图 |
| `references/asset-query.md` | 资产/任务查询 |
| `references/error-codes.md` | 全局错误码 |

## 注意事项

- 图片上传有效期仅 **1 小时**
- 抠图为**同步**接口，商拍图为**异步**接口
- 商拍图轮询时出一张返回一张，不等全部完成
- QPS 限制，超限返回 errcode=1000007
