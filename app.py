import os

import gradio as gr
import base64
from pdf_processor import PDFProcessor
from llm_client import ClaudeClient

# ── Logo ──────────────────────────────────────────────────────────────────────
with open("logo_transparent.png", "rb") as f:
    LOGO_B64 = base64.b64encode(f.read()).decode()
LOGO_SRC = f"data:image/png;base64,{LOGO_B64}"

processor         = PDFProcessor()
report_text_state = {}

# ── Functions ─────────────────────────────────────────────────────────────────
def analyze_report(pdf_file):
    if not pdf_file:
        return (
            error_box("Please upload a PDF file first."),
            "", "", "", gr.update(visible=False)
        )
    try:
        text = processor.extract_text(pdf_file.name)
        meta = processor.get_metadata(pdf_file.name)

        if len(text.strip()) < 50:
            return (
                error_box("Could not read this PDF. Make sure it's a text-based PDF, not a scanned image."),
                "", "", "", gr.update(visible=False)
            )

        report_text_state["text"] = text

        client = ClaudeClient()
        result = client.summarize_report(text)

        status_colors = {
            "All Normal":             "#22c55e",
            "Mostly Normal":          "#eab308",
            "Attention Needed":       "#f97316",
            "Urgent Review Required": "#ef4444",
        }
        status_icons = {
            "All Normal":             "✅",
            "Mostly Normal":          "🟡",
            "Attention Needed":       "🟠",
            "Urgent Review Required": "🔴",
        }
        status       = result.get("overall_status", "Unknown")
        status_color = status_colors.get(status, "#94a3b8")
        status_icon  = status_icons.get(status, "📋")
        report_type  = result.get("report_type", "Medical Report")

        meta_html = f"""
        <div style='display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;animation:fadeIn 0.5s ease'>
          <div style='background:#1e293b;border-radius:10px;padding:12px 16px;
                      border-left:3px solid #f7941d;flex:1'>
            <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:1px'>
              Report Type</div>
            <div style='color:#e2e8f0;font-weight:600;font-size:15px;margin-top:3px'>
              {report_type}</div>
          </div>
          <div style='background:#1e293b;border-radius:10px;padding:12px 16px;
                      border-left:3px solid #1a6fb5'>
            <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:1px'>
              Pages</div>
            <div style='color:#e2e8f0;font-weight:600;font-size:15px;margin-top:3px'>
              {meta["pages"]}</div>
          </div>
          <div style='background:#1e293b;border-radius:10px;padding:12px 16px;
                      border-left:3px solid #1a6fb5'>
            <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:1px'>
              Words</div>
            <div style='color:#e2e8f0;font-weight:600;font-size:15px;margin-top:3px'>
              {meta["words"]:,}</div>
          </div>
          <div style='background:#1e293b;border-radius:10px;padding:12px 16px;
                      border-left:3px solid {status_color};flex:1;text-align:center'>
            <div style='color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:1px'>
              Overall Status</div>
            <div style='color:{status_color};font-weight:700;font-size:15px;margin-top:3px'>
              {status_icon} {status}</div>
          </div>
        </div>"""

        summary_en = result.get("summary_en", "")
        summary_ar = result.get("summary_ar", "")
        summary_html = f"""
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;animation:fadeIn 0.6s ease'>
          <div style='background:#1e293b;border-radius:12px;padding:18px;border-top:3px solid #f7941d'>
            <div style='color:#f7941d;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:1px;margin-bottom:10px'>🇬🇧 English Summary</div>
            <div style='color:#e2e8f0;font-size:14px;line-height:1.8'>{summary_en}</div>
          </div>
          <div style='background:#1e293b;border-radius:12px;padding:18px;border-top:3px solid #1a6fb5;
                      direction:rtl;text-align:right'>
            <div style='color:#60a5fa;font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:1px;margin-bottom:10px'>🇪🇬 الملخص بالعربي</div>
            <div style='color:#e2e8f0;font-size:14px;line-height:1.8'>{summary_ar}</div>
          </div>
        </div>"""

        red_flags = result.get("red_flags", [])
        if red_flags:
            severity_colors = {
                "mild":     "#eab308",
                "moderate": "#f97316",
                "severe":   "#ef4444",
            }
            flags_html = "<div style='display:flex;flex-direction:column;gap:10px;animation:fadeIn 0.7s ease'>"
            for flag in red_flags:
                sev   = flag.get("severity", "mild").lower()
                color = severity_colors.get(sev, "#f97316")
                flags_html += f"""
                <div style='background:#140a0a;border:1px solid {color}44;
                            border-left:4px solid {color};border-radius:12px;padding:16px'>
                  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
                    <span style='color:{color};font-weight:700;font-size:15px'>
                      ⚠️ {flag.get("finding","")}</span>
                    <span style='background:{color}22;color:{color};padding:3px 12px;
                                 border-radius:20px;font-size:11px;font-weight:700;
                                 text-transform:uppercase'>{sev}</span>
                  </div>
                  <div style='display:flex;gap:20px;margin-bottom:10px'>
                    <span style='color:#94a3b8;font-size:13px'>
                      Measured: <strong style='color:#e2e8f0'>{flag.get("value","")}</strong></span>
                    <span style='color:#94a3b8;font-size:13px'>
                      Normal: <strong style='color:#22c55e'>{flag.get("normal_range","")}</strong></span>
                  </div>
                  <div style='color:#cbd5e1;font-size:13px;line-height:1.7;
                              background:#ffffff07;border-radius:8px;padding:10px'>
                    💬 {flag.get("plain_explanation","")}</div>
                </div>"""
            flags_html += "</div>"
        else:
            flags_html = """
            <div style='background:#071a07;border:1px solid #22c55e44;border-radius:12px;
                        padding:20px;text-align:center;animation:fadeIn 0.7s ease'>
              <div style='font-size:32px;margin-bottom:8px'>✅</div>
              <div style='color:#22c55e;font-weight:700;font-size:15px'>No abnormal findings</div>
              <div style='color:#64748b;font-size:13px;margin-top:4px'>
                All reviewed values appear within normal range</div>
            </div>"""

        findings = result.get("key_findings", [])
        findings_html = "<div style='display:flex;flex-direction:column;gap:8px;animation:fadeIn 0.8s ease'>"
        for f in findings:
            findings_html += f"""
            <div style='display:flex;gap:10px;align-items:flex-start;
                        background:#1e293b;border-radius:10px;padding:12px 16px'>
              <span style='color:#f7941d;font-size:18px'>•</span>
              <span style='color:#e2e8f0;font-size:14px;line-height:1.6'>{f}</span>
            </div>"""
        findings_html += "</div>"

        followup        = result.get("follow_up_suggested", False)
        followup_reason = result.get("follow_up_reason", "")
        if followup:
            followup_html = f"""
            <div style='background:#1a1500;border:1px solid #f7941d55;border-radius:12px;
                        padding:16px 20px;margin-top:12px;display:flex;gap:12px;align-items:flex-start'>
              <span style='font-size:24px'>📅</span>
              <div>
                <div style='color:#f7941d;font-weight:700;font-size:14px;margin-bottom:4px'>
                  Follow-up Recommended</div>
                <div style='color:#fcd34d;font-size:13px;line-height:1.6'>{followup_reason}</div>
              </div>
            </div>"""
        else:
            followup_html = """
            <div style='background:#071a07;border:1px solid #22c55e44;border-radius:10px;
                        padding:12px 16px;margin-top:12px;display:flex;gap:10px;align-items:center'>
              <span style='font-size:20px'>✅</span>
              <span style='color:#22c55e;font-size:14px'>
                No immediate follow-up required based on this report</span>
            </div>"""

        return (
            meta_html,
            summary_html,
            flags_html,
            findings_html + followup_html,
            gr.update(visible=True)
        )

    except Exception as e:
        return (
            error_box(f"Something went wrong: {str(e)}"),
            "", "", "", gr.update(visible=False)
        )


