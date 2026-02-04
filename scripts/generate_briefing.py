#!/usr/bin/env python3
"""
生活简报生成器
自动从 Telegram 对话和 Obsidian 日志中提取数据，生成每日简报
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
OBSIDIAN_PATH = "../obsidian-sync/journals"
BRIEFINGS_PATH = "briefings"
TEMPLATES_PATH = "templates"
DOCS_PATH = "docs"

class LifeBriefingGenerator:
    def __init__(self, date=None):
        self.date = date or datetime.now()
        self.date_str = self.date.strftime("%Y-%m-%d")
        self.date_file = self.date.strftime("%Y_%m_%d")
        self.data = {
            "date": self.date_str,
            "weekday": self._get_weekday(),
            "sleep": None,
            "exercise": None,
            "mood": None,
            "work": [],
            "insights": [],
            "outputs": [],
            "ai_collab": [],
            "principles": {
                "app": False,
                "margin": False,
                "output": False
            }
        }
    
    def _get_weekday(self):
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[self.date.weekday()]
    
    def parse_obsidian_journal(self):
        """解析 Obsidian 日志文件"""
        journal_path = Path(OBSIDIAN_PATH) / f"{self.date_file}.md"
        
        if not journal_path.exists():
            print(f"No journal found for {self.date_str}")
            return
        
        content = journal_path.read_text(encoding='utf-8')
        
        # Extract structured section
        structured_match = re.search(r'## Structured(.*)', content, re.DOTALL)
        if structured_match:
            structured = structured_match.group(1)
            
            # Extract work items
            work_items = re.findall(r'\[work\] (.+?)(?: #|$)', structured)
            self.data["work"].extend(work_items)
            
            # Extract insights
            insights = re.findall(r'\[insight\] (.+?)(?: #|$)', structured)
            self.data["insights"].extend(insights)
            
            # Extract AI collaboration
            ai_items = re.findall(r'\[ai\] (.+?)(?: #|$)', structured)
            self.data["ai_collab"].extend(ai_items)
            
            # Extract todo items
            todo_items = re.findall(r'\[todo\] (.+?)(?: #|$)', structured)
            self.data["todos"] = todo_items
        
        # Count thinking depth (characters in Raw Input)
        raw_match = re.search(r'## Raw Input(.*?)## Structured', content, re.DOTALL)
        if raw_match:
            self.data["thinking_chars"] = len(raw_match.group(1).strip())
        
        # Simple mood detection
        if '积极' in content or '😊' in content:
            self.data["mood"] = "积极"
        elif '消极' in content or '沮丧' in content or '😔' in content or '低谷' in content:
            self.data["mood"] = "消极"
        else:
            self.data["mood"] = "中性"
        
        # Extract sleep data (simple pattern matching)
        sleep_patterns = [
            r'睡眠[:：]\s*(\d+(?:\.\d+)?)\s*小时?',
            r'睡了[:：]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*小时.*睡眠',
        ]
        for pattern in sleep_patterns:
            match = re.search(pattern, content)
            if match:
                self.data["sleep"] = float(match.group(1))
                break
        
        # Extract exercise data
        exercise_patterns = [
            r'运动[:：]\s*(\d+)\s*分钟?',
            r'锻炼[:：]\s*(\d+)',
            r'健身[:：]\s*(\d+)',
        ]
        for pattern in exercise_patterns:
            match = re.search(pattern, content)
            if match:
                self.data["exercise"] = int(match.group(1))
                break
    
    def check_principles(self):
        """检查三条原则的完成情况"""
        # Principle 1: 想法应用化 - 检查是否有"构建"、"应用"、"系统"等关键词
        # This is a heuristic based on journal content
        
        # Principle 2: 余裕管理 - 需要从用户明确记录
        
        # Principle 3: 公开输出 - 检查是否有发布/输出相关记录
        pass
    
    def generate_briefing(self):
        """生成简报 Markdown"""
        template_path = Path(TEMPLATES_PATH) / "briefing.md"
        
        # Use inline template if file doesn't exist
        if template_path.exists():
            template = template_path.read_text(encoding='utf-8')
        else:
            template = self._get_default_template()
        
        # Fill in template
        briefing = template.replace("{{date}}", self.data["date"])
        briefing = briefing.replace("{{weekday}}", self.data["weekday"])
        
        # Sleep rating based on hours
        sleep_hours = self.data.get("sleep")
        sleep_rating = 0
        if sleep_hours:
            if sleep_hours >= 7.5:
                sleep_rating = 5
            elif sleep_hours >= 7:
                sleep_rating = 4
            elif sleep_hours >= 6:
                sleep_rating = 3
            elif sleep_hours >= 5:
                sleep_rating = 2
            else:
                sleep_rating = 1
        
        briefing = briefing.replace("{{sleep_rating}}", "⭐" * sleep_rating if sleep_rating else "➖")
        briefing = briefing.replace("{{sleep_hours}}", f"({sleep_hours}h)" if sleep_hours else "")
        
        mood_emoji = {"积极": "😊", "消极": "😔", "中性": "😐"}.get(self.data["mood"], "😐")
        briefing = briefing.replace("{{mood_emoji}}", mood_emoji)
        briefing = briefing.replace("{{mood_text}}", self.data["mood"])
        
        # Work items
        work_text = "\n".join([f"- {item}" for item in self.data["work"]]) if self.data["work"] else "- 无记录"
        briefing = briefing.replace("{{work_items}}", work_text)
        
        # Insights
        insights_text = "\n".join([f"- **洞察**: {item}" for item in self.data["insights"]]) if self.data["insights"] else "- 无记录"
        briefing = briefing.replace("{{insights}}", insights_text)
        
        # AI Collaboration
        ai_text = "\n".join([f"- {item}" for item in self.data["ai_collab"]]) if self.data["ai_collab"] else "- 无记录"
        briefing = briefing.replace("{{ai_collaboration}}", ai_text)
        
        # Health details
        sleep_detail = f"{sleep_hours}h" if sleep_hours else "未记录"
        briefing = briefing.replace("{{sleep_detail}}", sleep_detail)
        
        exercise = self.data.get("exercise")
        exercise_detail = f"{exercise}分钟" if exercise else "未完成 ⚠️"
        briefing = briefing.replace("{{exercise_detail}}", exercise_detail)
        
        # Outputs (combine work and AI collab as outputs)
        outputs = []
        if self.data["work"]:
            outputs.extend([f"- [工作] {item}" for item in self.data["work"]])
        if self.data["ai_collab"]:
            outputs.extend([f"- [AI协作] {item}" for item in self.data["ai_collab"]])
        outputs_text = "\n".join(outputs) if outputs else "- 无记录"
        briefing = briefing.replace("{{outputs}}", outputs_text)
        
        # Tomorrow focus (from todo items)
        todos = self.data.get("todos", [])
        if todos:
            tomorrow_text = "\n".join([f"- [ ] {item}" for item in todos[:3]])  # Top 3 todos
        else:
            tomorrow_text = "- 暂无明确计划"
        briefing = briefing.replace("{{tomorrow_focus}}", tomorrow_text)
        
        # Principles
        completed = sum(self.data["principles"].values())
        briefing = briefing.replace("{{principles_completed}}", str(completed))
        briefing = briefing.replace("{{principles_status}}", "✅" if completed == 3 else "⚠️")
        
        # Streak (placeholder - would need persistent storage)
        briefing = briefing.replace("{{streak_days}}", "1")
        briefing = briefing.replace("{{total_days}}", "1")
        
        # Timestamp
        briefing = briefing.replace("{{timestamp}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return briefing
    
    def _get_default_template(self):
        """默认简报模板"""
        return """# 生活简报 - {{date}} {{weekday}}

