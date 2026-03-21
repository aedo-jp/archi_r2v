import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# =============================================================================
# App Title and Setup
# =============================================================================
st.title("Architecture Animation Workflow")
st.write("Upload a render, extract its physical geometry, and build perfect generative prompts.")

# =============================================================================
# Initialize Session State
# =============================================================================
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = ""
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = "=== ARCHITECTURE PROMPT HISTORY ===\n\n"
if "material_changes" not in st.session_state:
    st.session_state.material_changes = [{"id": 0, "from": "", "to": ""}]
if "mat_id_counter" not in st.session_state:
    st.session_state.mat_id_counter = 1
if "repopulate_people" not in st.session_state:
    st.session_state.repopulate_people = False

def add_material_row():
    st.session_state.material_changes.append({"id": st.session_state.mat_id_counter, "from": "", "to": ""})
    st.session_state.mat_id_counter += 1

def remove_material_row(index):
    st.session_state.material_changes.pop(index)

# =============================================================================
# UI Description Dictionaries
# =============================================================================
desc_time = {
    "Morning (Warm angled sunlight)": "Creates long, dramatic shadows and a soft, golden-warm hue. Ideal for making spaces feel inviting and energetic.",
    "Midday (Bright, neutral/cool white daylight)": "Mimics the sun at its peak. Creates sharp, short shadows and crisp, true-to-life white tones. Best for accurate colour representation.",
    "Golden Hour/Sunset": "Produces rich, deep orange and red tones with highly stretched, dramatic shadows. Very cinematic and emotional.",
    "Twilight / Blue Hour": "The brief window after sunset. Bathes the exterior in soft, cool blue light while making interior warm lights 'pop' and glow.",
    "Night": "Complete darkness outside, forcing the scene to rely entirely on artificial interior lighting, streetlamps, or moonlight.",
    "Evening Party (Moody, Downlights OFF)": "Turns off harsh overhead lights, relying on warm, low-level ambient fixtures (lamps, sconces) for an intimate, moody vibe."
}

desc_artificial_light = {
    "Match Natural Environment (Default)": "Lets the AI decide the interior fixture colour based on the time of day.",
    "Warm White (2700K - 3000K)": "Traditional cosy, yellowish-orange glow. Common in hospitality, residential, and restaurants.",
    "Neutral White (4000K)": "Clean, crisp, pure white light. Industry standard for modern offices, retail, and contemporary kitchens.",
    "Cool Daylight White (5000K - 6000K)": "Very bright, slightly bluish-white light. Used in hospitals, galleries, or ultra-modern minimalist spaces."
}

desc_weather = {
    "Clear / Crisp Air": "Sharp, high-contrast visibility with no atmospheric interference. Best for clean architectural showcases.",
    "Slight Nighttime Mist (Softens lights)": "Adds a very subtle, cinematic glow (halation) around light sources. Excellent for moody night renders.",
    "Atmospheric Haze / Dust Motes": "Catches the light in the air, creating a lived-in, photorealistic depth. Makes morning sunlight look tangible.",
    "Volumetric Lighting / God Rays": "Forces light to behave like physical beams cutting through the room/air. Very dramatic and stylised.",
    "Light Rain and Wet Reflective Surfaces": "Makes floors, roads, and hard surfaces glossy and reflective, adding texture and bouncing light beautifully.",
    "Heavy Torrential Rain": "Adds visible rain streaks, deepens material colours, and heavily diffuses background visibility.",
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
    "Natural Realism": "Unfiltered, raw colour output. Looks like a standard high-quality digital photograph.",
    "Architectural Crisp (Perfectly neutral white balance, cool daylight tones, accurate whites)": "Strips away warm tints, ensuring white walls look purely white. The industry standard for modern architectural portfolios.",
    "Bright & Airy (High key, diffused cool lighting)": "Overexposes the image slightly and lowers contrast for a light, breezy, and optimistic feel (often used in Scandi design).",
    "Cinematic (Rich Saturation, Crisp Sharpness)": "Boosts colours and edge sharpness to look like a frame from a high-budget film.",
    "Moody & Dramatic (Deep Shadows, Desaturated)": "Pulls colour out of the image and deepens shadows for a brooding, intense, and highly stylised look."
}

