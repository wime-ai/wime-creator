# 商拍图接口

## 创作商拍图

`POST /openapi/wime/1_0/draw`

### 入参

| 参数 | 类型 | 必传 | 说明 |
|------|------|------|------|
| width | Integer | 是 | 生成图片宽度（像素），示例：1024 |
| height | Integer | 是 | 生成图片高度（像素），示例：1024 |
| picList | Array\<Object\> | 是 | 图片列表，详见子参数 |
| num | Integer | 否 | 生成数量，如 num=4 则一次生成 4 张 |
| promptAi | String | 否 | AI 提示词，为空时由模型自动生成 |
| prompt | String | 否 | 正向提示词，描述期望生成内容 |
| negPrompt | String | 否 | 负向提示词，排除不希望出现的内容 |
| aiStyle | Boolean | 否 | 是否使用 AI 风格，默认 false，建议传 true |
| randomStyle | Boolean | 否 | 是否随机风格，默认 true |
| styleCode | String | 否 | 风格代码，如 "A0072" |
| referenceUrl | String | 否 | 风格参考图 URL |
| bgColor | String | 否 | 背景颜色值，如 "#FFFFFF"，空字符串表示无背景 |
| industry | String | 否 | 行业分类，如：其他、电商、餐饮等 |
| seed | Integer | 否 | 随机种子，0 表示随机，固定值可复现结果 |

### picList 子参数

| 参数 | 类型 | 必传 | 说明 |
|------|------|------|------|
| imageUrl | String | 是 | 展示图 URL（经过处理的图片，如抠图后） |
| sourceImageUrl | String | 是 | 原始图 URL（未经处理的原图） |
| width | Integer | 是 | 图片宽度（像素） |
| height | Integer | 是 | 图片高度（像素） |
| left | Float | 是 | X 轴偏移量（px） |
| top | Float | 是 | Y 轴偏移量（px） |
| scaleX | Float | 是 | X 轴缩放比例 |
| scaleY | Float | 是 | Y 轴缩放比例 |
| type | Integer | 是 | 图片类型，1=产品图 |
| imageCaption | String | 否 | 图片描述文字 |
| parentId | String | 否 | 父元素 ID，空字符串表示无父级 |

### 简易 picList 构建示例

```python
scale = min(canvas_w / img_w, canvas_h / img_h) * 0.8  # 留 20% 边距
pic_item = {
    "imageUrl": cutout_url,
    "sourceImageUrl": source_url,
    "width": img_w,
    "height": img_h,
    "left": (canvas_w - img_w * scale) / 2,
    "top": (canvas_h - img_h * scale) / 2,
    "scaleX": scale,
    "scaleY": scale,
    "type": 1,
    "imageCaption": "",
    "parentId": ""
}
```

### 出参

| 参数 | 类型 | 说明 |
|------|------|------|
| taskItemIds | List\<Long\> | 工作项 ID 列表，用于轮询异步结果 |

使用 taskItemId 作为 batchId 调用 `getResultByBatchId` 轮询，当 result 字段有值时即为结果图 URL。

### 签名注意

商拍图请求体较复杂（含中文、布尔值、嵌套 picList），**必须用签名时的 body_str 发送请求**：

```python
body_str = json.dumps(body, separators=(',',':'), sort_keys=True, ensure_ascii=False)
auth = sign(ak, sk, ts, 1800, 'POST', path, body=body_str)
# 必须用 data= 发送，不能用 json=
resp = requests.post(url, headers={'Authorization': auth, 'Content-Type': 'application/json'},
                     data=body_str.encode('utf-8'))
```

### 商拍图回调结构

```json
{
  "type": 1002,
  "taskItemId": 1000,
  "data": {
    "resultUrl": "https://xxx.png"
  }
}
```
