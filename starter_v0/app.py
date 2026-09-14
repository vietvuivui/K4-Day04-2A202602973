import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, trim_history, now_iso, safe_slug, write_transcript
from versioning import build_artifact_version, artifact_version_dict

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(page_title="IT Helpdesk Agent", page_icon="🤖", layout="wide")

# --- Funcs ---
def init_new_transcript(version, provider_name, model_name, system_prompt_path, tools_path, artifact_version):
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(version),
        safe_slug(provider_name),
        timestamp,
    ])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model_name,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    return transcript_path, transcript

def render_assistant_message(content, status, num_rounds):
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "reply" in data:
            st.markdown(data["reply"])
            with st.expander("🔍 Dữ liệu phản hồi gốc (JSON)"):
                st.json({k: v for k, v in data.items() if k != "reply"})
        else:
            st.write(content)
    except Exception:
        st.write(content)
        
    if status:
        color = "green" if status == "answered" else "orange" if status == "waiting_for_user" else "red"
        st.markdown(f"🔹 **Trace:** &nbsp; Trạng thái: :{color}[**{status}**] &nbsp; | &nbsp; Vòng lặp: **{num_rounds}**")

# --- UI Sidebar ---
with st.sidebar:
    st.header("⚙️ Setting")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"])
    
    try:
        import os
        if not os.environ.get(f"{provider_name.upper()}_API_KEY"):
            raise ValueError(f"Chưa cấu hình {provider_name.upper()}_API_KEY trong file .env")
            
        provider = make_provider(provider_name)
        model_name = getattr(provider, "default_model", "Unknown")
        st.success(f"✅ Đã kết nối: `{model_name}`")
    except Exception as e:
        st.error(f"❌ Lỗi Provider: {e}")
        provider = None
        model_name = None
        
    version_input = st.text_input("Version (dùng cho báo cáo)", value="v0", help="Ví dụ: v0, v1, v2")
    
    st.markdown("---")
    
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    
    # Tính toán Artifact Version & Hash
    artifact_version = build_artifact_version(version_input, system_prompt_path, tools_path)
    
    st.write("📦 **Artifact Version:**", artifact_version.artifact_version)
    st.caption(f"Prompt: `{artifact_version.prompt_hash[:8]}` | Tools: `{artifact_version.tools_hash[:8]}`")
    
    st.markdown("---")
    
    if st.button("🔄 Bắt đầu phiên hội thoại mới"):
        st.session_state.history = []
        st.session_state.messages_ui = []
        st.session_state.turn_index = 0
        st.session_state.transcript = None
        st.session_state.transcript_path = None
        st.rerun()
        
    if "transcript_path" in st.session_state and st.session_state.transcript_path:
        st.success(f"📂 **Transcript Path:**\n`{st.session_state.transcript_path.name}`")
        
    st.markdown("---")
    st.info("💡 **Tuân thủ quy tắc Lab:** Giao diện này tái sử dụng nguyên bản hàm `run_model_tool_loop`.")

st.title("🤖 IT Helpdesk Agent Lab - Live Chat")

# --- Initialize States ---
if "history" not in st.session_state:
    st.session_state.history = [] 
if "messages_ui" not in st.session_state:
    st.session_state.messages_ui = []
if "turn_index" not in st.session_state:
    st.session_state.turn_index = 0

# --- Render Chat UI ---
for msg in st.session_state.messages_ui:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            render_assistant_message(msg["content"], msg.get("status"), msg.get("num_rounds", 1))
        
            if msg.get("tool_events"):
                with st.expander("🛠️ Xem chi tiết Tool Trace"):
                    for event in msg["tool_events"]:
                        st.markdown(f"**🟢 Tool:** `{event.get('tool')}`")
                        st.json({"Arguments": event.get("args")})
                        result = event.get("result", {})
                        if "error" in result and result["error"] not in [None, ""]:
                            st.error(f"Lỗi ({result.get('error')}): {result.get('message')}")
                        else:
                            st.success("Kết quả:")
                            st.json(result)
                        st.divider()

# --- Chat Input ---
if user_text := st.chat_input("Nhập yêu cầu hỗ trợ...", disabled=provider is None):
    st.session_state.turn_index += 1
    
    # Hiển thị câu hỏi của user
    st.session_state.messages_ui.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    # Chuẩn bị
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    
    # Tạo transcript nếu chưa có
    if "transcript" not in st.session_state or not st.session_state.transcript:
        path, trans = init_new_transcript(version_input, provider_name, model_name, system_prompt_path, tools_path, artifact_version)
        st.session_state.transcript_path = path
        st.session_state.transcript = trans

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, window=5),
        {"role": "user", "content": user_text},
    ]

    turn_record = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    # Xử lý
    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_name,
                    max_tool_rounds=4,
                )
                
                assistant_text = result.get("assistant_text", "")
                tool_events = result.get("tool_events", [])
                status = result.get("status", "unknown")
                num_rounds = len(result.get("rounds", []))
                
                turn_record.update(result)
                
                render_assistant_message(assistant_text, status, num_rounds)
                
                if tool_events:
                    with st.expander("🛠️ Xem chi tiết Tool Trace", expanded=True):
                        for event in tool_events:
                            st.markdown(f"**🟢 Tool:** `{event.get('tool')}`")
                            st.json({"Arguments": event.get("args")})
                            res = event.get("result", {})
                            if "error" in res and res["error"] not in [None, ""]:
                                st.error(f"Lỗi ({res.get('error')}): {res.get('message')}")
                            else:
                                st.success("Kết quả:")
                                st.json(res)
                            st.divider()
                
                st.session_state.history.append({"role": "user", "content": user_text})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})
                st.session_state.messages_ui.append({
                    "role": "assistant", 
                    "content": assistant_text,
                    "tool_events": tool_events,
                    "status": status,
                    "num_rounds": num_rounds
                })
                
            except Exception as e:
                error_msg = f"Lỗi thực thi: {str(e)}"
                turn_record.update({
                    "status": "provider_error",
                    "error": f"{type(e).__name__}: {str(e)}",
                })
                st.error(error_msg)
                st.session_state.messages_ui.append({
                    "role": "assistant", 
                    "content": error_msg,
                    "status": "provider_error"
                })
            
            # Lưu log
            turn_record["ended_at"] = now_iso()
            st.session_state.transcript["turns"].append(turn_record)
            write_transcript(st.session_state.transcript_path, st.session_state.transcript)
            st.rerun()
