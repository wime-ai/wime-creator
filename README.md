# wime-creator

WIME AI 是面向中小微电商从业者的多模态 AI 内容创作平台，专为电商和新媒体场景设计。  
本目录提供 WIME OpenAPI 的常用能力说明与调用参考，重点覆盖：

- 图片上传（获取 `mediaId`）
- 抠图（返回透明背景图）
- 商拍图生成（异步任务，逐张出图）

## 目录结构

- `references/upload-image.md`：上传图片接口
- `references/cutout.md`：抠图接口
- `references/photo-shoot.md`：商拍图接口
- `references/asset-query.md`：任务/资产查询
- `references/error-codes.md`：错误码说明
- `scripts/wime_auth.py`：签名与请求头生成
- `scripts/crop_alpha.py`：透明边裁剪脚本（商拍图流程可用）

## 接口环境

- 生产环境 Base URL：`https://openapi.wime-ai.com`
- 可通过环境变量覆盖：`WIME_BASE_URL`

## AK/SK 获取方式

在调用 API 前，需要先获取 OpenAPI 的访问凭证 `AK` / `SK`。

推荐流程：

1. 访问 `https://wime.ai`
2. 登录你的 WIME 账号（无账号先注册）
3. 进入 OpenAPI / 开放平台 / API Key 管理页面
4. 创建或查看你的 `AK` 和 `SK`
5. 将 `AK/SK` 保存到本地环境变量（不要硬编码到代码）

如果你当前环境未配置 `WIME_AK` / `WIME_SK`，接口会因为签名凭证缺失而无法调用。

## 本地配置

```bash
export WIME_AK='你的AK'
export WIME_SK='你的SK'
export WIME_BASE_URL='https://openapi.wime-ai.com'  # 可选
```

也可以仅对单次命令生效：

```bash
WIME_AK='你的AK' WIME_SK='你的SK' python3 your_script.py
```

## 认证与签名

所有请求都必须携带 `Authorization`，签名逻辑见 `scripts/wime_auth.py`。  
签名核心是两步 HMAC-SHA256，最终格式：

`ak-v1/{ak}/{timestamp}/{expiration}/{signature}`

## 关键注意事项

### 1) 签名和请求体必须逐字节一致

若签名时使用了某个 `body_str`，发送请求时必须发送同一份字节内容。  
不要用会自动重新序列化的方式导致验签不一致。

### 2) 上传接口（multipart/form-data）签名 body 传空

文件上传时通常不传 JSON body 参与签名。

### 3) 时效与调用特性

- 上传后的资源有效期约 1 小时
- 抠图接口为同步返回
- 商拍图接口为异步任务，建议轮询并逐张返回结果

## 快速示例（生成签名头）

```python
from scripts.wime_auth import make_request_headers

headers = make_request_headers(
    env="ol",
    method="POST",
    uri_path="/openapi/wime/1_0/asset",
    body_dict={"foo": "bar"}
)

base_url = headers["base_url"]
authorization = headers["Authorization"]
body_str = headers["body_str"]
```

如果 `WIME_AK/WIME_SK` 未配置，`make_request_headers` 会直接抛错提示凭证缺失。
