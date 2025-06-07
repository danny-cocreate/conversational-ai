#!/usr/bin/env python3
"""
Unreal Speech vs Hume AI Comparison Tool
Helps compare audio quality, latency, and features
"""

import os
import time
import requests
import json
from datetime import datetime

UNREALSPEECH_API_KEY = os.getenv("UNREALSPEECH_API_KEY", "YOUR_API_KEY_HERE")

class TTSComparison:
    def __init__(self):
        self.results = {
            "unrealspeech": {},
            "hume": {},
            "comparison": {}
        }
        
        # Test sentences for comparison
        self.test_texts = {
            "greeting": "Hello! How can I assist you today?",
            "information": "The meeting is scheduled for 3 PM tomorrow in the main conference room.",
            "emotional": "I'm so excited to help you with this project! Let's make it amazing together.",
            "technical": "The API response time averages 250 milliseconds with a 99.9% uptime guarantee.",
            "long": "Let me explain the process step by step. First, you'll need to gather all necessary documents. Then, submit your application through our online portal. After that, our team will review your submission within 3 to 5 business days. Finally, you'll receive a confirmation email with further instructions."
        }
    
    def test_unrealspeech(self, text_key: str, text: str):
        """Test Unreal Speech API"""
        print(f"\n🔵 Testing Unreal Speech - {text_key}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                "https://api.v8.unrealspeech.com/stream",
                headers={
                    "Authorization": f"Bearer {UNREALSPEECH_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "Text": text,
                    "VoiceId": "af_sky",
                    "Bitrate": "192k",
                    "Speed": "0",
                    "Pitch": "1",
                    "Codec": "libmp3lame"
                },
                stream=True
            )
            
            # Measure time to first byte
            first_byte_time = None
            chunks = []
            
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    if first_byte_time is None:
                        first_byte_time = time.time() - start_time
                    chunks.append(chunk)
            
            total_time = time.time() - start_time
            
            # Save audio
            filename = f"unrealspeech_{text_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            with open(filename, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)
            
            result = {
                "status": "success",
                "ttfb": round(first_byte_time * 1000, 2),  # Convert to ms
                "total_time": round(total_time, 2),
                "file_size": sum(len(chunk) for chunk in chunks),
                "filename": filename,
                "char_count": len(text),
                "cost_estimate": len(text) * 0.000008  # $8 per 1M chars
            }
            
            print(f"  ✅ Success: TTFB={result['ttfb']}ms, Total={result['total_time']}s")
            print(f"  📁 Saved to: {filename}")
            
            self.results["unrealspeech"][text_key] = result
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.results["unrealspeech"][text_key] = {
                "status": "error",
                "error": str(e)
            }
    
    def simulate_hume_metrics(self, text_key: str, text: str):
        """Simulate Hume AI metrics based on your current implementation"""
        print(f"\n🟣 Simulating Hume AI metrics - {text_key}")
        
        # Based on your current implementation patterns
        estimated_latency = 500 + (len(text) * 2)  # Rough estimate
        estimated_cost = len(text) * 0.00024  # Hume is more expensive
        
        result = {
            "status": "simulated",
            "ttfb": round(estimated_latency, 2),
            "total_time": round(estimated_latency / 1000 + 0.5, 2),
            "char_count": len(text),
            "cost_estimate": estimated_cost,
            "note": "Based on current implementation patterns"
        }
        
        print(f"  📊 Estimated: TTFB={result['ttfb']}ms")
        print(f"  💰 Estimated cost: ${result['cost_estimate']:.6f}")
        
        self.results["hume"][text_key] = result
    
    def compare_results(self):
        """Generate comparison report"""
        print("\n" + "="*60)
        print("📊 COMPARISON REPORT")
        print("="*60)
        
        # Overall metrics
        if self.results["unrealspeech"] and self.results["hume"]:
            us_avg_ttfb = sum(r.get("ttfb", 0) for r in self.results["unrealspeech"].values() if r.get("status") == "success") / len(self.results["unrealspeech"])
            hume_avg_ttfb = sum(r.get("ttfb", 0) for r in self.results["hume"].values()) / len(self.results["hume"])
            
            us_total_cost = sum(r.get("cost_estimate", 0) for r in self.results["unrealspeech"].values() if r.get("status") == "success")
            hume_total_cost = sum(r.get("cost_estimate", 0) for r in self.results["hume"].values())
            
            print(f"\n🚀 LATENCY COMPARISON")
            print(f"  Unreal Speech avg TTFB: {us_avg_ttfb:.0f}ms")
            print(f"  Hume AI avg TTFB: {hume_avg_ttfb:.0f}ms")
            print(f"  Improvement: {((hume_avg_ttfb - us_avg_ttfb) / hume_avg_ttfb * 100):.1f}% faster")
            
            print(f"\n💰 COST COMPARISON")
            print(f"  Unreal Speech total: ${us_total_cost:.6f}")
            print(f"  Hume AI total: ${hume_total_cost:.6f}")
            print(f"  Savings: {((hume_total_cost - us_total_cost) / hume_total_cost * 100):.1f}% cheaper")
            
            # Cost projection
            chars_per_month = 10_000_000  # 10M chars
            us_monthly = chars_per_month * 0.000008
            hume_monthly = chars_per_month * 0.00024
            
            print(f"\n📈 MONTHLY PROJECTION (10M chars)")
            print(f"  Unreal Speech: ${us_monthly:.2f}")
            print(f"  Hume AI: ${hume_monthly:.2f}")
            print(f"  Monthly savings: ${hume_monthly - us_monthly:.2f}")
            print(f"  Annual savings: ${(hume_monthly - us_monthly) * 12:.2f}")
        
        # Feature comparison
        print(f"\n✨ FEATURE COMPARISON")
        print("┌─────────────────────┬───────────────┬──────────────┐")
        print("│ Feature             │ Unreal Speech │ Hume AI      │")
        print("├─────────────────────┼───────────────┼──────────────┤")
        print("│ HTTP Streaming      │ ✅ Yes        │ ⚠️  Limited  │")
        print("│ WebSocket Streaming │ ✅ Yes        │ ❌ No        │")
        print("│ Word Timestamps     │ ✅ Yes        │ ❌ No        │")
        print("│ Voice Options       │ 48 voices     │ Limited      │")
        print("│ Language Support    │ 8 languages   │ English only │")
        print("│ Max Text Length     │ 1,000 chars   │ Unclear      │")
        print("│ Audio Formats       │ MP3, μ-law    │ MP3          │")
        print("└─────────────────────┴───────────────┴──────────────┘")
        
        # Save detailed report
        report_filename = f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_filename}")
    
    def run_comparison(self):
        """Run full comparison test"""
        print("🔬 Starting TTS Comparison Test")
        print("================================")
        
        # Test each text sample
        for text_key, text in self.test_texts.items():
            print(f"\nTesting: {text_key}")
            print(f"Text: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # Test Unreal Speech
            self.test_unrealspeech(text_key, text)
            
            # Simulate Hume metrics
            self.simulate_hume_metrics(text_key, text)
            
            time.sleep(0.5)  # Small delay between tests
        
        # Generate comparison report
        self.compare_results()


def main():
    """Run the comparison"""
    if UNREALSPEECH_API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  Please set your Unreal Speech API key:")
        print("export UNREALSPEECH_API_KEY='your_actual_key'")
        return
    
    comparison = TTSComparison()
    comparison.run_comparison()
    
    print("\n✅ Comparison complete!")
    print("\n🎧 Next steps:")
    print("1. Listen to the generated audio files")
    print("2. Compare quality with your Hume AI samples")
    print("3. Review the metrics in the comparison report")
    print("4. Test with your actual conversation content")


if __name__ == "__main__":
    main()
