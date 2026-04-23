# 钉钉周报创建 Skill

自动创建钉钉周报文档并设置日程提醒的 Claude Code Skill。

## 功能特性

- ✅ 自动搜索上一周的周报并复制内容
- ✅ 创建新的周报文档
- ✅ 创建日程提醒（自动包含钉钉视频会议链接）
- ✅ 交互式选择参与者（支持全部成员或自定义选择）
- ✅ 自动搜索并预定会议室
- ✅ 预配置团队成员信息（无需查询 userId）

## 安装

使用 npx skills 安装：

```bash
npx skills add git@github.com:yimingy72/dingtalk-weekly-report-skill.git
```

或使用 HTTPS：

```bash
npx skills add https://github.com/yimingy72/dingtalk-weekly-report-skill.git
```

## 使用方法

安装后，直接通过自然语言触发 skill：

```
创建钉钉本周周报提醒，周五14:00-15:00
```

或者：

```
创建周报提醒
```

Claude 会引导你完成以下步骤：

1. **选择参与者**
   - 选择"全部成员"邀请所有团队成员
   - 或选择"自定义选择"，通过编号选择特定成员

2. **选择会议室**
   - 自动搜索可用会议室
   - 选择是否需要预定会议室

3. **自动完成**
   - 创建周报文档
   - 创建日程提醒
   - 添加参与者
   - 预定会议室（如果选择）

## 配置

首次使用前，需要配置团队成员信息。编辑 `config.json` 文件：

```json
{
  "team_members": {
    "成员1": "user_id_1",
    "成员2": "user_id_2",
    ...
  },
  "meeting_room_group_id": "32",
  "target_folder": {
    "name": "周报文件夹名称",
    "node_id": "文件夹ID",
    "url": "文件夹URL"
  }
}
```

### 获取用户 ID

使用 dws 命令查询用户 ID：

```bash
dws contact user search --keyword "姓名" --format json
```

### 获取文件夹信息

使用 dws 命令查询文件夹信息：

```bash
dws doc search --query "文件夹名称" --format json
dws doc info --node "文件夹ID" --format json
```

## 前置要求

- 已安装并登录 [dws](https://github.com/your-org/dws) 工具
- 有权限访问钉钉文档和日历
- Python 3.x

## 工作流程

1. 📋 搜索上一周的周报文档
2. 📄 读取上周周报内容
3. ✍️ 创建新的周报文档
4. 📅 创建日程提醒（自动生成钉钉视频会议链接）
5. 👥 添加参与者
6. 🏢 搜索并预定会议室（可选）

## 注意事项

- 文档创建后需要手动移动到目标文件夹（由于 API 限制）
- 会议室搜索范围为配置的会议室分组
- 日程会自动包含钉钉视频会议链接
- 参与者会收到日程邀请通知

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request。
