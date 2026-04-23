---
name: weekly-report
description: 创建问知学苑周报文档和日程提醒
trigger: 当用户要创建周报、周报提醒、周报会议时使用
---

# 问知学苑周报创建工具

自动创建问知学苑周报文档并设置日程提醒。

## 触发条件

当用户说以下内容时，应该使用此 skill：
- "创建本周周报"
- "创建周报提醒"
- "创建周报会议"
- "设置周报日程"
- "问知学苑周报"

## 使用方法

```bash
python3 create_weekly_report.py [选项]
```

## 主要功能

1. 自动搜索并复制上周周报内容
2. 创建新的周报文档
3. 创建日程提醒（包含钉钉视频会议链接）
4. 交互式选择参与者（已预配置13位团队成员）
5. 交互式选择会议室（搜索北京办公区空闲会议室）

## 预配置的团队成员

- 吴丛郁、李树成、段浩文、黄志香
- 郭凯频、徐赫、刘子阳、杨益鸣
- 吴振通、王嘉琳、朱昱嘉、王煜杰、聂万凯

**无需查询 userId，直接使用姓名即可！**

## 参数

- `--date`: 指定日期 (YYYY-MM-DD)
- `--time`: 日程时间 (HH:MM-HH:MM)，默认 14:00-15:00
- `--non-interactive`: 非交互模式
- `--test-user`: 测试用户姓名

## 示例

### 交互式创建周报
```bash
python3 create_weekly_report.py
```

### 测试模式（仅发送给指定用户）
```bash
python3 create_weekly_report.py --non-interactive --test-user "吴丛郁"
```

### 指定时间
```bash
python3 create_weekly_report.py --time "14:00-15:00"
```
