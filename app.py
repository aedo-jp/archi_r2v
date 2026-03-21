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

# Initialize Session State for Dynamic Material Changes
if "material_changes" not in st.session_state:
    st.session_state.material_changes = [{"id": 0, "from": "", "to": ""}]
if "mat_id_counter" not in st.session_state:
    st.session_state.mat_id_counter = 1

def add_material_row():
    st.session_state.material_changes.append({"id": st.session_state.mat_id_counter, "from": "", "to": ""})
    st.session_state.mat_id_counter += 1

def remove_material_row(index):
    st.session_state.material_changes.pop(index)

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
    
    # --- SECTION 1: MATERIAL OVERRIDES ---
    st.subheader("1. Material Overrides")
    st.write("Specify any materials you want to change from the original render. Leave blank to keep everything original.")
    
    for i, change in enumerate(st.session_state.material_changes):
        col_m1, col_m2, col_m3 = st.columns([4, 4, 1])
        with col_m1:
            change["from"] = st.text_input(
                "Original Material (Change From)", 
                value=change["from"], 
                key=f"from_{change['id']}", 
                label_visibility="visible" if i == 0 else "collapsed",
                placeholder="e.g., concrete floor"
            )
        with col_m2:
            change["to"] = st.text_input(
                "New Material (Change To)", 
                value=change["to"], 
                key=f"to_{change['id']}", 
                label_visibility="visible" if i == 0 else "collapsed",
                placeholder="e.g., warm oak timber"
            )
        with col_m3:
            if i == 0:
                st.write("")
                st.write("")
            if st.button("❌", key=f"del_{change['id']}", help="Delete this row"):
                remove_material_row(i)
                st.rerun()
                
    if st.button("➕ Add Material Change"):
        add_material_row()
        st.rerun()

    st.divider()

    # --- SECTION 2: SUBJECTS (PEOPLE) ---
    st.subheader("2. Subject Details")
    
    if "repopulate_people" not in st.session_state:
        st.session_state.repopulate_people = False

    repopulate_rendered_people = st.checkbox("Repopulate existing rendered figures with photorealistic subjects.", help="Check this box if fake-looking CGI people are already in the scene and you want to replace them in their exact positions. This disables the other inputs below.")
    
    if repopulate_rendered_people != st.session_state.repopulate_people:
        st.session_state.repopulate_people = repopulate_rendered_people
        st.rerun()

    col1, col2 = st.columns(2)
    
    with col1:
        num_people = st.slider("Number of People to Add", 0, 10, 2, disabled=st.session_state.repopulate_people)
        placement_option = st.selectbox("Location in Scene", [
            "Foreground Center", "Foreground Left", "Foreground Right",
            "Middle-ground Center", "Middle-ground Left", "Middle-ground Right",
            "Background Center", "Background Left", "Background Right",
            "Other (Custom Description)"
        ], disabled=st.session_state.repopulate_people)
        
        if placement_option == "Other (Custom Description)" and not st.session_state.repopulate_people:
            placement = st.text_input("Describe custom location", "standing behind the glass balcony railing")
        elif not st.session_state.repopulate_people:
            placement = placement_option.lower()
        else:
            placement = ""

    with col2:
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
            facing_direction = ""
            
        attire = st.text_input("Describe Attire", "Modern, casual business wear", disabled=st.session_state.repopulate_people)

    st.divider()
    
    # --- SECTION 3: ENVIRONMENT & STYLE ---
    st.subheader("3. Environment, Lighting & Rendering")
    col3, col4 = st.columns(2)
    
    with col3:
        time_of_day = st.selectbox("Time of Day / Lighting Scenario", [
            "Morning (Warm angled sunlight)", 
            "Midday (Bright, neutral/cool white daylight)", 
            "Golden Hour/Sunset", 
            "Twilight / Blue Hour", 
            "Night",
            "Evening Party (Moody, Downlights OFF)"
        ])
        
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
        
        # UPDATED: Set "Architectural Crisp" as the default using index=1
        color_grade = st.selectbox("Color Grade", [
            "Natural Realism",
            "Architectural Crisp (Perfectly neutral white balance, cool daylight tones, accurate whites)",
            "Bright & Airy (High key, diffused cool lighting)",
            "Cinematic (Rich Saturation, Crisp Sharpness)",
            "Moody & Dramatic (Deep Shadows, Desaturated)"
        ], index=1)
    
    # Generate Button
    st.write("")
    if st.button("Generate Image Prompt"):
        
        valid_mat_changes = [c for c in st.session_state.material_changes if c["from"].strip() and c["to"].strip()]
        
        # --- BUILDING THE STRUCTURED PROMPT ---
        
        # 1. BASE AND PERSPECTIVE
        base_prompt = f"**[BASE]**\n- A high-resolution, hyper-realistic {scene_type.lower()} architectural photograph.\n\n"
        
        base_prompt += "**[CAMERA & PERSPECTIVE]**\n- CRITICAL PERSPECTIVE LOCK: You MUST maintain the exact camera position, horizon line, focal length, and target viewpoint from the uploaded image. Do NOT shift the camera or change the composition.\n\n"
        
        # 2. LIGHTING & FIXTURES
        base_prompt += "**[LIGHTING & FIXTURES]**\n"
        if time_of_day == "Evening Party (Moody, Downlights OFF)":
            base_prompt += "- The time of day is night, featuring an intimate, moody evening party atmosphere.\n"
            base_prompt += "- CRITICAL FIXTURE LOCK & LIGHTING RULE: All overhead ceiling downlights, recessed lights, and bright spotlights MUST be completely turned OFF. The space is illuminated exclusively by existing low-level ambient lighting, floor lamps, wall sconces, and indirect cove lighting present in the original design. Do NOT invent new party lights, string lights, or disco balls. Maintain original fixture geometry perfectly, just change which ones are emitting light to create a dim, moody environment.\n"
        else:
            base_prompt += f"- The lighting scenario is {time_of_day}.\n"
            if time_of_day in ["Twilight / Blue Hour", "Night"]:
                 base_prompt += "- CRITICAL FIXTURE LOCK: The exact physical design, shape, and architectural style of the existing lighting fixtures MUST be strictly preserved. Do NOT alter their appearance, morph them into generic lamps, or invent new light sources. Increase the luminosity of the existing architectural lights to beautifully illuminate the space while maintaining their exact original geometry.\n"
            else:
                 if scene_type == "Interior":
                     base_prompt += f"- The interior is illuminated beautifully by natural {time_of_day.lower()} streaming in through the windows, alongside balanced existing interior fixtures. The exact physical design and shape of all light fixtures MUST be strictly preserved.\n"
                 else:
                     base_prompt += f"- Utilize natural environmental light matching the {time_of_day.lower()}. Do NOT add new artificial light fixtures to the architecture. Maintain original fixture geometry perfectly.\n"
        
        if rendering_style != "Standard Photorealistic PBR":
            base_prompt += f"- Rendered utilizing {rendering_style.lower()} and full global illumination to ensure natural, realistic light bounce throughout the scene, naturally softening shadows.\n"
        else:
            base_prompt += "- Rendered with full global illumination to ensure natural, realistic light bounce throughout the scene, naturally softening shadows.\n"
        
        if shadow_quality != "Standard realistic shadows":
            base_prompt += f"- Ensure the lighting features {shadow_quality.lower()}.\n"
        base_prompt += "\n"
            
        # 3. GEOMETRY & MATERIALS
        base_prompt += "**[PHYSICAL GEOMETRY & MATERIALS]**\n"
        if st.session_state.analysis_text:
            base_prompt += f"- The precise physical {scene_type.lower()} scene consists of: {st.session_state.analysis_text}\n"
            
        if valid_mat_changes:
            base_prompt += "- CRITICAL MATERIAL INSTRUCTION: Retain all original architectural materials perfectly and elevate them to photorealistic PBR quality, EXCEPT for the following explicit replacements:\n"
            for change in valid_mat_changes:
                base_prompt += f"  * REPLACE '{change['from']}' WITH '{change['to']}'\n"
            base_prompt += "\n"
        else:
            base_prompt += "- CRITICAL MATERIAL INSTRUCTION: Retain all original architectural materials perfectly. Elevate them to hyper-realistic, natural textures and physically based rendering (PBR) quality.\n\n"
            
        # 4. SUBJECTS
        if repopulate_rendered_people:
            base_prompt += "**[SUBJECTS & PEOPLE: REPOPULATE]**\n"
            base_prompt += "- CRITICAL PEOPLE REPLACEMENT: Identify all existing CGI-looking or low-detail people figures present in the original geometry. Treat them strictly as placeholder masks for complete photo-painting. Do NOT attempt to improve or enhance the old figures. Instead, paint them over ENTIRELY with high-end, photorealistic human subjects.\n"
            base_prompt += "- The new subjects MUST possess flawless, detailed photorealistic faces and features, clearly defined and in sharp focus, as if from real photography. No CGI characteristics, blurs, blank expressions, or missing facial features (like eyes or mouths) are permitted. All details of their clothing, skin, and pose must be photo-perfect, maintaining their exact positions and locations from the original render.\n"
            base_prompt += "- The human subjects are lit naturally by the environment, casting accurate soft contact shadows.\n\n"
        elif num_people > 0:
            base_prompt += "**[SUBJECTS & PEOPLE: ADD]**\n"
            base_prompt += f"- Integrated seamlessly {placement} are {num_people} people wearing {attire}, {facing_direction}. All subjects must possess flawless photorealistic faces and clear, defined features.\n"
            base_prompt += "- The human subjects are lit naturally by the environment, casting accurate soft contact shadows.\n\n"
        else:
            base_prompt += "**[SUBJECTS & PEOPLE]**\n- No human subjects present. Focus purely on the architecture.\n\n"
        
        # 5. ATMOSPHERE & RENDERING
        base_prompt += "**[ATMOSPHERE & RENDERING]**\n"
        if weather != "Clear / Crisp Air":
            if scene_type == "Interior":
                base_prompt += f"- The view outside the windows and the quality of the light reflect {weather.lower()} conditions.\n"
            else:
                base_prompt += f"- The atmospheric conditions feature {weather.lower()}. CRITICAL: Atmospheric effects like mist, haze, or fog must strictly remain volumetric light scatter and MUST NOT alter, morph, or redesign the physical geometry of the building or its lighting fixtures.\n"
        
        if color_grade != "Natural Realism":
            base_prompt += f"- The final image should be color graded as: {color_grade}.\n"
            
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
        vid_prompt = f"**[CAMERA MOVEMENT]**\n- {camera_motion} moving through the space at {video_speed.lower()}.\n"
        vid_prompt += "- Camera is mounted on a perfectly smooth mechanical slider and stabilized gimbal. Zero camera shake, no handheld movement, no walking bounce, perfectly fluid cinematic motion.\n\n"
        
        vid_prompt += f"**[SUBJECT MOTION]**\n- The subjects maintain a {walk_speed}.\n\n"
        
        vid_prompt += f"**[LENS & FOCUS]**\n- The lens uses {depth_of_field.lower()}.\n\n"
        
        vid_prompt += "**[PERSISTENCE & PHYSICS]**\n- Maintain exact architectural geometry, original lighting, and floor reflections from the starting frame. Natural, physics-based ambient movement."
        
        st.success("Copy this prompt into Google Flow Video:")
        st.code(vid_prompt)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] VIDEO PROMPT:\n{vid_prompt}\n\n"
