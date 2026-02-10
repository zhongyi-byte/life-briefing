# 实验 #1: qLib 数据探索

## 实验目标
了解 qLib 数据层的基本结构，加载股票数据并查看统计信息。

## 代码示例

```python
import qlib
from qlib.data import D

# 初始化 qLib
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data')

# 获取股票列表
instruments = D.instruments(market='csi300')

# 加载特征数据
features = D.features(
    instruments,
    fields=['$close', '$volume', '$open', '$high', '$low'],
    start_time='2020-01-01',
    end_time='2020-12-31'
)

# 查看数据
print(f"数据形状: {features.shape}")
print(f"\n前5行:\n{features.head()}")
print(f"\n统计信息:\n{features.describe()}")
```

## 预期输出

### 数据形状
```
(73150, 5)  # 约 7万条记录，5个特征
```

### 统计信息
| 特征 | 均值 | 标准差 | 最小值 | 最大值 |
|------|------|--------|--------|--------|
| $close | 15.23 | 8.45 | 2.10 | 89.50 |
| $volume | 2345678 | 1234567 | 10000 | 9876543 |
| ... | ... | ... | ... | ... |

## 关键概念

1. **provider_uri**: 数据存储位置
2. **instruments**: 股票代码列表
3. **fields**: 特征字段（$close 收盘价等）
4. **D.features**: 核心数据加载函数

## 下一步
尝试修改时间范围或添加更多特征字段。
