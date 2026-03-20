import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# 1. App Title and Setup
st.title("Architecture Animation Workflow")
st.write("Upload a render, extract its physical geometry, and build perfect generative prompts.")

# 2. Initialize Session State
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = ""
    
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = "=== ARCHITECTURE PROMPT HISTORY ===\n\n"

# 3. Sidebar
with st.sidebar:
    st.header("Setup")
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        st.success("✅ API Key securely loaded!")
    except KeyError:
        st.error("API Key not found! Please add it to your Streamlit Secrets.")
        
    st.divider()
    
    st.header("Export Prompts")
    st.download_button(
        label="Download History (TXT)",
        data=st.session_state.prompt_history,
        file_name="prompt_history.txt",
        mime="text/plain"
    )
    
    if st.button("Clear History"):
        st.session_state.prompt_history = "=== ARCHITECTURE PROMPT HISTORY ===\n\n"
        st.rerun()

# 4. Create Tabs
tab1, tab2 = st.tabs(["Step 1: Bake (Image)", "Step 2: Animate (Video)"])

# --- TAB 1: IMAGE GENERATION ---
with tab1:
    st.header("Step 1a: Extract Simplified Geometry")
    
    uploaded_file = st.file_uploader("Upload your clean architectural render (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Render", use_container_width=True)
        
        if st.button("Extract Physical Geometry"):
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar/secrets first!")
            else:
                with st.spinner("Extracting simplified blank slate geometry..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # NEW: Highly simplified, concise analysis prompt
                        vision_prompt = """Analyze this architectural render. Provide a concise, simplistic, comma-separated list describing ONLY the core architectural form, key building materials, and key landscaping features. 
                        CRITICAL: Keep it extremely brief (under 40 words). Do NOT include any descriptions of lighting, shadows, time of day, sky, or weather. I need a simplified blank slate."""
                        
                        response = model.generate_content([vision_prompt, image])
                        
                        st.session_state.analysis_text = response.text
                        st.success("Geometry Extraction Complete!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
    if st.session_state.analysis_text:
        st.info("**Simplified 'Blank Slate' Geometry:**\n" + st.session_state.analysis_text)

    st.divider()

    st.header("Step 1b: Generate 'Baking' Prompt")
    
    # --- SECTION 1: SUBJECTS (PEOPLE) ---
    st.subheader("1. Subject Details")
    col1, col2 = st.columns(2)
    
    with col1:
        num_people = st.slider("Number of People", 0, 10, 2)
        placement_option = st.selectbox("Location in Scene", [
            "Foreground Center", "Foreground Left", "Foreground Right",
            "Middle-ground Center", "Middle-ground Left", "Middle-ground Right",
            "Background Center", "Background Left", "Background Right",
            "Other (Custom Description)"
        ])
        
        if placement_option == "Other (Custom Description)":
            placement = st.text_input("Describe custom location", "standing behind the glass balcony railing")
        else:
            placement = placement_option.lower()

    with col2:
        facing_direction = st.selectbox("Facing Direction", [
            "walking away from the camera", 
            "walking towards the camera", 
            "facing left", 
            "facing right", 
            "looking out the window/view"
        ])
        attire = st.text_input("Describe Attire", "Modern, casual business wear")

    st.divider()
    
    # --- SECTION 2: ENVIRONMENT & STYLE (OVERHAULED) ---
    st.subheader("2. Environment, Lighting & Rendering")
    col3, col4 = st.columns(2)
    
    with col3:
        time_of_day = st.selectbox("Time of Day", ["Morning", "Midday", "Golden Hour/Sunset", "Twilight / Blue Hour", "Night"])
        
        # NEW: Granular Light Source Control
        light_source = st.selectbox("Primary Light Source", [
            "Natural ambient sunlight/skylight",
            "Soft ambient moonlight",
            "Warm interior lights spilling out with ambient city glow",
            "Low-level landscape lighting and warm architectural uplighting",
            "Harsh directional spotlighting"
        ])
        
        # UPGRADED: Atmosphere with subtle mist/haze options
        weather = st.selectbox("Atmosphere & Weather", [
            "Clear / Crisp Air",
            "Slight Nighttime Mist (Softens lights)",
            "Atmospheric Haze / Dust Motes",
            "Volumetric Lighting / God Rays",
            "Light Rain and Wet Reflective Surfaces",
            "Heavy Torrential Rain",
            "Light Snow Flurries",
            "Heavy Snowstorm",
            "Overcast / Diffused Sky"
        ])
        
    with col4:
        # NEW: Shadow Quality Modifiers
        shadow_quality = st.selectbox("Shadow Quality", [
            "Standard realistic shadows",
            "Soft, feathered shadows with low contrast",
            "Ambient nighttime lighting with balanced exposure (no pitch-black areas)",
            "Harsh, high-contrast crisp shadows"
        ])
        
        # NEW: Rendering Engine Terminology
        rendering_style = st.selectbox("Rendering Engine & Camera Tech", [
            "Standard Photorealistic PBR",
            "Global Illumination & Ambient Occlusion",
            "High Dynamic Range (HDR) photography",
            "Long exposure photography style"
        ])
        
        color_grade = st.selectbox("Color Grade", [
            "Natural Realism",
            "Cinematic (Rich Saturation, Crisp Sharpness)",
            "Moody & Dramatic (Deep Shadows, Desaturated)",
            "Light & Airy (Low Contrast, Bright)"
        ])
    
    # Generate Button
    st.write("")
    if st.button("Generate Image Prompt"):
        base_prompt = f"A high-resolution, hyper-realistic architectural photograph. "
        
        # 1. Lighting and Time
        base_prompt += f"The time of day is {time_of_day}. "
        base_prompt += f"The scene is illuminated primarily by {light_source.lower()}. "
        if shadow_quality != "Standard realistic shadows":
            base_prompt += f"The lighting features {shadow_quality.lower()}. "
            
        # 2. Blank Slate Geometry
        if st.session_state.analysis_text:
            base_prompt += f"The physical scene consists of: {st.session_state.analysis_text}. "
            
        # 3. People (If any)
        if num_people > 0:
            base_prompt += f"Integrated seamlessly {placement} are {num_people} people wearing {attire}, {facing_direction}. "
            base_prompt += f"The subjects are lit naturally by the {time_of_day} environment, casting accurate soft contact shadows. "
        
        # 4. Atmosphere & Rendering
        if weather != "Clear / Crisp Air":
            base_prompt += f"The atmospheric conditions feature {weather.lower()}. "
        
        if rendering_style != "Standard Photorealistic PBR":
            base_prompt += f"Rendered utilizing {rendering_style.lower()} to ensure natural light bounce. "
            
        if color_grade != "Natural Realism":
            base_prompt += f"The final image should be color graded as: {color_grade}."
            
        st.success("Copy this prompt into your Image Generator:")
        st.code(base_prompt)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] IMAGE PROMPT:\n{base_prompt}\n\n"

# --- TAB 2: VIDEO GENERATION ---
with tab2:
    st.header("Step 2: Animate the Baked Image")
    
    col5, col6 = st.columns(2)
    with col5:
        camera_motion = st.selectbox("Camera Movement", [
            "Static / No Movement",
            "Slow Dolly-In (Push In)", "Fast Dolly-In",
            "Slow Dolly-Out (Pull Out)", "Fast Dolly-Out",
            "Slow Pan Left", "Fast Pan Left",
            "Slow Pan Right", "Fast Pan Right",
            "Slow Tilt Up", "Slow Tilt Down",
            "Slow Tracking Shot Left", "Slow Tracking Shot Right",
            "Aerial Overhead Drone Shot (Bird's Eye)",
            "Horizontal Drone Fly-By",
            "Crane Shot Sweep"
        ])
        walk_speed = st.selectbox("Walking Speed", ["Casual stroll", "Brisk walk", "Standing still"])
        
    with col6:
        video_speed = st.selectbox("Video Speed / Framerate Style", [
            "Normal Cinematic Speed (Real-time 24fps)",
            "Slow Motion (120fps style)",
            "Fast Motion / Time-lapse"
        ])
        
        depth_of_field = st.selectbox("Depth of Field (Focus)", [
            "Deep Focus (f/8+ style, entire scene is sharp)",
            "Shallow Focus (Subject is sharp, background beautifully blurred/bokeh)",
            "Shallow Focus (Background is sharp, foreground subjects blurred)",
            "Rack Focus (Focus smoothly shifts from foreground to background)"
        ])
    
    if st.button("Generate Video Prompt"):
        vid_prompt = f"{camera_motion} moving through the space at {video_speed.lower()}. "
        vid_prompt += "Camera is mounted on a perfectly smooth mechanical slider and stabilized gimbal. Zero camera shake, no handheld movement, no walking bounce, perfectly fluid cinematic motion. "
        vid_prompt += f"The subjects maintain a {walk_speed}. "
        vid_prompt += f"The lens uses {depth_of_field.lower()}. "
        vid_prompt += "Maintain exact architectural geometry, original lighting, and floor reflections from the starting frame. Natural, physics-based ambient movement."
        
        st.success("Copy this prompt into Google Flow Video:")
        st.code(vid_prompt)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] VIDEO PROMPT:\n{vid_prompt}\n\n"
