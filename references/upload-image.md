# 图片上传接口

`POST /openapi/wime/1_0/uploadImage`

Content-Type: multipart/form-data

限制: ≤20M, 格式 jpeg/jpg/png, 不能违规。上传后有效期 1h。

**签名注意:** 图片上传为 multipart/form-data，签名时 body 传空（`body=None`）。

**入参:**

| 参数 | 类型 | 必传 | 说明 |
|------|------|------|------|
| file | MultipartFile | 是 | 文件流数据 |

**出参 (data):**

| 参数 | 类型 | 说明 |
|------|------|------|
| mediaId | Long | 图片 ID |
| width | Integer | 图片宽度 |
| height | Integer | 图片高度 |

## 调用示例

```python
import requests
from wime_auth import make_request_headers

# 图片上传签名时 body_dict=None
auth = make_request_headers(
    env="ol",
    method="POST",
    uri_path="/openapi/wime/1_0/uploadImage",
    body_dict=None
)

with open("image.png", "rb") as f:
    resp = requests.post(
        f"{auth['base_url']}/openapi/wime/1_0/uploadImage",
        headers={"Authorization": auth["Authorization"]},
        files={"file": ("image.png", f, "image/png")}
    )
print(resp.json())
# {"errcode": "0", "errmsg": "ok", "data": {"mediaId": 123456, "width": 1024, "height": 1024}}
```