def chat_fn(message, history):
    if not report_text_state.get("text"):
        history.append((message, "⚠️ Please upload and analyze a report first."))
        return history, ""
    try:
        client = ClaudeClient()
        answer = client.answer_question(report_text_state["text"], message, history)
        history.append((message, answer))
    except Exception as e:
        history.append((message, f"❌ Error: {str(e)}"))
    return history, ""


def error_box(msg):
    return f"""
    <div style='background:#2d1515;border:1px solid #ef444466;border-radius:12px;
                padding:16px 20px;display:flex;gap:12px;align-items:flex-start'>
      <span style='font-size:22px'>🚫</span>
      <div style='color:#fca5a5;font-size:14px;line-height:1.6'>{msg}</div>
    </div>"""


css = """
@keyframes fadeIn {
  from { opacity:0; transform:translateY(10px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 0 #f7941d44; }
  50%      { box-shadow: 0 0 0 10px #f7941d00; }
}
* { box-sizing: border-box; }
body, .gradio-container {
    background: #0a0f1e !important;
    color: #e2e8f0 !important;
    font-family: 'Segoe UI', system-ui, sans-serif !important;
}
.gr-panel, .gr-box, .gradio-container .block {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 16px !important;
}
label, .gr-form label {
    color: #e2e8f0 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.gr-file-upload, .upload-container {
    background: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 14px !important;
    color: #94a3b8 !important;
    transition: all 0.2s !important;
    min-height: 120px !important;
}
.gr-file-upload:hover {
    border-color: #f7941d !important;
    background: #f7941d08 !important;
}
.gr-button-primary {
    background: linear-gradient(135deg, #f7941d, #e07b0a) !important;
    border: none !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    border-radius: 12px !important;
    padding: 14px !important;
    animation: pulse 2s infinite !important;
    transition: all 0.2s !important;
    letter-spacing: 0.5px !important;
}
.gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px #f7941d66 !important;
    animation: none !important;
}
.gr-button-secondary {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.gr-button-secondary:hover {
    border-color: #f7941d !important;
    color: #f7941d !important;
}
.tab-nav button {
    color: #64748b !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
}
.tab-nav button.selected {
    color: #f7941d !important;
    border-bottom-color: #f7941d !important;
}
.section-title {
    color: #f7941d;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 18px 0 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1f2d45;
}
footer { display: none !important; }
"""