desc_lens = {
    "24mm Wide — Interior Rooms & Large Spaces": "Classic architectural wide-angle. Shows full spatial depth. Slight barrel distortion at edges.",
    "35mm Standard Prime — Street Level & Lifestyle": "The most 'human eye' focal length. Natural perspective, minimal distortion. Ideal for people-forward scenes.",
    "50mm Standard — Balanced Exterior Facade": "Compression-free, neutral perspective. Makes materials and proportions feel true-to-life.",
    "85mm Short Telephoto — Compressed Facade / Portrait Bias": "Gently flatters faces and compresses depth. Ideal when people are a prominent feature.",
    "16mm Ultra-Wide — Dramatic Interiors & Tall Structures": "Maximises spatial drama. Pronounced distortion and foreshortening. Very cinematic."
}

desc_photographer = {
    "Architectural Editorial (Wallpaper* / Dezeen)": "Clean, composed, slightly cool. Architecture is the hero. People are incidental lifestyle props.",
    "Luxury Lifestyle (AD / Robb Report)": "Warm, aspirational, inviting. People look relaxed and affluent. Light is always flattering.",
    "Candid / Documentary": "Slightly looser framing, natural imperfection. Feels caught-in-the-moment. Truest to real life.",
    "Commercial Campaign": "High contrast, high saturation, perfectly lit. Everything is deliberate. No accidents."
}

desc_skin_tone = {
    "AI-determined (varied and natural)": "Let the model choose a realistic, diverse mix of skin tones naturally.",
    "Predominantly fair / light skin tones": "Northern European or East Asian complexions. Cool-to-neutral undertones.",
    "Predominantly medium / olive skin tones": "Mediterranean, Middle Eastern, or Latin complexions. Warm-neutral undertones.",
    "Predominantly dark / deep skin tones": "African, South Asian, or Afro-Caribbean complexions. Rich warm-to-cool undertones.",
    "Diverse mix of ethnicities": "Explicitly varied — no single demographic dominates."
}

desc_body_language = {
    "Casually conversing in small groups": "Natural social clusters, relaxed posture, slight body lean toward conversation partners.",
    "Walking naturally, mid-stride": "Caught mid-step. Weight shift visible. Arms swinging naturally.",
    "Standing still, observing the space or view": "Relaxed standing posture. Weight on one hip. Gaze directed outward or upward.",
    "Seated, relaxed posture": "Natural slouch, crossed legs, clothing draping and folding naturally against the seat.",
    "Using a phone or laptop": "Head tilted slightly down, focus directed at device. Subtle screen glow visible on face.",
    "Engaged in a professional meeting or discussion": "Upright posture, direct eye contact between subjects, purposeful hand gestures."
}

# =============================================================================
# Sidebar
# =============================================================================
with st.sidebar:
    st.header("Setup")
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        st.success("✅ API Key securely loaded!")
    except KeyError:
        st.error("API Key not found! Please add it to your Streamlit Secrets.")
        api_key = None

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

# =============================================================================
# Tabs
# =============================================================================
tab1, tab2 = st.tabs(["Step 1: Bake (Image)", "Step 2: Animate (Video)"])

