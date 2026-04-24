#!/usr/bin/env python3
"""
问知学苑周报创建和日程提醒 Skill
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timedelta
import argparse

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')


def load_config():
    """加载配置文件"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_command(cmd):
    """执行命令并返回结果"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"错误: {result.stderr}", file=sys.stderr)
        return None
    return json.loads(result.stdout) if result.stdout else None


def get_week_range(date=None):
    """获取指定日期所在周的日期范围（周一到周五）"""
    if date is None:
        date = datetime.now()
    
    # 获取周一
    monday = date - timedelta(days=date.weekday())
    # 获取周五
    friday = monday + timedelta(days=4)
    
    return monday, friday


def format_date_range(start_date, end_date):
    """格式化日期范围为中文格式"""
    return f"{start_date.month}月{start_date.day}日-{end_date.month}月{end_date.day}日"


def resolve_user_ids(names, config):
    """解析用户名到userId"""
    team_members = config['team_members']
    user_ids = []
    not_found = []

    for name in names:
        name = name.strip()
        if name in team_members:
            user_ids.append(team_members[name])
        else:
            not_found.append(name)

    return user_ids, not_found


def select_participants(config):
    """交互式选择参与者"""
    team_members = config['team_members']
    members_list = list(team_members.items())

    print("\n请选择参与者:")
    print("=" * 60)
    print(" 0. 全部成员（13人）")
    print("-" * 60)
    for i, (name, user_id) in enumerate(members_list, 1):
        print(f"{i:2d}. {name}")
    print("-" * 60)
    print("输入说明:")
    print("  - 输入 0 选择全部成员")
    print("  - 输入序号选择单个成员（如：1）")
    print("  - 输入多个序号用逗号分隔（如：1,3,5）")
    print("  - 完成选择后按回车确认")
    print("=" * 60)

    selected_ids = []
    selected_names = []

    while True:
        choice = input("\n请输入序号（直接回车完成选择）: ").strip()

        # 直接回车表示完成选择
        if choice == '':
            break

        # 选择全部成员
        if choice == '0':
            selected_ids = [user_id for name, user_id in members_list]
            selected_names = [name for name, user_id in members_list]
            print(f"✓ 已选择全部 {len(selected_names)} 位成员")
            break

        try:
            # 支持逗号分隔的多个选择
            indices = [int(x.strip()) for x in choice.split(',')]
            for idx in indices:
                if 1 <= idx <= len(members_list):
                    name, user_id = members_list[idx - 1]
                    if user_id not in selected_ids:
                        selected_ids.append(user_id)
                        selected_names.append(name)
                        print(f"✓ 已添加: {name}")
                    else:
                        print(f"! {name} 已在列表中")
                else:
                    print(f"! 无效的序号: {idx}")
        except ValueError:
            print("! 请输入有效的数字")

    if selected_names:
        print(f"\n已选择 {len(selected_names)} 位参与者: {', '.join(selected_names)}")

    return selected_ids, selected_names


def search_previous_report(current_start):
    """搜索上一周的周报"""
    # 计算上周的日期范围
    prev_monday = current_start - timedelta(days=7)
    prev_friday = prev_monday + timedelta(days=4)
    prev_range = format_date_range(prev_monday, prev_friday)
    
    # 搜索上周的周报
    search_query = f"问知学苑周报 {prev_range}"
    cmd = f'dws doc search --query "{search_query}" --format json'
    result = run_command(cmd)
    
    if not result or not result.get('documents'):
        # 如果找不到，尝试模糊搜索
        search_query = f"问知学苑周报 {prev_monday.month}月"
        cmd = f'dws doc search --query "{search_query}" --format json'
        result = run_command(cmd)
    
    if result and result.get('documents'):
        # 返回第一个匹配的文档
        return result['documents'][0]
    
    return None


def read_document(node_id):
    """读取文档内容"""
    cmd = f'dws doc read --node "{node_id}" --format json'
    result = run_command(cmd)
    return result.get('markdown') if result else None


def create_document(title, content, folder_id=None):
    """创建新文档"""
    cmd = f'dws doc create --name "{title}" --format json'
    if folder_id:
        cmd += f' --folder "{folder_id}"'
    
    result = run_command(cmd)
    node_id = result.get('nodeId') if result else None
    
    # 如果创建成功且有内容，更新文档内容
    if node_id and content:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_file = f.name
        
        # 使用文件重定向
        update_cmd = f'dws doc update --node "{node_id}" --markdown "$(cat {temp_file})" --mode overwrite --format json'
        run_command(update_cmd)
        
        # 删除临时文件
        os.unlink(temp_file)
    
    return node_id


def create_calendar_event(title, start_time, end_time, location=None):
    """创建日程"""
    cmd = f'dws calendar event create --title "{title}" --start "{start_time}" --end "{end_time}" --format json'
    if location:
        cmd += f' --desc "地点: {location}"'
    
    result = run_command(cmd)
    return result.get('result', {}).get('id') if result else None


def add_participants(event_id, user_ids):
    """添加日程参与者"""
    cmd = f'dws calendar participant add --event "{event_id}" --users "{user_ids}" --format json'
    result = run_command(cmd)
    return result.get('success', False)


def search_available_rooms(start_time, end_time, group_id):
    """搜索可用会议室"""
    cmd = f'dws calendar room search --start "{start_time}" --end "{end_time}" --group-id "{group_id}" --format json'
    result = run_command(cmd)
    
    if result and result.get('result', {}).get('rooms'):
        return result['result']['rooms']
    return []


def select_meeting_room(rooms):
    """交互式选择会议室"""
    if not rooms:
        return None
    
    print(f"\n找到 {len(rooms)} 个可用会议室:")
    print("-" * 80)
    for i, room in enumerate(rooms, 1):
        print(f"{i:2d}. {room['roomName']}")
        if room.get('roomLocation'):
            print(f"    位置: {room['roomLocation']}")
        if room.get('capacity'):
            print(f"    容量: {room['capacity']}人")
        print()
    print(" 0. 不预定会议室")
    print("-" * 80)
    
    while True:
        choice = input("\n请选择会议室（输入序号）: ").strip()
        
        if choice == '0':
            return None
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(rooms):
                selected_room = rooms[idx - 1]
                print(f"\n✓ 已选择: {selected_room['roomName']}")
                return selected_room
            else:
                print(f"! 无效的序号，请输入 0-{len(rooms)}")
        except ValueError:
            print("! 请输入有效的数字")


def add_meeting_room(event_id, room_id):
    """添加会议室"""
    cmd = f'dws calendar room add --event "{event_id}" --rooms "{room_id}" --format json'
    result = run_command(cmd)
    return result.get('success', False) if result else False


def main():
    parser = argparse.ArgumentParser(description='创建问知学苑周报和日程提醒')
    parser.add_argument('--date', help='指定日期 (YYYY-MM-DD)，默认为当前日期')
    parser.add_argument('--time', help='日程时间 (HH:MM-HH:MM)，默认为周五 14:00-15:00')
    parser.add_argument('--folder', help='文档所在文件夹 ID')
    parser.add_argument('--participants', help='参与者：输入"all"选择全部成员，或输入姓名（逗号分隔，如：徐赫,吴振通）')
    parser.add_argument('--room', help='会议室名称（用于自动匹配），输入"skip"跳过会议室预定')
    parser.add_argument('--skip-participants', action='store_true', help='跳过添加参与者步骤（用于分步执行）')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式（用于测试）')
    parser.add_argument('--test-user', help='测试用户（仅在非交互模式下使用）')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 解析日期
    if args.date:
        current_date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        current_date = datetime.now()
    
    # 获取本周和上周的日期范围
    monday, friday = get_week_range(current_date)
    date_range = format_date_range(monday, friday)
    
    print(f"\n{'='*80}")
    print(f"问知学苑周报创建工具")
    print(f"{'='*80}")
    print(f"\n正在创建周报: 问知学苑周报（{date_range}）")
    
    # 1. 搜索上周的周报
    print("\n步骤 1/6: 搜索上周的周报...")
    prev_report = search_previous_report(monday)
    
    if not prev_report:
        print("错误: 找不到上周的周报", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ 找到上周周报: {prev_report['name']}")
    
    # 2. 读取上周周报内容
    print("\n步骤 2/6: 读取上周周报内容...")
    content = read_document(prev_report['nodeId'])
    
    if not content:
        print("错误: 无法读取上周周报内容", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ 已读取周报内容（{len(content)} 字符）")
    
    # 3. 创建新周报
    print("\n步骤 3/6: 创建新周报...")
    new_title = f"问知学苑周报（{date_range}）"
    # 不指定folder，创建在根目录
    new_node_id = create_document(new_title, content, None)

    if not new_node_id:
        print("错误: 创建周报失败", file=sys.stderr)
        sys.exit(1)

    # 获取文档URL
    result = run_command(f'dws doc info --node "{new_node_id}" --format json')
    doc_url = result.get('docUrl') if result else None

    print(f"✓ 周报创建成功! 文档 ID: {new_node_id}")
    
    # 4. 创建日程提醒
    print("\n步骤 4/6: 创建日程提醒...")
    
    # 解析时间，默认为周五 14:00-15:00
    if args.time:
        time_parts = args.time.split('-')
        start_hour, start_minute = map(int, time_parts[0].split(':'))
        end_hour, end_minute = map(int, time_parts[1].split(':'))
    else:
        start_hour, start_minute = 14, 0
        end_hour, end_minute = 15, 0
    
    # 日程时间为周五
    event_start = friday.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    event_end = friday.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    
    # 格式化为 ISO-8601
    start_time = event_start.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    end_time = event_end.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
    event_title = f"问知学苑周报会议（{date_range}）"
    event_id = create_calendar_event(event_title, start_time, end_time, None)
    
    if not event_id:
        print("错误: 创建日程失败", file=sys.stderr)
        sys.exit(1)
    
    print(f"✓ 日程创建成功! 日程 ID: {event_id}")
    
    # 5. 选择并添加参与者
    print("\n步骤 5/6: 选择参与者...")

    team_members = config['team_members']
    selected_names = []
    user_ids = []

    if args.skip_participants:
        print("⏭️  已跳过参与者步骤（--skip-participants）")
        print(f"📋 日程 ID: {event_id}（可稍后通过 --event-id 添加参与者）")
    elif args.non_interactive and args.test_user:
        # 测试模式
        if args.test_user in team_members:
            user_ids = [team_members[args.test_user]]
            selected_names = [args.test_user]
            print(f"✓ 测试模式: 仅发送给 {args.test_user}")
        else:
            print(f"错误: 找不到测试用户 {args.test_user}", file=sys.stderr)
            sys.exit(1)
    elif args.participants:
        # 命令行参数模式
        if args.participants.lower() == 'all':
            # 选择全部成员
            user_ids = list(team_members.values())
            selected_names = list(team_members.keys())
            print(f"✓ 已选择全部 {len(selected_names)} 位成员")
        else:
            # 解析姓名列表
            names = [n.strip() for n in args.participants.split(',')]
            user_ids, not_found = resolve_user_ids(names, config)
            selected_names = [n for n in names if n in team_members]

            if not_found:
                print(f"警告: 以下人员未找到: {', '.join(not_found)}", file=sys.stderr)

            if user_ids:
                print(f"✓ 已选择 {len(user_ids)} 位参与者: {', '.join(selected_names)}")
    else:
        # 交互模式
        user_ids, selected_names = select_participants(config)

    if user_ids:
        success = add_participants(event_id, ','.join(user_ids))
        if success:
            print(f"✓ 参与者添加成功! ({len(user_ids)}人)")
        else:
            print("警告: 添加参与者失败", file=sys.stderr)
    else:
        print("提示: 未选择参与者")
    
    # 6. 搜索并选择会议室
    print("\n步骤 6/6: 搜索可用会议室...")

    # 搜索北京办公区的会议室（分组ID: 32）
    rooms = search_available_rooms(start_time, end_time, "32")

    location = None

    if args.room:
        if args.room.lower() == 'skip':
            # 明确跳过会议室预定
            print("✓ 已跳过会议室预定")
        elif not rooms:
            print(f"⚠️  警告: 该时间段没有可用的会议室，无法预定'{args.room}'")
        else:
            # 命令行参数模式：自动匹配会议室
            matched_room = None
            for room in rooms:
                if args.room in room['roomName']:
                    matched_room = room
                    break

            if matched_room:
                print(f"✓ 找到匹配的会议室: {matched_room['roomName']}")
                success = add_meeting_room(event_id, matched_room['roomId'])
                if success:
                    print(f"✓ 会议室预定成功: {matched_room['roomName']}")
                    location = matched_room['roomName']
                else:
                    print("❌ 警告: 会议室预定失败", file=sys.stderr)
            else:
                print(f"⚠️  警告: 未找到名称包含'{args.room}'的会议室")
                if rooms:
                    print(f"可用会议室: {', '.join([r['roomName'] for r in rooms[:5]])}")
    elif args.participants:
        # 有participants参数但没有room参数：显示会议室信息但不预定
        if not rooms:
            print("⚠️  该时间段没有可用的会议室")
        else:
            print(f"ℹ️  找到 {len(rooms)} 个可用会议室，但未指定会议室参数")
            print(f"   可用会议室: {', '.join([r['roomName'] for r in rooms[:5]])}")
    elif args.non_interactive:
        # 测试模式
        if rooms:
            print(f"✓ 找到 {len(rooms)} 个可用会议室（测试模式，跳过选择）")
        else:
            print("⚠️  该时间段没有可用的会议室")
    else:
        # 交互模式
        if not rooms:
            print("⚠️  该时间段没有可用的会议室")
            confirm = input("\n没有可用会议室，是否继续创建日程？(y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消创建")
                sys.exit(0)
        else:
            # 交互模式下，必须选择会议室
            print(f"⚠️  找到 {len(rooms)} 个可用会议室，请选择一个会议室")
            selected_room = select_meeting_room(rooms)

            if selected_room:
                success = add_meeting_room(event_id, selected_room['roomId'])
                if success:
                    print(f"✓ 会议室预定成功: {selected_room['roomName']}")
                    location = selected_room['roomName']
                else:
                    print("❌ 警告: 会议室预定失败", file=sys.stderr)
                    location = None
            else:
                print("⚠️  警告: 未选择会议室，日程将不包含会议室信息")
                confirm = input("\n确认不预定会议室？(y/n): ").strip().lower()
                if confirm != 'y':
                    print("已取消创建")
                    sys.exit(0)
    
    # 完成
    print(f"\n{'='*80}")
    print("✅ 周报创建和日程提醒设置完成!")
    print(f"{'='*80}")
    print(f"\n📄 周报: {new_title}")
    if doc_url:
        print(f"🔗 文档链接: {doc_url}")
    print(f"📅 日程: {event_title}")
    print(f"⏰ 时间: {event_start.strftime('%Y-%m-%d %H:%M')} - {event_end.strftime('%H:%M')}")
    if selected_names:
        print(f"👥 参与者: {', '.join(selected_names)}")
    if 'location' in locals() and location:
        print(f"📍 地点: {location}")

    # 添加移动文档提示
    target_folder = config.get('target_folder', {})
    if target_folder and doc_url:
        print(f"\n{'='*80}")
        print("⚠️  重要提示：请移动文档到目标文件夹")
        print(f"{'='*80}")
        print(f"\n📁 目标文件夹: {target_folder.get('name', '2026问知学苑周报')}")
        print(f"🔗 文件夹链接: {target_folder.get('url', '')}")
        print(f"\n操作步骤:")
        print(f"  1. 点击上方文档链接打开周报")
        print(f"  2. 点击文件夹链接打开目标文件夹")
        print(f"  3. 将周报文档拖拽到目标文件夹中")
        print(f"\n💡 提示: 由于dws工具的限制，无法自动移动文档到知识库文件夹")

    print()


if __name__ == '__main__':
    main()
