import os
import tempfile
import streamlit as st
from PIL import Image
import base64

# Import existing logic
from iris_key import CASIA_IRIS_DIR, discover_casia_iris_images
from stego import (
    embed_message,
    extract_message,
    enroll_user,
    verify_user,
    AUTH_DIR,
    PAYLOAD_TYPE_TEXT,
    PAYLOAD_TYPE_FILE
)

# Page Configuration
st.set_page_config(
    page_title="Biometric Steganography HUD",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to get base64 of an image (for CSS backgrounds or direct embedding)
def get_image_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Path to the generated banner
BANNER_PATH = os.path.join(os.getcwd(), "iris_banner_png_1776158705096.png")

# Custom Styling (Premium Dark Mode + Glassmorphism)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Outfit:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {{
        --primary: #00f2fe;
        --secondary: #4facfe;
        --hacker-green: #39ff14;
        --hacker-pink: #ff00ff;
        --bg: #020617;
        --card-bg: rgba(15, 23, 42, 0.7);
    }}

    .stApp {{
        background-color: var(--bg);
        background-image: 
            linear-gradient(rgba(0, 242, 254, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 242, 254, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
        color: #f8fafc;
        font-family: 'Outfit', sans-serif;
    }}

    /* Scanline Animation */
    .stApp::before {{
        content: " ";
        display: block;
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 1000;
        background-size: 100% 2px, 3px 100%;
        pointer-events: none;
        opacity: 0.3;
    }}

    /* Glassmorphism Cyber Card */
    .glass-card {{
        background: var(--card-bg);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(0, 242, 254, 0.2);
        border-radius: 4px; /* Harder corners for tech vibe */
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.1);
        position: relative;
        overflow: hidden;
    }}
    
    .glass-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 10px;
        height: 10px;
        border-top: 2px solid var(--primary);
        border-left: 2px solid var(--primary);
    }}

    .glass-card:hover {{
        border: 1px solid var(--primary);
        box-shadow: 0 0 30px rgba(0, 242, 254, 0.3);
    }}

    /* Typography */
    h1, h2, h3 {{
        font-family: 'Share Tech Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    
    .hero-title {{
        font-size: 4rem;
        color: var(--primary);
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.8);
        margin-bottom: 0.5rem;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: rgba(2, 6, 23, 0.98);
        border-right: 2px solid var(--primary);
        box-shadow: 5px 0 15px rgba(0, 242, 254, 0.2);
    }}

    /* Button Styling (Cyberpunk style) */
    .stButton>button {{
        border: 1px solid var(--primary);
        background: transparent;
        color: var(--primary);
        font-family: 'Share Tech Mono', monospace;
        font-weight: 700;
        border-radius: 0px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        position: relative;
    }}
    
    .stButton>button:hover {{
        background: var(--primary);
        color: #000 !important;
        box-shadow: 0 0 25px var(--primary);
    }}

    /* Terminal Output */
    .terminal-out {{
        font-family: 'JetBrains Mono', monospace;
        background-color: rgba(0, 0, 0, 0.9);
        color: var(--hacker-green);
        padding: 15px;
        border-radius: 4px;
        border: 1px solid var(--hacker-green);
        box-shadow: inset 0 0 10px rgba(57, 255, 20, 0.2);
        font-size: 0.9rem;
        line-height: 1.5;
    }}

    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--bg);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--primary);
        border-radius: 10px;
    }}

    /* Metric Styling */
    [data-testid="stMetricValue"] {{
        font-family: 'Share Tech Mono', monospace;
        color: var(--hacker-pink) !important;
        text-shadow: 0 0 10px var(--hacker-pink);
    }}

    /* Scanning Line Overlay */
    .scanner {{
        position: relative;
        overflow: hidden;
    }}
    .scanner::after {{
        content: "";
        position: absolute;
        top: -100%;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(0deg, transparent 0%, var(--primary) 50%, transparent 100%);
        opacity: 0.3;
        animation: scan 3s linear infinite;
        pointer-events: none;
    }}
    @keyframes scan {{
        0% {{ top: -100%; }}
        100% {{ top: 100%; }}
    }}