with gr.Blocks(css=css, theme=gr.themes.Base()) as demo:

    gr.HTML(f"""
    <div style='display:flex;align-items:center;gap:18px;padding:20px 28px;
                background:linear-gradient(135deg,#111827,#1a2035);
                border-bottom:3px solid #f7941d;border-radius:16px;
                margin-bottom:20px;animation:fadeIn 0.6s ease'>
      <img src='{LOGO_SRC}'
           style='height:50px;width:auto;object-fit:contain;mix-blend-mode:screen;
                  filter:brightness(1.1) drop-shadow(0 0 8px #f7941d88)'>
      <div style='flex:1'>
        <div style='font-size:22px;font-weight:800;color:white'>
          AMC <span style='color:#f7941d'>Report</span> Summarizer</div>
        <div style='font-size:12px;color:#64748b;margin-top:3px'>
          Aseel Medical Care · Red Sea · AI-Powered Medical Report Analysis</div>
      </div>
      <div style='background:#f7941d18;border:1px solid #f7941d44;
                  border-radius:10px;padding:10px 16px;text-align:center'>
        <div style='color:#f7941d;font-size:11px;font-weight:800;letter-spacing:1px'>
          🔒 PRIVATE & SECURE</div>
        <div style='color:#64748b;font-size:10px;margin-top:2px'>Files processed in memory only</div>
      </div>
    </div>
    """)

    gr.HTML("""
    <div style='background:linear-gradient(135deg,#111827,#1a2035);border-radius:16px;
                padding:24px;margin-bottom:20px;border:1px solid #1f2d45;animation:fadeIn 0.7s ease'>
      <div style='color:#f7941d;font-size:11px;font-weight:700;text-transform:uppercase;
                  letter-spacing:2px;margin-bottom:16px;text-align:center'>✨ How It Works</div>
      <div style='display:flex;gap:10px;align-items:stretch'>
        <div style='flex:1;background:#0a0f1e;border-radius:12px;padding:16px;
                    text-align:center;border:1px solid #1f2d45'>
          <div style='font-size:32px;margin-bottom:8px'>📄</div>
          <div style='color:#f7941d;font-size:10px;font-weight:700;letter-spacing:2px;margin-bottom:6px'>
            STEP 1</div>
          <div style='color:white;font-weight:700;font-size:14px;margin-bottom:6px'>
            Upload Your Report</div>
          <div style='color:#64748b;font-size:12px;line-height:1.6'>
            Click the upload box and choose any medical PDF —
            lab results, radiology, discharge papers, or prescriptions</div>
        </div>
        <div style='display:flex;align-items:center;color:#f7941d;font-size:22px;padding:0 4px'>→</div>
        <div style='flex:1;background:#0a0f1e;border-radius:12px;padding:16px;
                    text-align:center;border:1px solid #1f2d45'>
          <div style='font-size:32px;margin-bottom:8px'>🔍</div>
          <div style='color:#f7941d;font-size:10px;font-weight:700;letter-spacing:2px;margin-bottom:6px'>
            STEP 2</div>
          <div style='color:white;font-weight:700;font-size:14px;margin-bottom:6px'>
            Click Analyze</div>
          <div style='color:#64748b;font-size:12px;line-height:1.6'>
            Hit the orange button — our AI reads and understands your report in seconds</div>
        </div>
        <div style='display:flex;align-items:center;color:#f7941d;font-size:22px;padding:0 4px'>→</div>
        <div style='flex:1;background:#0a0f1e;border-radius:12px;padding:16px;
                    text-align:center;border:1px solid #1f2d45'>
          <div style='font-size:32px;margin-bottom:8px'>📊</div>
          <div style='color:#f7941d;font-size:10px;font-weight:700;letter-spacing:2px;margin-bottom:6px'>
            STEP 3</div>
          <div style='color:white;font-weight:700;font-size:14px;margin-bottom:6px'>
            Read Your Summary</div>
          <div style='color:#64748b;font-size:12px;line-height:1.6'>
            Get a plain-language summary in English & Arabic,
            with abnormal values clearly highlighted</div>
        </div>
        <div style='display:flex;align-items:center;color:#f7941d;font-size:22px;padding:0 4px'>→</div>
        <div style='flex:1;background:#0a0f1e;border-radius:12px;padding:16px;
                    text-align:center;border:1px solid #1f2d45'>
          <div style='font-size:32px;margin-bottom:8px'>💬</div>
          <div style='color:#f7941d;font-size:10px;font-weight:700;letter-spacing:2px;margin-bottom:6px'>
            STEP 4</div>
          <div style='color:white;font-weight:700;font-size:14px;margin-bottom:6px'>
            Ask Questions</div>
          <div style='color:#64748b;font-size:12px;line-height:1.6'>
            Switch to the chat tab and ask anything in English or Arabic</div>
        </div>
      </div>
    </div>
    """)

    with gr.Tabs():

        with gr.Tab("📄  Upload & Analyze"):
            with gr.Row(equal_height=False):

                with gr.Column(scale=1, min_width=260):
                    gr.HTML("<div class='section-title'>📎 Upload Your Medical Report</div>")
                    pdf_input = gr.File(
                        label="Click here or drag & drop your PDF",
                        file_types=[".pdf"],
                        type="filepath"
                    )
                    gr.HTML("""
                    <div style='background:#1e293b;border-radius:10px;padding:14px;margin:10px 0'>
                      <div style='color:#94a3b8;font-size:12px;line-height:1.8'>
                        ✅ Lab results<br>
                        ✅ Radiology reports<br>
                        ✅ Discharge summaries<br>
                        ✅ Prescriptions<br>
                        ✅ Any medical document<br><br>
                        🔒 Your file is <strong style='color:#e2e8f0'>never stored</strong>
                        — processed in memory only
                      </div>
                    </div>""")
                    analyze_btn = gr.Button("🔍  Analyze My Report", variant="primary", size="lg")

                with gr.Column(scale=2, min_width=400):
                    gr.HTML("<div class='section-title'>📊 Report Overview</div>")
                    meta_out = gr.HTML("""
                    <div style='background:#111827;border:2px dashed #1f2d45;border-radius:12px;
                                padding:40px;text-align:center;color:#334155'>
                      <div style='font-size:36px;margin-bottom:10px'>📋</div>
                      <div style='font-size:14px'>Upload your PDF and click
                        <strong style='color:#f7941d'>Analyze My Report</strong> to see results here</div>
                    </div>""")

                    gr.HTML("<div class='section-title'>📝 Plain Language Summary</div>")
                    summary_out = gr.HTML()

                    gr.HTML("<div class='section-title'>🚨 Abnormal Values</div>")
                    flags_out = gr.HTML()

                    gr.HTML("<div class='section-title'>🔍 Key Findings & Follow-up</div>")
                    findings_out = gr.HTML()

            chat_hint = gr.HTML(visible=False, value="""
            <div style='margin-top:16px;background:#071a07;border:1px solid #22c55e55;
                        border-radius:12px;padding:16px 20px;display:flex;gap:14px;
                        align-items:center;animation:fadeIn 0.5s ease'>
              <span style='font-size:28px'>💬</span>
              <div>
                <div style='color:#22c55e;font-weight:700;font-size:15px'>Report analyzed!</div>
                <div style='color:#64748b;font-size:13px;margin-top:3px'>
                  Switch to the <strong style='color:#f7941d'>Ask About Your Report</strong>
                  tab to ask questions about your results.</div>
              </div>
            </div>""")

            analyze_btn.click(
                fn=analyze_report,
                inputs=[pdf_input],
                outputs=[meta_out, summary_out, flags_out, findings_out, chat_hint]
            )

        with gr.Tab("💬  Ask About Your Report"):
            gr.HTML("""
            <div style='background:#1e293b;border-left:4px solid #f7941d;border-radius:10px;
                        padding:14px 18px;margin-bottom:16px'>
              <div style='color:#f7941d;font-weight:700;font-size:13px;margin-bottom:6px'>
                💡 How to use this tab</div>
              <div style='color:#94a3b8;font-size:13px;line-height:1.7'>
                After analyzing your report, ask any question in
                <strong style='color:#e2e8f0'>English or Arabic</strong>.<br>
                Examples:<br>
                &nbsp;&nbsp;→ "Is my hemoglobin level dangerous?"<br>
                &nbsp;&nbsp;→ "What does high creatinine mean?"<br>
                &nbsp;&nbsp;→ "ما معنى نتيجة السكر عندي؟"
              </div>
            </div>""")

            chatbot = gr.Chatbot(label="", height=400, bubble_full_width=False)
            with gr.Row():
                chat_input = gr.Textbox(
                    placeholder="Type your question here... (English or Arabic)",
                    label="", scale=5, lines=1
                )
                send_btn  = gr.Button("Send →", variant="primary", scale=1)
                clear_btn = gr.Button("Clear",  variant="secondary", scale=1)

            send_btn.click(fn=chat_fn, inputs=[chat_input, chatbot],
                           outputs=[chatbot, chat_input])
            chat_input.submit(fn=chat_fn, inputs=[chat_input, chatbot],
                              outputs=[chatbot, chat_input])
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, chat_input])

    gr.HTML("""
    <div style='margin-top:20px;padding:16px 20px;background:#111827;border-radius:12px;
                border:1px solid #1f2d45;display:flex;align-items:flex-start;gap:14px'>
      <span style='font-size:22px'>⚕️</span>
      <span style='color:#475569;font-size:12px;line-height:1.7'>
        <strong style='color:#64748b'>Medical Disclaimer:</strong>
        This tool provides summaries for informational purposes only.
        It does not constitute medical advice, diagnosis, or treatment.
        Always consult your physician before making any health decisions.
        Your uploaded documents are processed in memory and are never stored or shared.
        — <em>AMC Red Sea · AI Division</em>
      </span>
    </div>
    """)

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
