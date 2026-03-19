import streamlit as st

# 1. Set the Title of your Web App
st.title("Architecture Animation Workflow")
st.write("Use this tool to generate perfectly structured prompts for your renders.")

# 2. Create Two Tabs for your Two-Step Process
tab1, tab2 = st.tabs(["Step 1: Bake (Image)", "Step 2: Animate (Video)"])

# --- TAB 1: IMAGE GENERATION ---
with tab1:
    st.header("Step 1: Add People to Static Render")
    
    # Define your dashboard ingredients (variables)
    time_of_day = st.selectbox("Time of Day", ["Morning", "Midday", "Golden Hour/Sunset", "Night"])
    num_people = st.slider("Number of People", 1, 5, 2) # Slider from 1 to 5, default 2
    attire = st.text_input("Describe Attire", "Modern, casual business wear")
    shadows = st.checkbox("Force Contact Shadows & Reflections", value=True)
    
    # The action button
    if st.button("Generate Image Prompt"):
        # This is where the magic happens: assembling the prompt based on your inputs
        base_prompt = f"A high-resolution photorealistic architectural photograph at {time_of_day}. "
        base_prompt += f"Integrated seamlessly into the middle ground are {num_people} people wearing {attire}. "
        
        if shadows:
            base_prompt += "Crucially, they cast diffuse contact shadows and subtle soft reflections on the floor, perfectly matching the global lighting. "
            
        st.success("Copy this prompt into your Image Generator:")
        st.code(base_prompt) # This displays the text in a neat, copyable box

# --- TAB 2: VIDEO GENERATION ---
with tab2:
    st.header("Step 2: Animate the Baked Image")
    
    # Define video-specific ingredients
    camera_motion = st.selectbox("Camera Movement", ["Slow Dolly-In", "Slow Pan Right", "Static / No Camera Movement"])
    walk_speed = st.selectbox("Walking Speed", ["Casual stroll", "Brisk walk", "Standing still"])
    
    if st.button("Generate Video Prompt"):
        vid_prompt = f"{camera_motion} moving through the space. The subjects maintain a {walk_speed}. "
        vid_prompt += "Maintain the exact architectural geometry, original lighting, and floor reflections from the starting frame. Subtle ambient movement in background elements."
        
        st.success("Copy this prompt into Google Flow Video:")
        st.code(vid_prompt)