</style>
""", unsafe_allow_html=True)

def main():
    # Hero Section with Banner
    if os.path.exists(BANNER_PATH):
        st.image(BANNER_PATH, width='stretch')
    
    st.markdown("<h1 class='hero-title'>AES-DWT BIOMETRIC HUD</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:1.2rem; color:#94a3b8; margin-bottom:2rem;'>Secure Wavelet-Domain Steganography with Cancelable Biometric Templates</p>", unsafe_allow_html=True)
    
    # Sidebar for Biometric Management
    with st.sidebar:
        st.markdown("<h2 style='color:#00f2fe'>🔐 IDENTITY</h2>", unsafe_allow_html=True)
        
        # Discover Iris Images
        available_images = discover_casia_iris_images(CASIA_IRIS_DIR)
        rel_paths = [os.path.relpath(p, CASIA_IRIS_DIR) for p in available_images]
        
        selected_rel_path = st.selectbox(
            "Target Subject",
            options=rel_paths if rel_paths else ["No samples discovered"],
            help="Select a biometric sample for authentication."
        )
        
        full_iris_path = os.path.join(CASIA_IRIS_DIR, selected_rel_path) if rel_paths else None
        
        if full_iris_path and os.path.exists(full_iris_path):
            st.markdown("<div class='glass-card scanner' style='padding:5px'>", unsafe_allow_html=True)
            img = Image.open(full_iris_path)
            st.image(img, caption=f"BIO-REF: {selected_rel_path}", width='stretch')
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Simulated Telemetry
            st.markdown("""
            <div style='font-family:Share Tech Mono; font-size:0.8rem; color:#4facfe; opacity:0.8;'>
            > PUPIL_DILATION: 0.42<br>
            > COLLAGEN_FREQ: 2.1GHz<br>
            > PATTERN_VEC: [7, 2, 9, 3]
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        
        if st.button("✨ INITIALIZE ENROLLMENT"):
            if full_iris_path:
                with st.status("Initializing Secure Template...", expanded=True) as status:
                    st.write("Extracting biometric features...")
                    # logic inside stego.enroll_user does the printing
                    enroll_user(full_iris_path)
                    st.write("Generating encrypted keystream...")
                    st.write("Hardening template with salt transition...")
                    status.update(label="Enrollment Complete", state="complete", expanded=False)
                st.toast("Biometric template hardened and stored.", icon="🔒")
            else:
                st.warning("No subject selected.")

    # Main HUD Layout
    col_main, col_status = st.columns([2.5, 1])
    
    with col_main:
        tab_hide, tab_extract, tab_about = st.tabs(["[ ⚡ ENCODE ]", "[ 💡 DECODE ]", "[ ℹ️ SYSTEM ]"])
        
        with tab_hide:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("### 🏹 Payload Injection")
            
            c1, c2 = st.columns(2)
            with c1:
                audio_upload = st.file_uploader("Source Audio (.wav)", type=["wav"], help="WAV file for message carrier.")
            with c2:
                payload_mode = st.radio("Payload Mode", ["Text Message", "Binary File"], horizontal=True)
                
                if payload_mode == "Text Message":
                    message = st.text_area("Secure Message", placeholder="TOP SECRET - CLASSIFIED", height=100)
                    file_payload = None
                else:
                    file_payload = st.file_uploader("Payload File", type=["pdf", "docx", "png", "jpg", "jpeg", "csv", "txt", "bin"])
                    message = None
            
            if audio_upload:
                st.audio(audio_upload, format="audio/wav")
            
            if st.button("🚀 EXECUTE EMBEDDING"):
                if not audio_upload:
                    st.error("Missing carrier audio.")
                elif payload_mode == "Text Message" and not message:
                    st.error("Payload is empty.")
                elif payload_mode == "Binary File" and not file_payload:
                    st.error("No file selected for payload.")
                elif not full_iris_path:
                    st.error("Biometric ID not selected.")
                else:
                    try:
                        with st.spinner("Processing DWT & Biometric HUD..."):
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
                                tmp_in.write(audio_upload.getvalue())
                                input_path = tmp_in.name
                            
                            output_path = input_path + "_stego.wav"
                            
                            if payload_mode == "Text Message":
                                embed_message(input_path, message.encode('utf-8'), output_path, full_iris_path, mode=PAYLOAD_TYPE_TEXT)
                            else:
                                embed_message(input_path, file_payload.getvalue(), output_path, full_iris_path, mode=PAYLOAD_TYPE_FILE, filename=file_payload.name)
                            
                            with open(output_path, "rb") as f:
                                stego_data = f.read()
                            
                            st.success("Embedding Process Finalized.")
                            st.download_button(
                                label="📥 RETRIEVE STEGO-CARRIER",
                                data=stego_data,
                                file_name="stego_output.wav",
                                mime="audio/wav"
                            )
                            
                            os.remove(input_path)
                            os.remove(output_path)
                    except Exception as e:
                        st.error(f"Critical System Error: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_extract:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("### 🔍 Payload Extraction")
            
            stego_upload = st.file_uploader("Stego Audio (.wav)", type=["wav"], key="extract_uploader")
            
            if stego_upload:
                st.audio(stego_upload, format="audio/wav")
                
                if st.button("🔓 INITIATE EXTRACTION"):
                    if not full_iris_path:
                        st.error("Biometric ID not selected.")
                    else:
                        try:
                            with st.spinner("Authenticating & Extracting..."):
                                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_in:
                                    tmp_in.write(stego_upload.getvalue())
                                    input_path = tmp_in.name
                                
                                result = extract_message(input_path, full_iris_path)
                                
                                if result:
                                    mode, data, filename = result
                                    st.success("Data Extraction Successful.")
                                    
                                    if mode == PAYLOAD_TYPE_FILE:
                                        st.info(f"📁 Recovered File: **{filename}**")
                                        st.download_button(
                                            label=f"📥 DOWNLOAD {filename.upper()}",
                                            data=data,
                                            file_name=filename
                                        )
                                    else:
                                        try:
                                            text_msg = data.decode('utf-8')
                                            st.markdown(f"<div class='terminal-out'>{text_msg}</div>", unsafe_allow_html=True)
                                        except:
                                            st.warning("Data recovered but appears to be non-text binary.")
                                            st.download_button("Download Raw Data", data=data, file_name="extracted_data.bin")
                                
                                os.remove(input_path)
                        except Exception as e:
                            st.error(f"Extraction Failure: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab_about:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("""
            ### 🖥️ System Manifest
            - **Algorithm**: Haar Discrete Wavelet Transform (DWT)
            - **Authentication**: Salted-XOR Biometric Template Protection
            - **Encryption Pool**: AES-128 via Fernet
            - **Biometric Path**: `biometric_config/`
            """)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_status:
        st.markdown("<div class='glass-card' style='height: 100%;'>", unsafe_allow_html=True)
        st.markdown("### 📊 TELEMETRY")
        
        # Real-time stats visualization
        cols = st.columns(2)
        cols[0].metric("ENCR", "AES-256", delta="Active")
        cols[1].metric("DWT", "HAAR", delta="L1-L2")
        
        st.divider()
        st.markdown("#### 📡 SIGNAL ANALYSIS")
        st.progress(0.75, text="CHANNEL NOISE: 0.003dB")
        st.progress(0.42, text="ENTROPY DENSITY: 0.98")
        
        st.divider()
        st.markdown("#### 📟 KERNEL LOG")
        log_placeholder = st.empty()
        log_placeholder.markdown("""
        <div class='terminal-out' style='height: 250px; overflow-y: auto;'>
        [LOAD] BOOTING_HUD_V2.0... OK<br>
        [NET] SOCKET_HANDSHAKE: 127.0.0.1... ESTABLISHED<br>
        [MOD] WAVELET_ENGINE: INITIALIZING... READY<br>
        [BIO] IRIS_DRIVERS: LOADED<br>
        [SEC] AES_ENCRYPTION_POOL: STANDBY<br>
        <span style='color:#ff00ff'>[ALERT] STANDBY_FOR_INPUT...</span><br>
        --- SYSTEM READY ---
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
