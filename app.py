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
    
    scene_type = st.radio("Select Scene Type:", ["Exterior", "Interior"], horizontal=True)
    st.divider()
    
    st.header("Step 1a: Extract Simplified Geometry")
    
    uploaded_file = st.file_uploader("Upload your clean architectural render (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Render", use_container_width=True)
        
        if st.button("Extract Physical Geometry"):
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar/secrets first!")
            else:
                with st.spinner(f"Extracting simplified {scene_type.lower()} geometry..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # AMENDMENT 1 & 2: Updating the extraction prompt to lock camera and define lighting fixtures as structural geometry.
                        if scene_type == "Exterior":
                            vision_prompt = """Analyze this architectural render. Describe:
                            1. The precise camera perspective, horizon line, and framing.
                            2. The core architectural form and geometry.
                            3. Key building and landscaping materials (comma-separated list).
                            4. CRITICAL: Identify and describe any physical architectural lighting fixtures (e.g., sconces, uplights) as structural geometry that must not change shape.
                            Keep it extremely concise (under 50 words). Do NOT describe current lighting, shadows, sky, or weather. Provide a 'blank slate' physical description."""
                        else:
                            vision_prompt = """Analyze this interior architectural render. Describe:
                            1. The precise spatial layout and camera viewpoint (e.g., wide-angle interior view).
                            2. Key floor/wall materials (comma-separated list).
                            3. Major structural furniture or built-ins.
                            4. CRITICAL: Identify and describe all physical interior lighting fixtures (e.g., specific lamps, chandeliers, pendant lights) as structural geometry that must remain identical.
                            Keep it extremely concise (under 50 words). Do NOT describe current lighting, shadows, time of day, or weather. Provide a 'blank slate' of the physical room."""
                            
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
    
    # AMENDMENT 4: Checkbox to disable new people inputs and replace existing ones.
    # Using session state to manage disabled inputs dynamically.
    if "repopulate_people" not in st.session_state:
        st.session_state.repopulate_people = False

    repopulate_rendered_people = st.checkbox("Repopulate existing rendered figures with photorealistic subjects.", help="Check this box if fake-looking CGI people are already in the scene and you want to replace them in their exact positions. This disables the other inputs below.")
    
    # Update session state based on checkbox
    if repopulate_rendered_people != st.session_state.repopulate_people:
        st.session_state.repopulate_people = repopulate_rendered_people
        st.rerun()

    col1, col2 = st.columns(2)
    
    with col1:
        # Disable if repopulate checkbox is ticked
        num_people = st.slider("Number of People to Add", 0, 10, 2, disabled=st.session_state.repopulate_people)
        placement_option = st.selectbox("Location in Scene", [
            "Foreground Center", "Foreground Left", "Foreground Right",
            "Middle-ground Center", "Middle-ground Left", "Middle-ground Right",
            "Background Center", "Background Left", "Background Right",
            "Other (Custom Description)"
        ], disabled=st.session_state.repopulate_people)
        
        # Streamlit Magic: Placement "Other" text input logic
        if placement_option == "Other (Custom Description)" and not st.session_state.repopulate_people:
            placement = st.text_input("Describe custom location", "standing behind the glass balcony railing")
        elif not st.session_state.repopulate_people:
            placement = placement_option.lower()
        else:
            placement = "" # Placement handled by replacement logic below

    with col2:
        # Disable if repopulate checkbox is ticked
        
        # AMENDMENT 3: Facing Direction logic with an "Other" override.
        facing_direction_option = st.selectbox("Facing Direction", [
            "walking away from the camera", 
            "walking towards the camera", 
            "facing left", 
            "facing right", 
            "looking out the window/view",
            "Other (Custom Direction)"
        ], disabled=st.session_state.repopulate_people)
        
        if facing_direction_option == "Other (Custom Direction)" and not st.session_state.repopulate_people:
            facing_direction = st.text_input("Describe custom direction", "gazing directly up at the ceiling feature")
        elif not st.session_state.repopulate_people:
            facing_direction = facing_direction_option
        else:
            facing_direction = "" # Direction handled by replacement logic below
            
        attire = st.text_input("Describe Attire", "Modern, casual business wear", disabled=st.session_state.repopulate_people)

    st.divider()
    
    # --- SECTION 2: ENVIRONMENT & STYLE ---
    st.subheader("2. Environment, Lighting & Rendering")
    col3, col4 = st.columns(2)
    
    with col3:
        time_of_day = st.selectbox("Time of Day", ["Morning", "Midday", "Golden Hour/Sunset", "Twilight / Blue Hour", "Night"])
        
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
        shadow_quality = st.selectbox("Shadow Quality", [
            "Standard realistic shadows",
            "Soft, feathered shadows with low contrast",
            "Ambient nighttime lighting with balanced exposure (no pitch-black areas)",
            "Harsh, high-contrast crisp shadows"
        ])
        
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
        # AMENDMENT 1 & 2: Starting the prompt with strict "LOCKING" commands.
        base_prompt = f"A high-resolution, hyper-realistic {scene_type.lower()} architectural photograph. "
        
        # Lock Perspective
        base_prompt += "CRITICAL PERSPECTIVE LOCK: You MUST maintain the exact camera position, horizon line, focal length, and target viewpoint from the uploaded image. Do NOT shift the camera or change the composition. "
        
        # 1. Time of Day and Strict Lighting Control
        base_prompt += f"The time of day is {time_of_day}. "
        
        if time_of_day in ["Twilight / Blue Hour", "Night"]:
             base_prompt += "CRITICAL FIXTURE LOCK: Utilize ONLY the existing physical architectural lighting fixtures present in the original design. Do NOT invent or add any new fixtures. Increase the luminosity of the existing architectural lights to beautifully illuminate the space. Maintain their exact geometry. "
        else:
             if scene_type == "Interior":
                 base_prompt += f"The interior is illuminated beautifully by natural {time_of_day} light streaming in through the windows, alongside balanced existing interior fixtures. Maintain fixture geometry. "
             else:
                 base_prompt += f"Utilize natural environmental light matching the {time_of_day}. Do NOT add new artificial light fixtures to the architecture. Maintain fixture geometry. "
        
        if shadow_quality != "Standard realistic shadows":
            base_prompt += f"Ensure the lighting features {shadow_quality.lower()}. "
            
        # 2. Blank Slate Geometry
        if st.session_state.analysis_text:
            base_prompt += f"The precise physical {scene_type.lower()} scene consists of: {st.session_state.analysis_text}. "
            
        # 3. People (Handling Amendment 4 Logic)
        if repopulate_rendered_people:
            # New specific replacement instructions
            base_prompt += "Integrated seamlessly into the scene: Identify any existing, CGI-looking rendered people figures present in the original geometry. Repopulate and replace them with high-end, photorealistic human subjects of the same gender and attire style, maintaining their exact positions, poses, and locations perfectly. "
        elif num_people > 0:
            # Existing add-new-people logic
            base_prompt += f"Integrated seamlessly {placement} are {num_people} people wearing {attire}, {facing_direction}. "
        
        # If people exist, light them correctly
        if repopulate_rendered_people or num_people > 0:
            base_prompt += f"The human subjects are lit naturally by the environment, casting accurate soft contact shadows. "
        
        # 4. Atmosphere & Rendering
        if weather != "Clear / Crisp Air":
            if scene_type == "Interior":
                base_prompt += f"The view outside the windows and the quality of the light reflect {weather.lower()} conditions. "
            else:
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
