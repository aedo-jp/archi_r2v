import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# 1. App Title and Setup
st.title("Architecture Animation Workflow")
st.write("Upload a render, extract its physical geometry, and build perfect generative prompts.")

# 2. Initialize Session State (Memory)
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = ""
    
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = "=== ARCHITECTURE PROMPT HISTORY ===\n\n"

# 3. Sidebar (API Key & Export)
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
    st.write("Save your generated prompts as a text file.")
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
    st.header("Step 1a: Extract 'Blank Slate' Geometry")
    
    uploaded_file = st.file_uploader("Upload your clean architectural render (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Render", use_container_width=True)
        
        if st.button("Extract Physical Geometry"):
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar/secrets first!")
            else:
                with st.spinner("Extracting blank slate geometry and materials..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # NEW: The highly specific, conflict-free analysis prompt
                        vision_prompt = """Please analyze this architectural render. I want to use your analysis to generate a new, highly photorealistic version of this exact building, but I will be changing the lighting and time of day myself. 
                        Please provide a detailed, comma-separated descriptive prompt focusing strictly on the following:
                        - The camera angle, and framing.
                        - The architectural style, geometry, and structural forms.
                        - Hyper-specific descriptions of the building materials and textures.
                        - The static landscaping and environment (trees, terrain, roads).
                        CRITICAL: Do NOT include any descriptions of the current lighting, shadows, time of day, sky, or weather conditions in your output prompt. Strip all atmospheric details away so I am left with a 'blank slate' physical description of the scene."""
                        
                        response = model.generate_content([vision_prompt, image])
                        
                        st.session_state.analysis_text = response.text
                        st.success("Geometry Extraction Complete!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
    if st.session_state.analysis_text:
        st.info("**Extracted 'Blank Slate' Geometry:**\n" + st.session_state.analysis_text)

    st.divider()

    st.header("Step 1b: Generate 'Baking' Prompt")
    
    # --- SECTION 1: SUBJECTS (PEOPLE) ---
    st.subheader("1. Subject Details")
    col1, col2 = st.columns(2)
    
    with col1:
        # NEW: Slider from 0 to 10
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
    
    # --- SECTION 2: ENVIRONMENT & STYLE ---
    st.subheader("2. Environment & Atmosphere")
    col3, col4 = st.columns(2)
    
    with col3:
        time_of_day = st.selectbox("Time of Day", ["Morning", "Midday", "Golden Hour/Sunset", "Night", "Overcast Daytime"])
        weather = st.selectbox("Weather & Atmosphere", [
            "Clear / No Weather Effects",
            "Light Rain and Wet Surfaces",
            "Heavy Torrential Rain",
            "Light Snow Flurries",
            "Heavy Snowstorm",
            "Volumetric Fog / Morning Mist",
            "Atmospheric Haze / Dust Motes",
            "Windy (blowing leaves and debris)",
            "Overcast / Diffused Sky"
        ])
        
    with col4:
        color_grade = st.selectbox("Color Grade & Post-Processing", [
            "Standard Photorealistic",
            "Cinematic (High Contrast, Rich Saturation, Crisp Sharpness)",
            "Moody & Dramatic (Deep Shadows, High Contrast, Desaturated)",
            "Light & Airy (Low Contrast, Bright, Soft Natural Sharpness)",
            "Film Emulation (Subtle Film Grain, Analog Colors)"
        ])
    
    # Generate Button
    st.write("")
    if st.button("Generate Image Prompt"):
        base_prompt = f"A high-resolution, hyper-realistic architectural photograph. "
        
        # 1. Establish the Atmosphere FIRST
        base_prompt += f"The time of day is exclusively {time_of_day}, featuring highly realistic {time_of_day} lighting, physically accurate global illumination, and matching shadows. "
        
        # 2. Inject the Blank Slate Geometry SECOND
        if st.session_state.analysis_text:
            base_prompt += f"The physical scene is structured as follows: {st.session_state.analysis_text}. "
            base_prompt += "Crucially, render all described materials with hyper-realistic, natural textures and physically based rendering (PBR) quality. "
        
        # 3. Add People (Only if num_people > 0)
        if num_people > 0:
            base_prompt += f"Integrated seamlessly {placement} are {num_people} people wearing {attire}. "
            base_prompt += f"They are {facing_direction}. "
            base_prompt += f"The lighting on the subjects must perfectly match the {time_of_day} environment, casting accurate diffuse contact shadows and material reflections. "
        
        # 4. Add Weather and Finishing Grades
        if weather != "Clear / No Weather Effects":
            base_prompt += f"The atmospheric conditions feature {weather.lower()}, interacting naturally with the light and architecture. "
        if color_grade != "Standard Photorealistic":
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
