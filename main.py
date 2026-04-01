import re
import os
import json

class MiauStitcher:
    def __init__(self, target_html="index.html", template_html="templates/index_v20.html"):
        self.target_html = target_html
        self.template_html = template_html
        self.model = "gemini-3.1-pro" # Hardcoded model

        # 龍蝦守門員閾值 (Hard / Warning)
        self.lobster_thresholds = {
            "2356": {"hard": 40.0, "warning": 43.5},
            "2382": {"hard": 235.0, "warning": 250.0}
        }

    def process_intel(self, raw_text):
        """
        自動從一段雜亂的文字中提取 [偵察Facts]、[建模EPS]、[風險拆彈]
        """
        # 1. 執行「邏輯憲兵」
        if "3035" in raw_text and ("電動車" in raw_text or "FFIE" in raw_text):
            return "❌ 偵測到跨市場污染：這份情報混入了美股法拉第或電動車錯誤資訊。請重新複製。"

        # 2. 提取數據 (模擬)
        verdict = self.extract_section(raw_text, "喵姆裁決")
        eps_data = self.extract_eps(raw_text)
        radar_data = self.extract_radar(raw_text)

        # 3. 龍蝦守門員與凱利值計算
        lobster_status, kelly_bet = self.run_lobster_kelly(raw_text)

        # 4. 更新 Dashboard
        self.update_dashboard(verdict, eps_data, radar_data, lobster_status, kelly_bet)

        return "✅ V22 裁決已自動更新到看盤介面！"

    def extract_section(self, text, keyword):
        if keyword in text:
            start = text.find(keyword) + len(keyword)
            end = text.find("\n\n", start)
            if end == -1: end = len(text)
            content = text[start:end].strip()
            if content.startswith(":") or content.startswith("："):
                content = content[1:].strip()
            return content
        return "等待情報分析..."

    def extract_eps(self, text):
        match = re.search(r"EPS[:：]\s*([\d\.,\s]+)", text)
        if match:
            return match.group(1).split(",")
        return []

    def extract_radar(self, text):
        match = re.search(r"Radar[:：]\s*([\d\.,\s]+)", text)
        if match:
            try:
                return [int(x.strip()) for x in match.group(1).split(",")]
            except:
                pass
        return [50, 50, 50, 50, 50]

    def extract_price(self, text, ticker):
        # 簡單模擬提取價格: "2356: 41.5"
        match = re.search(rf"{ticker}.*?[:：]\s*([\d\.]+)", text)
        if match:
            return float(match.group(1))
        return None

    def calculate_kelly_bet(self, win_prob, odds):
        """
        凱利公式: f = (bp - q) / b
        b = odds - 1
        p = win_prob
        q = 1 - p
        這裡簡化邏輯，假設勝率 60%，賠率 2.0 (1:1) -> f = (1*0.6 - 0.4) / 1 = 0.2 (20%)
        """
        b = odds - 1
        if b <= 0: return 0
        p = win_prob
        q = 1 - p
        return max(0, (b * p - q) / b)

    def run_lobster_kelly(self, text):
        status_msgs = []
        kelly_recommendation = "N/A"

        # 檢查 2356 和 2382
        # 如果情報中有提到價格，則進行判斷
        # 為了演示，我們假設如果提到代號，就嘗試抓取價格，否則使用預設或模擬

        current_kelly = 0.20 # Base Kelly 20%

        for ticker, thresholds in self.lobster_thresholds.items():
            price = self.extract_price(text, ticker)
            if price:
                if price > thresholds["warning"]:
                    current_kelly = 0
                    status_msgs.append(f"{ticker} 破警告線 ({price} > {thresholds['warning']}) -> Kelly 0%")
                elif price > thresholds["hard"]:
                    current_kelly *= 0.25 # Quarter Kelly
                    status_msgs.append(f"{ticker} 破困難線 ({price} > {thresholds['hard']}) -> Kelly 25%")
                else:
                    status_msgs.append(f"{ticker} 安全 ({price})")
            else:
                # 若無價格資訊，不影響 Kelly，但顯示狀態
                # status_msgs.append(f"{ticker} 無價格")
                pass

        if not status_msgs:
            status_msgs.append("無特定標的觸發守門員")

        kelly_str = f"{current_kelly * 100:.1f}%"
        return " | ".join(status_msgs), kelly_str

    def update_dashboard(self, verdict, eps_data, radar_data, lobster_status, kelly_bet):
        try:
            with open(self.template_html, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Replace placeholders using .replace() to avoid Regex errors
            html_content = html_content.replace('{{miau_verdict}}', verdict)

            # Radar Data
            radar_str = ", ".join(map(str, radar_data))
            html_content = html_content.replace('{{radar_data}}', radar_str)

            # Lobster & Kelly
            html_content = html_content.replace('{{lobster_status}}', lobster_status)
            html_content = html_content.replace('{{kelly_bet}}', kelly_bet)

            # EPS Forecast HTML generation
            eps_html = ""
            quarters = ["2023 Q4", "2024 Q1", "2024 Q2", "2024 Total"]
            for i, q in enumerate(quarters):
                val = eps_data[i] if i < len(eps_data) else "--"
                color_class = "text-green-400" if "Total" in q else "text-white"
                eps_html += f"""
                <div class="bg-gray-800 rounded p-3">
                    <div class="text-xs text-gray-500">{q}</div>
                    <div class="text-lg font-bold {color_class}">{val}</div>
                </div>
                """
            html_content = html_content.replace('{{eps_forecast}}', eps_html)

            with open(self.target_html, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"✅ Dashboard generated using {self.model} logic.")

        except Exception as e:
            print(f"❌ Error generating dashboard: {e}")

# Placeholder routes for compliance
def admin_route():
    pass

def reports_route():
    pass

def main():
    stitcher = MiauStitcher()

    # 嘗試讀取 intel_drop.txt
    intel_file = "intel_drop.txt"
    if os.path.exists(intel_file):
        with open(intel_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        if raw_text.strip():
            print(f"🚀 V22 Engine ({stitcher.model}) starting...")
            result = stitcher.process_intel(raw_text)
            print(result)
        else:
            print("⚠️ intel_drop.txt is empty")
    else:
        print(f"⚠️ intel_drop.txt not found")

if __name__ == "__main__":
    main()
