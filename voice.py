"""Browser-side voice input via Web Speech API.

Streamlit can't read JS values, so the component writes the transcript to
the clipboard. User then pastes (Cmd/Ctrl-V) into the textarea above.
"""
from __future__ import annotations
import streamlit.components.v1 as components


HTML = """
<style>
  .nirva-voice {
    display: inline-flex; gap: 10px; align-items: center;
    padding: 8px 14px; border: 1px solid rgba(40,30,20,0.18);
    border-radius: 999px; background: #fff; cursor: pointer;
    font-family: Inter, sans-serif; font-size: 14px; color: #1f1f1f;
    transition: all .15s;
  }
  .nirva-voice:hover { border-color: #4d6c5c; color: #4d6c5c; }
  .nirva-voice.recording { background: rgba(180,80,80,0.08); border-color: #b34a4a; color: #b34a4a; }
  .nirva-voice .dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #ccc; transition: background .15s;
  }
  .nirva-voice.recording .dot { background: #b34a4a; animation: nirva-pulse 1s infinite; }
  @keyframes nirva-pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.4 } }
  .nirva-voice-out {
    margin-top: 8px; padding: 8px 12px; min-height: 40px;
    background: #fbf9f3; border: 1px solid rgba(40,30,20,0.10);
    border-radius: 8px; font-size: 14px; color: #3d3d3d;
  }
</style>

<button class="nirva-voice" id="nirva-voice-btn">
  <span class="dot"></span>
  <span class="label">__LABEL__</span>
</button>
<div class="nirva-voice-out" id="nirva-voice-out">__PLACEHOLDER__</div>

<script>
(function() {
  const btn = document.getElementById('nirva-voice-btn');
  const out = document.getElementById('nirva-voice-out');
  const label = btn.querySelector('.label');
  const startLabel = '__LABEL__';
  const stopLabel = '__STOP_LABEL__';

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    btn.disabled = true;
    out.textContent = '__UNSUPPORTED__';
    return;
  }

  const rec = new SR();
  rec.lang = '__LANG__';
  rec.interimResults = true;
  rec.continuous = false;

  let recording = false;
  let final = '';

  btn.addEventListener('click', () => {
    if (recording) { rec.stop(); return; }
    final = '';
    rec.start();
  });

  rec.addEventListener('start', () => {
    recording = true;
    btn.classList.add('recording');
    label.textContent = stopLabel;
  });

  rec.addEventListener('end', () => {
    recording = false;
    btn.classList.remove('recording');
    label.textContent = startLabel;
    if (final) {
      navigator.clipboard.writeText(final).catch(function(){});
      out.innerHTML = '<strong>📋 ' + final + '</strong><br><small style="color:#6b6b6b">__COPIED__</small>';
    }
  });

  rec.addEventListener('result', (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        final += e.results[i][0].transcript;
      } else {
        interim += e.results[i][0].transcript;
      }
    }
    out.textContent = final + interim;
  });

  rec.addEventListener('error', (e) => {
    out.textContent = '⚠ ' + e.error;
  });
})();
</script>
"""


def render(
    label: str = "🎤 พูดได้เลย",
    stop_label: str = "⏹ หยุด",
    placeholder: str = "ข้อความจากเสียง…",
    unsupported: str = "บราวเซอร์นี้ไม่รองรับ Voice (ใช้ Chrome / Edge / Safari)",
    copied: str = "(คัดลอกแล้ว — กด ⌘V / Ctrl+V วาง)",
    lang: str = "th-TH",
    height: int = 130,
):
    html = (
        HTML
        .replace("__LABEL__", label)
        .replace("__STOP_LABEL__", stop_label)
        .replace("__PLACEHOLDER__", placeholder)
        .replace("__UNSUPPORTED__", unsupported)
        .replace("__COPIED__", copied)
        .replace("__LANG__", lang)
    )
    components.html(html, height=height)
