#!/usr/bin/env python3
"""
生活简报生成器
自动从 Telegram 对话和 Obsidian 日志中提取数据，生成每日简报
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
OBSIDIAN_PATH = "../obsidian-sync/journals"
BRIEFINGS_PATH = "../briefings"
TEMPLATES_PATH = "../templates"
DASHBOARD_PATH = "../dashboard"

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
        
        # Count thinking depth (characters in Raw Input)
        raw_match = re.search(r'## Raw Input(.*?)## Structured', content, re.DOTALL)
        if raw_match:
            self.data["thinking_chars"] = len(raw_match.group(1).strip())
        
        # Simple mood detection
        if '积极' in content or '😊' in content:
            self.data["mood"] = "积极"
        elif '消极' in content or '沮丧' in content or '😔' in content:
            self.data["mood"] = "消极"
        else:
            self.data["mood"] = "中性"
    
    def check_principles(self):
        """检查三条原则的完成情况"""
        # Principle 1: 想法应用化 - 检查是否有新应用构建
        # This would need to be tracked manually or via commit messages
        
        # Principle 2: 余裕管理 - 需要从用户输入
        
        # Principle 3: 公开输出 - 检查本周是否有输出
        pass
    
    def generate_briefing(self):
        """生成简报 Markdown"""
        template_path = Path(TEMPLATES_PATH) / "briefing.md"
        template = template_path.read_text(encoding='utf-8')
        
        # Fill in template
        briefing = template.replace("{{date}}", self.data["date"])
        briefing = briefing.replace("{{weekday}}", self.data["weekday"])
        briefing = briefing.replace("{{sleep_rating}}", "⭐" * (self.data.get("sleep_rating", 0)))
        briefing = briefing.replace("{{sleep_hours}}", f"({self.data.get('sleep', '--')}h)" if self.data.get("sleep") else "")
        briefing = briefing.replace("{{mood_emoji}}", {"积极": "😊", "消极": "😔", "中性": "😐"}.get(self.data["mood"], "😐"))
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
        
        # Principles
        completed = sum(self.data["principles"].values())
        briefing = briefing.replace("{{principles_completed}}", str(completed))
        briefing = briefing.replace("{{principles_status}}", "✅" if completed == 3 else "⚠️")
        
        # Timestamp
        briefing = briefing.replace("{{timestamp}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return briefing
    
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
        metrics_path = Path(DASHBOARD_PATH) / "metrics.json"
        
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
        else:
            metrics = {"weekly": {"days": []}, "monthly": {"principleCompletion": {}}}
        
        # Update today's data
        metrics["today"] = {
            "date": self.date_str,
            "sleep": self.data.get("sleep"),
            "exercise": self.data.get("exercise"),
            "thinking": self.data.get("thinking_chars", 0),
            "mood": self.data["mood"],
            "principles": self.data["principles"]
        }
        
        metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"Metrics updated")


def main():
    """主函数"""
    generator = LifeBriefingGenerator()
    
    print(f"Generating briefing for {generator.date_str}...")
    
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