## 📋 今日概览
- **日期**: {{date}}
- **睡眠质量**: {{sleep_rating}} {{sleep_hours}}
- **运动**: {{exercise_detail}}
- **情绪状态**: {{mood_emoji}} {{mood_text}}
- **原则遵循**: {{principles_completed}}/3 {{principles_status}}

## 💼 工作进展
{{work_items}}

## 🧠 深度思考
{{insights}}

## 💪 健康追踪
- **睡眠**: {{sleep_detail}}
- **运动**: {{exercise_detail}}
- **饮食**: 未记录

## 📝 今日输出
{{outputs}}

## 🤖 AI 协作
{{ai_collaboration}}

## 🎯 明日关注
{{tomorrow_focus}}

## 📈 连续记录
- **当前连胜**: {{streak_days}}天
- **总记录天数**: {{total_days}}天

---

*Generated by Life Briefing System | {{timestamp}}*
"""
    
    def save_briefing(self, content):
        """保存简报到文件"""
        year = self.date.strftime("%Y")
        month = self.date.strftime("%m")
        
        briefing_dir = Path(BRIEFINGS_PATH) / year / month
        briefing_dir.mkdir(parents=True, exist_ok=True)
        
        briefing_path = briefing_dir / f"{self.date_str}.md"
        briefing_path.write_text(content, encoding='utf-8')
        
        print(f"Briefing saved to {briefing_path}")
        return briefing_path
    
    def update_metrics(self):
        """更新仪表盘指标数据"""
        metrics_path = Path(DOCS_PATH) / "metrics.json"
        
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
        else:
            metrics = {"weekly": {"days": []}, "monthly": {"principleCompletion": {}}, "history": []}
        
        # Add to history if not exists
        day_data = {
            "date": self.date_str,
            "sleep": self.data.get("sleep"),
            "exercise": self.data.get("exercise"),
            "thinking": self.data.get("thinking_chars", 0),
            "mood": self.data["mood"],
            "principles": self.data["principles"]
        }
        
        # Update or add to history
        history = metrics.get("history", [])
        existing = [i for i, h in enumerate(history) if h["date"] == self.date_str]
        if existing:
            history[existing[0]] = day_data
        else:
            history.append(day_data)
        
        metrics["history"] = history
        
        # Update today's data (most recent)
        metrics["today"] = day_data
        
        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"Metrics updated")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Generate daily life briefing')
    parser.add_argument('--date', choices=['today', 'yesterday'], default='today',
                       help='Generate briefing for which date (default: today)')
    args = parser.parse_args()
    
    # Determine target date
    if args.date == 'yesterday':
        target_date = datetime.now() - timedelta(days=1)
        print(f"Generating briefing for yesterday: {target_date.strftime('%Y-%m-%d')}")
    else:
        target_date = datetime.now()
        print(f"Generating briefing for today: {target_date.strftime('%Y-%m-%d')}")
    
    generator = LifeBriefingGenerator(date=target_date)
    
    print(f"Target date: {generator.date_str}")
    print(f"Journal file: {generator.date_file}.md")
    
    # Parse data sources
    generator.parse_obsidian_journal()
    generator.check_principles()
    
    # Generate and save
    briefing_content = generator.generate_briefing()
    generator.save_briefing(briefing_content)
    
    # Update metrics
    generator.update_metrics()
    
    print("Done!")


if __name__ == "__main__":
    main()
