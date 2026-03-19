import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. App Title and Setup
st.title("Architecture Animation Workflow")
st.write("Upload a render, analyze its physical properties, and generate perfect prompts.")

# 2. Sidebar for API Key (Keeps it secure and out of the main screen)
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.write("Get a free API key at [Google AI Studio](https://aistudio.google.com/)")

    if api_key:
        genai.configure(api_key=api_key)

# 3. Initialize Session State (To remember the analysis)
if "analysis_text" not in st.session_state:
    st.session_state.analysis_text = ""

# 4. Create Tabs
tab1, tab2 = st.tabs(["Step 1: Bake (Image)", "Step 2: Animate (Video)"])

# --- TAB 1: IMAGE GENERATION ---
with tab1:
    st.header("Step 1a: Analyze Original Render")
    
    # The File Uploader
    uploaded_file = st.file_uploader("Upload your clean architectural render (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Render", use_container_width=True)
        
        # Analyze Button
        if st.button("Analyze Lighting & Materials"):
            if not api_key:
                st.error("Please enter your Gemini API Key in the sidebar first!")
            else:
                with st.spinner("Analyzing image physics..."):
                    try:
                        # Call the Gemini Vision model
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = "Analyze this architectural render. Describe the primary lighting direction, the quality of the light (hard/soft, warm/cool), the main floor materials, and the perspective/camera angle. Keep it concise."
                        response = model.generate_content([prompt, image])
                        
                        # Save the result to session state so it remembers it
                        st.session_state.analysis_text = response.text
                        st.success("Analysis Complete!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
    # Show the analysis if it exists
    if st.session_state.analysis_text:
        st.info("**AI Image Analysis:**\n" + st.session_state.analysis_text)

    st.divider() # A nice visual line break

    st.header("Step 1b: Generate 'Baking' Prompt")
    
    # Dashboard ingredients
    time_of_day = st.selectbox("Time of Day", ["Match Original Image", "Morning", "Midday", "Golden Hour/Sunset", "Night"])
    num_people = st.slider("Number of People", 1, 5, 2)
    attire = st.text_input("Describe Attire", "Modern, casual business wear")
    
    if st.button("Generate Image Prompt"):
        base_prompt = f"A high-resolution photorealistic architectural photograph. "
        
        # Inject the AI's analysis so the new people match the room!
        if st.session_state.analysis_text:
             base_prompt += f"The environment has the following properties: {st.session_state.analysis_text} "
        
        base_prompt += f"Integrated seamlessly into the middle ground are {num_people} people wearing {attire}. "
        base_prompt += f"The lighting on the people must perfectly match the described environmental lighting. Crucially, they cast diffuse contact shadows and accurate reflections on the described floor materials."
            
        st.success("Copy this prompt into your Image Generator:")
        st.code(base_prompt)

# --- TAB 2: VIDEO GENERATION (Same as before) ---
with tab2:
    st.header("Step 2: Animate the Baked Image")
    camera_motion = st.selectbox("Camera Movement", ["Slow Dolly-In", "Slow Pan Right", "Static"])
    walk_speed = st.selectbox("Walking Speed", ["Casual stroll", "Brisk walk"])
    
    if st.button("Generate Video Prompt"):
        vid_prompt = f"{camera_motion} moving through the space. The subjects maintain a {walk_speed}. Maintain exact architectural geometry, original lighting, and floor reflections from the starting frame."
        st.success("Copy this prompt into Google Flow Video:")
        st.code(vid_prompt)
