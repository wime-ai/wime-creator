# 用户资产 & 任务查询

## 获取用户剩余资产

`POST /openapi/wime/1_0/asset`

无需入参。

**出参 (data):**

| 参数 | 类型 | 说明 |
|------|------|------|
| type | Int | 资产类型 |
| subType | Int | 子资产类型 |
| count | Long | 资产数量 |
| expireTime | Date | 过期时间 |

## 根据批次 ID 查询创作结果

`POST /openapi/wime/1_0/getResultByBatchId`

**入参:**

| 参数 | 类型 | 必传 | 说明 |
|------|------|------|------|
| batchId | Long | 是 | 批次 ID |

**出参 (data):**

| 参数 | 类型 | 说明 |
|------|------|------|
| batchId | Long | 批次 ID |
| taskStatus | Integer | 0=执行失败, 1=执行中, 2=完成（result 有值）, 3=执行中, 4=排队中 |
| result | String | 创作结果 JSON |
| type | String | 创作类型 |
