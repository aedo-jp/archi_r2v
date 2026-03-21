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

# --- DICTIONARIES FOR DYNAMIC UI DESCRIPTIONS ---
desc_time = {
    "Morning (Warm angled sunlight)": "Creates long, dramatic shadows and a soft, golden-warm hue. Ideal for making spaces feel inviting and energetic.",
    "Midday (Bright, neutral/cool white daylight)": "Mimics the sun at its peak. Creates sharp, short shadows and crisp, true-to-life white tones. Best for accurate color representation.",
    "Golden Hour/Sunset": "Produces rich, deep orange and red tones with highly stretched, dramatic shadows. Very cinematic and emotional.",
    "Twilight / Blue Hour": "The brief window after sunset. Bathes the exterior in soft, cool blue light while making interior warm lights 'pop' and glow.",
    "Night": "Complete darkness outside, forcing the scene to rely entirely on artificial interior lighting, streetlamps, or moonlight.",
    "Evening Party (Moody, Downlights OFF)": "Turns off harsh overhead lights, relying on warm, low-level ambient fixtures (lamps, sconces) for an intimate, moody vibe."
}

desc_weather = {
    "Clear / Crisp Air": "Sharp, high-contrast visibility with no atmospheric interference. Best for clean architectural showcases.",
    "Slight Nighttime Mist (Softens lights)": "Adds a very subtle, cinematic glow (halation) around light sources. Excellent for moody night renders.",
    "Atmospheric Haze / Dust Motes": "Catches the light in the air, creating a lived-in, photorealistic depth. Makes morning sunlight look tangible.",
    "Volumetric Lighting / God Rays": "Forces light to behave like physical beams cutting through the room/air. Very dramatic and stylized.",
    "Light Rain and Wet Reflective Surfaces": "Makes floors, roads, and hard surfaces glossy and reflective, adding texture and bouncing light beautifully.",
    "Heavy Torrential Rain": "Adds visible rain streaks, deepens material colors, and heavily diffuses background visibility.",
    "Light Snow Flurries": "Adds a cold, soft ambiance with gentle falling snow. Best paired with warm interior lighting for contrast.",
    "Heavy Snowstorm": "Creates a white-out effect, significantly softening the light and muting background details.",
    "Overcast / Diffused Sky": "Acts like a giant softbox. Eliminates harsh shadows entirely, providing incredibly even, flat, and balanced lighting."
}

desc_shadow = {
    "Standard realistic shadows": "Default physics. Shadow hardness depends entirely on the size of the light source.",
    "Soft, feathered shadows with low contrast": "Mimics large, diffused light sources (like overcast days or studio softboxes). Very flattering for interiors.",
    "Ambient nighttime lighting with balanced exposure (no pitch-black areas)": "Prevents 'crushed' black shadows, ensuring details are still visible in the darkest corners of a night scene.",
    "Harsh, high-contrast crisp shadows": "Mimics direct, unobstructed sunlight or intense spotlights. Creates bold, graphic architectural lines."
}

desc_render = {
    "Standard Photorealistic PBR": "The baseline standard for modern physically-based rendering. Accurate materials and realistic light.",
    "Global Illumination & Ambient Occlusion": "Forces the AI to focus on how light bounces off walls and softly darkens in corners. Results in highly realistic, grounded scenes.",
    "High Dynamic Range (HDR) photography": "Balances the exposure so you can clearly see details in both the brightest windows and the darkest shadows simultaneously.",
    "Long exposure photography style": "Smooths out water, blurs moving elements (like clouds), and creates a highly polished, serene architectural look."
}

