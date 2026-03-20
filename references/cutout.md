# 抠图接口

`POST /openapi/wime/1_0/cutout`

**同步接口**，直接返回抠图结果。

**入参:**

| 参数 | 类型 | 必传 | 说明 |
|------|------|------|------|
| imageUrl | String | 条件必传 | 图片 URL（imageUrl 和 mediaId 必须存在一个） |
| mediaId | Long | 条件必传 | 图片 ID（通过 uploadImage 获取） |

**出参 (data):**

| 参数 | 类型 | 说明 |
|------|------|------|
| imageUrl | String | 抠图结果 URL |
| imageCaption | String | 图片描述 |

## 调用示例

```python
import requests, json
from wime_auth import make_request_headers

body = {"mediaId": 123456}
auth = make_request_headers(
    env="ol",
    method="POST",
    uri_path="/openapi/wime/1_0/cutout",
    body_dict=body
)

resp = requests.post(
    f"{auth['base_url']}/openapi/wime/1_0/cutout",
    headers={
        "Authorization": auth["Authorization"],
        "Content-Type": "application/json"
    },
    json=body
)
print(resp.json())
# {"errcode": "0", "errmsg": "ok", "data": {"imageUrl": "https://...", "imageCaption": "A white product"}}
```

## 典型使用流程

1. 调用 `uploadImage` 上传原图 → 获得 `mediaId`
2. 调用 `cutout` 传入 `mediaId` → 获得抠图结果 `imageUrl`
3. 抠图结果可用于商拍图等后续创作
