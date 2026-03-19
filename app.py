import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# 1. App Title and Setup
st.title("Architecture Animation Workflow")
st.write("Upload a render, analyze its physical properties, and generate perfect prompts.")

# 2. Initialize Session State (Memory)
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = ""
    
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = "=== ARCHITECTURE PROMPT HISTORY ===\n\n"

# 3. Sidebar (API Key & Export)
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.write("Get a free API key at [Google AI Studio](https://aistudio.google.com/)")

    if api_key:
        genai.configure(api_key=api_key)
        
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
    st.header("Step 1a: Analyze Original Render")
    
    uploaded_file = st.file_uploader("Upload your clean architectural render (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Render", use_container_width=True)
        
        if st.button("Analyze Lighting & Materials"):
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar first!")
            else:
                with st.spinner("Analyzing image physics..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = "Analyze this architectural render. Describe the primary lighting direction, the quality of the light (hard/soft, warm/cool), the main floor materials, and the perspective/camera angle. Keep it concise."
                        response = model.generate_content([prompt, image])
                        
                        st.session_state.analysis_text = response.text
                        st.success("Analysis Complete!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
    if st.session_state.analysis_text:
        st.info("**AI Image Analysis:**\n" + st.session_state.analysis_text)

    st.divider()

    st.header("Step 1b: Generate 'Baking' Prompt")
    
    col1, col2 = st.columns(2)
    with col1:
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
            
        num_people = st.slider("Number of People", 1, 5, 2)
        
        # NEW: Weather & Atmosphere
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
        
    with col2:
        facing_direction = st.selectbox("Facing Direction", [
            "walking away from the camera", 
            "walking towards the camera", 
            "facing left", 
            "facing right", 
            "looking out the window/view"
        ])
        time_of_day = st.selectbox("Time of Day", ["Match Original Image", "Morning", "Midday", "Golden Hour/Sunset", "Night"])
        
        # NEW: Image Enhancement / Post-Processing
        color_grade = st.selectbox("Color Grade & Post-Processing", [
            "Standard Photorealistic (Match Original)",
            "Cinematic (High Dynamic Range, Rich Saturation, Crisp Sharpness)",
            "Moody & Dramatic (Deep Shadows, High Contrast, Desaturated)",
            "Light & Airy (Low Contrast, Bright, Soft Natural Sharpness)",
            "Film Emulation (Subtle Film Grain, Analog Colors)"
        ])
        
    attire = st.text_input("Describe Attire", "Modern, casual business wear")
    
    if st.button("Generate Image Prompt"):
        base_prompt = f"A high-resolution, hyper-realistic architectural photograph. "
        
        if st.session_state.analysis_text:
             base_prompt += f"The base environment features: {st.session_state.analysis_text}. "
             base_prompt += "Crucially, upgrade and render all described materials with hyper-realistic, natural textures and physically based rendering (PBR) quality. "
        
        base_prompt += f"Integrated seamlessly {placement} are {num_people} people wearing {attire}. "
        base_prompt += f"They are {facing_direction}. "
        base_prompt += f"The lighting on the people must perfectly match the described environmental lighting, casting diffuse contact shadows and accurate material reflections. "
        
        # Inject Weather and Grading
        if weather != "Clear / No Weather Effects":
            base_prompt += f"The atmospheric conditions feature {weather.lower()}, interacting naturally with the light and architecture. "
        if color_grade != "Standard Photorealistic (Match Original)":
            base_prompt += f"The final image should be color graded as: {color_grade}."
            
        st.success("Copy this prompt into your Image Generator:")
        st.code(base_prompt)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] IMAGE PROMPT:\n{base_prompt}\n\n"

# --- TAB 2: VIDEO GENERATION ---
with tab2:
    st.header("Step 2: Animate the Baked Image")
    
    col3, col4 = st.columns(2)
    with col3:
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
        
    with col4:
        # NEW: Video Speed
        video_speed = st.selectbox("Video Speed / Framerate Style", [
            "Normal Cinematic Speed (Real-time 24fps)",
            "Slow Motion (120fps style)",
            "Fast Motion / Time-lapse"
        ])
        
        # NEW: Depth of Field (Focus)
        depth_of_field = st.selectbox("Depth of Field (Focus)", [
            "Deep Focus (f/8+ style, entire scene is sharp)",
            "Shallow Focus (Subject is sharp, background beautifully blurred/bokeh)",
            "Shallow Focus (Background is sharp, foreground subjects blurred)",
            "Rack Focus (Focus smoothly shifts from foreground to background)"
        ])
    
    if st.button("Generate Video Prompt"):
        vid_prompt = f"{camera_motion} moving through the space at {video_speed.lower()}. "
        vid_prompt += f"The subjects maintain a {walk_speed}. "
        vid_prompt += f"The lens uses {depth_of_field.lower()}. "
        vid_prompt += "Maintain exact architectural geometry, original lighting, and floor reflections from the starting frame. Natural, physics-based ambient movement."
        
        st.success("Copy this prompt into Google Flow Video:")
        st.code(vid_prompt)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] VIDEO PROMPT:\n{vid_prompt}\n\n"