# =============================================================================
# TAB 1: IMAGE GENERATION
# =============================================================================
with tab1:

    scene_type = st.radio("Select Scene Type:", ["Exterior", "Interior"], horizontal=True)
    st.divider()

    # -------------------------------------------------------------------------
    # STEP 1a: GEOMETRY EXTRACTION
    # -------------------------------------------------------------------------
    st.header("Step 1a: Extract Simplified Geometry")

    uploaded_file = st.file_uploader("Upload your clean architectural render (JPG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Render", use_container_width=True)

        if st.button("Extract Physical Geometry"):
            if not api_key:
                st.error("Please add your Gemini API Key to Streamlit Secrets first.")
            else:
                with st.spinner(f"Extracting simplified {scene_type.lower()} geometry..."):
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')

                        if scene_type == "Exterior":
                            vision_prompt = (
                                "Analyse this architectural render. Describe:\n"
                                "1. The exact camera perspective, horizon line, and framing.\n"
                                "2. The core architectural form and structural geometry.\n"
                                "3. Key building and landscaping materials (comma-separated list).\n"
                                "4. Identify physical architectural lighting fixtures (e.g., sconces, uplights).\n"
                                "Keep it extremely concise (under 50 words). "
                                "Do NOT describe current lighting, shadows, sky, or weather. "
                                "Provide a 'blank slate' physical description."
                            )
                        else:
                            vision_prompt = (
                                "Analyse this interior architectural render. Describe:\n"
                                "1. The exact spatial layout and camera viewpoint (e.g., wide-angle interior view).\n"
                                "2. Key floor/wall/ceiling materials (comma-separated list).\n"
                                "3. Major structural furniture or built-ins.\n"
                                "4. Identify all physical interior lighting fixtures (e.g., specific lamps, chandeliers, pendant lights).\n"
                                "Keep it extremely concise (under 50 words). "
                                "Do NOT describe current lighting, shadows, time of day, or weather. "
                                "Provide a 'blank slate' of the physical room."
                            )

                        response = model.generate_content([vision_prompt, image])
                        st.session_state.analysis_text = response.text
                        st.success("Geometry Extraction Complete!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    if st.session_state.analysis_text:
        st.info("**Simplified 'Blank Slate' Geometry:**\n" + st.session_state.analysis_text)

    st.divider()

    # -------------------------------------------------------------------------
    # STEP 1b: PROMPT BUILDER
    # -------------------------------------------------------------------------
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

    repopulate_rendered_people = st.checkbox(
        "Repopulate existing rendered figures with photorealistic subjects.",
        help="Check this box if fake-looking CGI people are already in the scene and you want to replace them in their exact positions."
    )

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

        attire = st.text_input(
            "Describe Attire",
            "Modern, casual business wear",
            disabled=st.session_state.repopulate_people,
            help="Be specific: fabric type, colours, and fit all help. E.g., 'slim-fit dark navy trousers, white linen shirt, no tie'"
        )

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

        body_language = st.selectbox(
            "Body Language / Activity",
            list(desc_body_language.keys()),
            disabled=st.session_state.repopulate_people
        )
        if not st.session_state.repopulate_people:
            st.caption(f"💡 *{desc_body_language[body_language]}*")

        skin_tone = st.selectbox(
            "Skin Tone / Ethnicity Guidance",
            list(desc_skin_tone.keys()),
            disabled=st.session_state.repopulate_people
        )
        if not st.session_state.repopulate_people:
            st.caption(f"💡 *{desc_skin_tone[skin_tone]}*")

    st.divider()

    # --- SECTION 3: ENVIRONMENT & STYLE ---
    st.subheader("3. Environment, Lighting & Rendering")
    col3, col4 = st.columns(2)

    with col3:
        time_of_day = st.selectbox("Time of Day / Lighting Scenario", list(desc_time.keys()))
        st.caption(f"💡 *{desc_time[time_of_day]}*")
        st.write("")

        artificial_light = st.selectbox("Artificial Lighting Colour Temperature", list(desc_artificial_light.keys()))
        st.caption(f"💡 *{desc_artificial_light[artificial_light]}*")
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

        color_grade = st.selectbox("Colour Grade", list(desc_color.keys()), index=1)
        st.caption(f"💡 *{desc_color[color_grade]}*")

    st.divider()

    # --- SECTION 4: CAMERA & PHOTOGRAPHER STYLE ---
    st.subheader("4. Camera & Photographer Style")
    st.write("These settings have a major impact on photorealism — especially for faces and skin.")
    col5, col6 = st.columns(2)

    with col5:
        lens_choice = st.selectbox("Lens / Focal Length", list(desc_lens.keys()))
        st.caption(f"💡 *{desc_lens[lens_choice]}*")
        st.write("")

    with col6:
        photographer_style = st.selectbox("Photographer / Editorial Style", list(desc_photographer.keys()))
        st.caption(f"💡 *{desc_photographer[photographer_style]}*")
        st.write("")

    # ==========================================================================
    # GENERATE BUTTON
    # ==========================================================================
    st.write("")
    if st.button("🎯 Generate Image Prompt", type="primary"):

        valid_mat_changes = [c for c in st.session_state.material_changes if c["from"].strip() and c["to"].strip()]

        # --- Strip parenthetical descriptions for clean prompt text ---
        clean_time = time_of_day.split(" (")[0]
        clean_weather = weather.split(" (")[0]
        clean_artificial = artificial_light.split(" (")[0]
        clean_render = rendering_style.split(" (")[0]
        clean_shadow = shadow_quality.split(" (")[0]
        clean_color = color_grade.split(" (")[0]
        clean_lens = lens_choice.split(" —")[0]

        # --- Extract approximate focal length mm for camera block ---
        focal_mm_map = {
            "24mm": "24mm",
            "35mm": "35mm",
            "50mm": "50mm",
            "85mm": "85mm",
            "16mm": "16mm"
        }
        focal_mm = next((v for k, v in focal_mm_map.items() if k in lens_choice), "35mm")

        # ==========================================
        # BLOCK 1: BASE CONSTRAINT
        # ==========================================
        prompt = (
            "**[BASE CONSTRAINT]**\n"
            f"- ABSOLUTE STANDARD: The output must be indistinguishable from an editorial photograph "
            f"published in Architectural Digest or Wallpaper* magazine. "
            f"Style: {photographer_style}.\n"
            f"- Treat the uploaded image as a strict compositional and geometric reference only. "
            f"Reconstruct every element as a physically real, photographic {scene_type.lower()} scene. "
            "Replace all illustrative, stylised, or synthetic CGI qualities with physically plausible "
            "forms, proportions, and surface behaviour.\n"
            "- PERSPECTIVE LOCK: Maintain the camera angle, focal length, horizon line, and field of "
            "view precisely as shown in the reference. Do not reframe, zoom, or crop.\n"
            "- The final image must read unmistakably as a photograph captured by a real camera — "
            "not a digital illustration, 3D render, or AI composite.\n\n"
        )

        # ==========================================
        # BLOCK 2: CAMERA & LENS
        # ==========================================
        prompt += (
            "**[CAMERA & LENS]**\n"
            f"- Shot on a Sony A7R V full-frame mirrorless camera with a {focal_mm} prime lens. "
            "ISO 400, 1/125s shutter speed. RAW file with natural, unprocessed colour science.\n"
            f"- Lens characteristics: Very subtle chromatic aberration at high-contrast edges, "
            "natural vignetting toward the corners, and slight barrel distortion consistent with "
            f"a {focal_mm} prime. Bokeh is smooth and organic with circular aperture blades — "
            "not artificial or over-rendered.\n"
            "- Sensor grain: Fine luminance grain visible in shadow regions and smooth tonal areas, "
            "consistent with native ISO 400. This is analogue-style film grain structure, "
            "not digital noise.\n"
            "- Depth of field: Natural and physically accurate for the lens and aperture. "
            "Foreground elements that break the focal plane show natural, gradual blur falloff.\n\n"
        )

        # ==========================================
        # BLOCK 3: LIGHTING & FIXTURES
        # ==========================================
        prompt += "**[LIGHTING & FIXTURES]**\n"

        if time_of_day == "Evening Party (Moody, Downlights OFF)":
            prompt += (
                "- The lighting scenario is an intimate, moody evening party atmosphere at night.\n"
                "- All overhead ceiling downlights and bright spotlights are completely turned OFF. "
                "The space is illuminated only by the existing low-level ambient lighting, floor lamps, "
                "and indirect cove lighting present in the design. Do not add string lights or party décor.\n"
            )
        else:
            prompt += f"- Environmental / natural lighting scenario: {clean_time}.\n"
            if "Night" in time_of_day or "Twilight" in time_of_day:
                prompt += (
                    "- Maintain the exact physical design of all existing lighting fixtures. "
                    "Do not alter their shape or position. Increase the luminosity and glow of "
                    "existing architectural lights to beautifully illuminate the space.\n"
                )
            else:
                if scene_type == "Interior":
                    prompt += (
                        f"- The interior is lit naturally by {clean_time.lower()} streaming in through "
                        "the windows, balanced with existing interior fixtures at natural output levels.\n"
                    )
                else:
                    prompt += (
                        f"- Utilise natural environmental light matching {clean_time.lower()}. "
                        "Maintain existing fixture geometry perfectly without adding new artificial lights.\n"
                    )

        if clean_artificial != "Match Natural Environment":
            prompt += (
                f"- CRITICAL COLOUR TEMPERATURE: All artificial interior lighting fixtures "
                f"(pendant globes, downlights, cove lighting, sconces) must specifically emit "
                f"a {clean_artificial.lower()} colour temperature. This must be visually consistent "
                "across every fixture in the scene.\n"
            )

        prompt += (
            "- Apply natural shadow falloff, accurate surface reflections, and subtle exposure "
            "variation (natural vignetting) across the full scene.\n"
        )

        if clean_render != "Standard Photorealistic PBR":
            prompt += (
                f"- Rendered with {clean_render.lower()} and full global illumination to ensure "
                "accurate, natural light bounce and interreflection between surfaces.\n"
            )

        if clean_shadow != "Standard realistic shadows":
            prompt += f"- Shadow quality: {clean_shadow.lower()}.\n"

        prompt += (
            "- CRITICAL — LIGHT CONSISTENCY ON FACES AND BODIES: The direction, colour temperature, "
            "and intensity of light falling on all human faces and bodies must match the scene's "
            "primary light source precisely. If sunlight enters from the left, the left side of "
            "every face must be bright and warm; the right side in natural shadow with correct "
            "cool fill. No subject may appear lit by a different or separate light source. "
            "Zero compositing artefacts.\n\n"
        )

        # ==========================================
        # BLOCK 4: PHYSICAL GEOMETRY & MATERIALS
        # ==========================================
        prompt += "**[PHYSICAL GEOMETRY & MATERIALS]**\n"

        if st.session_state.analysis_text:
            prompt += (
                f"- The precise physical {scene_type.lower()} scene consists of: "
                f"{st.session_state.analysis_text}\n"
            )

        if valid_mat_changes:
            prompt += (
                "- Retain all original architectural materials perfectly, EXCEPT for the following "
                "explicit replacements:\n"
            )
            for change in valid_mat_changes:
                prompt += f"  * REPLACE '{change['from']}' WITH '{change['to']}'\n"
        else:
            prompt += "- Retain all original architectural materials perfectly.\n"

        prompt += (
            "- MATERIAL PHYSICS: All surfaces must exhibit physically accurate light response. "
            "Glass has internal reflections and slight transmission distortion. Metal shows "
            "directional brushing or casting grain. Stone and timber have micro-surface variation — "
            "no visible tiling pattern artefacts. Fabric has visible weave structure and soft "
            "draping shadows at folds.\n"
            "- SURFACE REALISM: Apply natural surface imperfections to all materials — "
            "fingerprints near glass handles, slight edge wear on high-traffic flooring, "
            "natural dust settling on horizontal ledges. Not dirty — lived-in and authentic.\n"
            "- True-to-life textures throughout: wood grain, metal brushing, plastic sheen, "
            "glass reflectivity, and stone granularity must all be physically plausible.\n\n"
        )

        # ==========================================
        # BLOCK 5: SUBJECTS & PEOPLE
        # ==========================================
        if repopulate_rendered_people:
            prompt += (
                "**[SUBJECTS & PEOPLE: REPOPULATE EXISTING FIGURES]**\n"
                "- CRITICAL — COUNT LOCK: Count the exact number of people visible in the uploaded "
                "image. Replace ONLY that exact number of people. Do NOT add any additional figures. "
                "Do NOT remove any existing figures. The total human count in the output must be "
                "identical to the total human count in the input image. This is non-negotiable.\n"
                "- Identify each person currently present in the original image by their position "
                "and scale. Paint over each one entirely with a high-end, photorealistic human "
                "subject placed in the exact same location.\n"
                "- DEMOGRAPHIC INFERENCE: Analyse the visual cues of each original figure "
                "(hair length and colour, clothing style, skirts vs. trousers, body shape and scale) "
                "to infer their intended demographic, gender, and approximate age. "
                "Preserve these inferred demographics precisely in the replacement subjects.\n"
                "- POSITION & SCALE LOCK: Maintain the exact position, scale, and pose of every "
                "person precisely as they appear in the original render. Do not move, resize, or "
                "repose any figure.\n"
                "- FACES: Each face must exhibit physically accurate subsurface scattering — soft "
                "light penetrating the dermis, warm glow visible at earlobes, nostrils, and "
                "fingertips. Natural skin texture with visible pore structure, fine surface hairs, "
                "and subtle anatomical asymmetry. Eyes must have specular catchlights matching the "
                "dominant light source in position and colour. Natural scleral vein detail, correct "
                "iris depth and translucency. Lips show natural moisture variation. "
                "No airbrushing, no smoothing filters, no uncanny valley symmetry — "
                "natural imperfection is what makes a face believably human.\n"
                "- SKIN: Physically accurate subsurface scattering with warm undertones visible "
                "where light transmits through thin skin (earlobes, nose tip, finger webbing). "
                "Natural colour variation across each face — slightly ruddier at cheeks and nose, "
                "cooler at temples and jaw. Skin is not a uniform solid colour.\n"
                "- HAIR: Rendered at strand-level detail with natural variation in colour, sheen, "
                "and direction. Hair reacts correctly to scene lighting — translucency and "
                "scattering visible at the backlit edges of each head.\n"
                "- CLOTHING & BODY: Natural, relaxed anatomical posture. Weight distributed "
                "realistically. Clothing wrinkles and folds at joints (elbows, knees, waist). "
                "Shoes make genuine ground contact with visible, physically accurate contact shadows.\n"
                "- FINAL CHECK: Before rendering, verify the human count matches the input image "
                "exactly. If the input has 3 people, the output has 3 people. "
                "Do not invent, add, or hallucinate any additional figures under any circumstance.\n"
                f"- INTEGRATION: All subjects are fully lit by the {clean_time.lower()} lighting "
                "environment. Shadow direction on each body matches the scene's primary light "
                "source precisely. Soft natural fill light on shadow sides. "
                "Zero compositing or floating artefacts.\n\n"
            )

        elif num_people > 0:
            clean_body_language = desc_body_language[body_language]
            prompt += (
                "**[SUBJECTS & PEOPLE: ADD NEW FIGURES]**\n"
                f"- Place {num_people} photorealistic human subject(s) in the {placement}, "
                f"{facing_direction}, dressed in {attire}.\n"
                f"- SKIN TONE: {skin_tone}. {desc_skin_tone[skin_tone]}\n"
                f"- BODY LANGUAGE & ACTIVITY: {body_language}. {clean_body_language}\n"
                "- SCALE: Figures must be correctly scaled relative to the architecture, using "
                "door heights, ceiling heights, and furniture proportions as reference. "
                "No floating. Feet make genuine ground contact.\n"
                "- FACES: Each face must exhibit physically accurate subsurface scattering — soft "
                "light penetrating the dermis, warm glow visible at earlobes, nostrils, and "
                "fingertips. Natural skin texture with visible pore structure, fine surface hairs, "
                "and subtle anatomical asymmetry. Eyes must have specular catchlights matching the "
                "dominant light source in position and colour. Natural scleral vein detail, correct "
                "iris depth and translucency. Lips show natural moisture variation. "
                "No airbrushing, no smoothing filters, no uncanny valley symmetry — "
                "natural imperfection is what makes a face believably human.\n"
                "- SKIN: Physically accurate subsurface scattering with warm undertones visible "
                "where light transmits through thin skin (earlobes, nose tip, finger webbing). "
                "Natural colour variation across each face — slightly ruddier at cheeks and nose, "
                "cooler at temples and jaw. Skin is not a uniform solid colour.\n"
                "- HAIR: Rendered at strand-level detail with natural variation in colour, sheen, "
                "and direction. Hair reacts correctly to scene lighting — translucency and "
                "scattering visible at the backlit edges of each head.\n"
                "- CLOTHING & BODY: Natural, relaxed anatomical posture. Weight distributed "
                "realistically. Clothing wrinkles and folds at joints (elbows, knees, waist). "
                "Shoes make genuine ground contact with visible, physically accurate contact shadows.\n"
                f"- INTEGRATION: Subjects are fully integrated into the {clean_time.lower()} "
                "lighting environment. Shadow direction on each body matches the scene's primary "
                "light source precisely. Soft natural fill light on shadow sides. "
                "Zero compositing or floating artefacts.\n\n"
            )

        else:
            prompt += (
                "**[SUBJECTS & PEOPLE]**\n"
                "- No human subjects present. Focus entirely on the architecture, materials, "
                "and environment.\n\n"
            )

        # ==========================================
        # BLOCK 6: ATMOSPHERE & FINAL COLOUR GRADE
        # ==========================================
        prompt += "**[ATMOSPHERE & FINAL IMAGE]**\n"

        if clean_weather != "Clear / Crisp Air":
            if scene_type == "Interior":
                prompt += (
                    f"- The view through all windows and the quality of interior light reflect "
                    f"{clean_weather.lower()} conditions outside.\n"
                )
            else:
                prompt += f"- The atmospheric conditions feature {clean_weather.lower()}.\n"

        if clean_color != "Natural Realism":
            prompt += f"- Final colour grade: {clean_color}.\n"

        prompt += (
            "- The final image is grounded in photographic reality: physically accurate depth of "
            "field, natural lens imperfections, fine sensor grain in shadows, and no AI softness, "
            "bloom, or over-sharpening.\n"
            "- OUTPUT STANDARD: If this image were shown alongside real editorial architecture "
            "photography, it must be indistinguishable from the real photographs.\n"
        )

        # ==========================================
        # DISPLAY & SAVE
        # ==========================================
        st.success("✅ Copy this prompt into Google Flow:")
        st.code(prompt)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] IMAGE PROMPT:\n{prompt}\n\n{'='*60}\n\n"