desc_color = {
    "Natural Realism": "Unfiltered, raw color output. Looks like a standard high-quality digital photograph.",
    "Architectural Crisp (Perfectly neutral white balance, cool daylight tones, accurate whites)": "Strips away warm tints, ensuring white walls look purely white. The industry standard for modern architectural portfolios.",
    "Bright & Airy (High key, diffused cool lighting)": "Overexposes the image slightly and lowers contrast for a light, breezy, and optimistic feel (often used in Scandi design).",
    "Cinematic (Rich Saturation, Crisp Sharpness)": "Boosts colors and edge sharpness to look like a frame from a high-budget Hollywood film.",
    "Moody & Dramatic (Deep Shadows, Desaturated)": "Pulls color out of the image and deepens shadows for a brooding, intense, and highly stylized look."
}
# ------------------------------------------------

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
                            1. The exact camera perspective, horizon line, and framing.
                            2. The core architectural form and structural geometry.
                            3. Key building and landscaping materials (comma-separated list).
                            4. Identify physical architectural lighting fixtures (e.g., sconces, uplights).
                            Keep it extremely concise (under 50 words). Do NOT describe current lighting, shadows, sky, or weather. Provide a 'blank slate' physical description."""
                        else:
                            vision_prompt = """Analyze this interior architectural render. Describe:
                            1. The exact spatial layout and camera viewpoint (e.g., wide-angle interior view).
                            2. Key floor/wall materials (comma-separated list).
                            3. Major structural furniture or built-ins.
                            4. Identify all physical interior lighting fixtures (e.g., specific lamps, chandeliers, pendant lights).
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
        time_of_day = st.selectbox("Time of Day / Lighting Scenario", list(desc_time.keys()))
        st.caption(f"💡 *{desc_time[time_of_day]}*")
        st.write("") 
        
        weather = st.selectbox("Atmosphere & Weather", list(desc_weather.keys()))
        st.caption(f"💡 *{desc_weather[weather]}*")
        st.write("")
        
    with col4:
        shadow_quality = st.selectbox("Shadow Quality", list(desc_shadow.keys()))
        st.caption(f"💡 *{desc_shadow[shadow_quality]}*")
        st.write("")
        
        rendering_style = st.selectbox("Rendering Engine & Camera Tech", list(desc_render.keys()))
        st.caption(f"💡 *{desc_render[rendering_style]}*")
        st.write("")
        
        color_grade = st.selectbox("Color Grade", list(desc_color.keys()), index=1)
        st.caption(f"💡 *{desc_color[color_grade]}*")
    
    # Generate Button
    st.write("")
    if st.button("Generate Image Prompt"):
        
        valid_mat_changes = [c for c in st.session_state.material_changes if c["from"].strip() and c["to"].strip()]
        
        clean_time = time_of_day.split(" (")[0]
        clean_weather = weather.split(" (")[0]
        
        # --- BUILDING THE STRUCTURED PROMPT FOR NANO BANANA PRO / MIDJOURNEY STYLE ---
        
        # 1. BASE AND PERSPECTIVE (Softer, photography-based locking)
        base_prompt = f"**[BASE]**\n- A high-resolution, photorealistic {scene_type.lower()} architectural photograph.\n\n"
        
        base_prompt += "**[CAMERA & PERSPECTIVE]**\n- Maintain the exact composition, framing, camera angle, and structural geometry of the reference image perfectly.\n\n"
        
        # 2. LIGHTING & FIXTURES
        base_prompt += "**[LIGHTING & FIXTURES]**\n"
        if time_of_day == "Evening Party (Moody, Downlights OFF)":
            base_prompt += "- The lighting is an intimate, moody evening party atmosphere at night.\n"
            base_prompt += "- All overhead ceiling downlights and bright spotlights are completely turned OFF. The space is illuminated beautifully by the existing low-level ambient lighting, floor lamps, and indirect cove lighting present in the design. Do not add string lights or party decor; just use the existing architecture to create a dim, moody environment.\n"
        else:
            base_prompt += f"- The lighting scenario is {clean_time}.\n"
            if "Night" in time_of_day or "Twilight" in time_of_day:
                 base_prompt += "- Maintain the exact physical design of the existing lighting fixtures. Do not alter their shape or invent new lamps. Beautifully increase the luminosity and glow of the existing architectural lights to illuminate the space.\n"
            else:
                 if scene_type == "Interior":
                     base_prompt += f"- The interior is illuminated beautifully by natural {clean_time.lower()} streaming in through the windows, alongside balanced existing interior fixtures.\n"
                 else:
                     base_prompt += f"- Utilize natural environmental light matching the {clean_time.lower()}. Maintain the existing fixture geometry perfectly without adding new artificial lights.\n"
        
        clean_render = rendering_style.split(" (")[0]
        if clean_render != "Standard Photorealistic PBR":
            base_prompt += f"- Rendered utilizing {clean_render.lower()} and full global illumination to ensure natural, realistic light bounce and softness throughout the scene.\n"
        else:
            base_prompt += "- Rendered with full global illumination to ensure natural, realistic light bounce and softness throughout the scene.\n"
        
        clean_shadow = shadow_quality.split(" (")[0]
        if clean_shadow != "Standard realistic shadows":
            base_prompt += f"- Ensure the lighting features {clean_shadow.lower()}.\n"
        base_prompt += "\n"
            
        # 3. GEOMETRY & MATERIALS
        base_prompt += "**[PHYSICAL GEOMETRY & MATERIALS]**\n"
        if st.session_state.analysis_text:
            base_prompt += f"- The precise physical {scene_type.lower()} scene consists of: {st.session_state.analysis_text}\n"
            
        if valid_mat_changes:
            base_prompt += "- Retain all original architectural materials perfectly and elevate them to photorealistic PBR quality, EXCEPT for the following explicit replacements:\n"
            for change in valid_mat_changes:
                base_prompt += f"  * REPLACE '{change['from']}' WITH '{change['to']}'\n"
            base_prompt += "\n"
        else:
            base_prompt += "- Retain all original architectural materials perfectly. Elevate them to hyper-realistic, natural textures and physically based rendering (PBR) quality.\n\n"
            
        # 4. SUBJECTS (HYPERBOOSTED PHOTOGRAPHY LANGUAGE)
        if repopulate_rendered_people:
            base_prompt += "**[SUBJECTS & PEOPLE: REPOPULATE]**\n"
            base_prompt += "- Identify all people currently present in the original image. Paint over them entirely with high-end, photorealistic human subjects.\n"
            base_prompt += "- HYPER-DETAILED FACES: Facial features must be rendered in extreme 8k resolution with razor-sharp photographic focus, especially for figures closer to the camera. Skin texture, eyes, and micro-details must look like a raw, high-end studio portrait spliced perfectly into the scene. No smooth, blurry, or low-res CGI faces.\n"
            base_prompt += "- Maintain the exact positions, scale, and locations of every person exactly as they appear in the original render.\n"
            base_prompt += f"- The human subjects must be lit perfectly in conjunction with the selected {clean_time.lower()} environment and {clean_weather.lower()} atmosphere, casting accurate contact shadows.\n\n"
            
        elif num_people > 0:
            base_prompt += "**[SUBJECTS & PEOPLE: ADD]**\n"
            base_prompt += f"- Integrated seamlessly {placement} are {num_people} people wearing {attire}, {facing_direction}.\n"
            base_prompt += "- HYPER-DETAILED FACES: Facial features must be rendered in extreme 8k resolution with razor-sharp photographic focus, especially for figures closer to the camera. Skin texture, eyes, and micro-details must look like a raw, high-end studio portrait. No smooth, blurry, or low-res CGI faces.\n"
            base_prompt += f"- The human subjects must be lit perfectly in conjunction with the selected {clean_time.lower()} environment and {clean_weather.lower()} atmosphere, casting accurate contact shadows.\n\n"
        else:
            base_prompt += "**[SUBJECTS & PEOPLE]**\n- No human subjects present. Focus purely on the architecture.\n\n"
        
        # 5. ATMOSPHERE & RENDERING
        base_prompt += "**[ATMOSPHERE & RENDERING]**\n"
        
        if clean_weather != "Clear / Crisp Air":
            if scene_type == "Interior":
                base_prompt += f"- The view outside the windows and the quality of the light reflect {clean_weather.lower()} conditions.\n"
            else:
                base_prompt += f"- The atmospheric conditions feature {clean_weather.lower()}. Any atmospheric effects like mist or haze must strictly remain volumetric light scatter and must not alter the physical geometry of the building.\n"
        
        clean_color = color_grade.split(" (")[0]
        if clean_color != "Natural Realism":
            base_prompt += f"- The final image should be color graded as: {clean_color}.\n"
            
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