# =============================================================================
# TAB 2: VIDEO GENERATION
# =============================================================================
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
        depth_of_field_video = st.selectbox("Depth of Field (Focus)", [
            "Deep Focus (f/8+ style, entire scene is sharp)",
            "Shallow Focus (Subject is sharp, background beautifully blurred/bokeh)",
            "Shallow Focus (Background is sharp, foreground subjects blurred)",
            "Rack Focus (Focus smoothly shifts from foreground to background)"
        ])

    if st.button("🎬 Generate Video Prompt", type="primary"):
        vid_prompt = (
            "**[CAMERA MOVEMENT]**\n"
            f"- Movement: {camera_motion}, executed at {video_speed.lower()}.\n"
            "- Camera is mounted on a perfectly smooth mechanical slider and stabilised gimbal. "
            "Zero camera shake, no handheld movement, no walking bounce. "
            "Perfectly fluid, cinema-grade motion throughout.\n\n"

            "**[SUBJECT MOTION]**\n"
            f"- The subjects maintain a {walk_speed}. "
            "Natural weight shift, realistic arm swing, clothing moves with genuine physics. "
            "Hair and fabric respond to any ambient airflow in the scene.\n\n"

            "**[LENS & FOCUS]**\n"
            f"- The lens uses {depth_of_field_video.lower()}. "
            "Bokeh is organic and smooth — not artificial or over-rendered. "
            "Focus transitions (if applicable) are smooth and motivated, not mechanical.\n\n"

            "**[PERSISTENCE & PHYSICS]**\n"
            "- Maintain exact architectural geometry, original lighting conditions, material "
            "appearance, and floor reflections precisely from the starting frame throughout "
            "the entire video duration.\n"
            "- Natural, physics-based ambient movement only: gentle fabric movement, "
            "realistic water ripple (if applicable), natural tree or plant sway.\n"
            "- Zero temporal flickering, no material or colour shifts between frames.\n\n"

            "**[OUTPUT STANDARD]**\n"
            "- The final video must read as a professionally filmed architectural cinematography "
            "piece — indistinguishable from a real camera crew on location.\n"
        )

        st.success("✅ Copy this prompt into Google Flow Video:")
        st.code(vid_prompt)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.prompt_history += f"[{timestamp}] VIDEO PROMPT:\n{vid_prompt}\n\n{'='*60}\n\n"
