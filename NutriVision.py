import streamlit as st
import os
import google.generativeai as genai
from PIL import Image

# --- Set Google API key ---
os.environ["GOOGLE_API_KEY"] = ""
api_key = os.environ["GOOGLE_API_KEY"]

if not api_key:
    st.error("❌ GOOGLE_API_KEY is missing. Please set it as an environment variable.")
    st.stop()

genai.configure(api_key=api_key)

# --- Functions ---
def get_gemini_response(prompt, image_parts=None):
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        if image_parts:
            response = model.generate_content([prompt, image_parts[0]])
        else:
            response = model.generate_content(prompt)
        text = response.text.strip()
        if not text:
            raise ValueError("Empty response")
        return text
    except Exception as e:
        return "⚠️ Sorry, I didn’t quite get that. Could you try rephrasing?"

def input_image_setup(uploaded_file):
    if uploaded_file:
        bytes_data = uploaded_file.getvalue()
        return [{"mime_type": uploaded_file.type, "data": bytes_data}]
    else:
        raise FileNotFoundError("No file uploaded")

# --- Streamlit UI ---
st.set_page_config(page_title="NutriVision - Your Nutritionist Assistant", layout="wide")
st.title("🥦 NutriVision - Your AI Nutritionist")

# Welcome Message
st.info("👋 Welcome to NutriVision! Choose a mode from the sidebar to get started.")

# Sidebar for Navigation
mode = st.sidebar.radio("Choose Mode", ["🥗 Meal Analyzer", "💬 HealthBot Chat"])

# --- Meal Analyzer ---
if mode == "🥗 Meal Analyzer":
    st.markdown("### Upload your meal image for analysis:")
    input_prompt = st.text_area("Prompt (Optional)", placeholder="e.g., Focus on sugar content.")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Your Meal", use_column_width=True)

    if st.button("🔍 Analyze Meal") and uploaded_file:
        try:
            image_data = input_image_setup(uploaded_file)
            prompt = input_prompt or "Analyze the nutritional content and healthiness of this meal."
            result = get_gemini_response(prompt, image_data)
            st.subheader("🍽️ Nutrition Analysis")
            st.write(result)

            if st.button("💾 Save Result"):
                with open("NutriVision_Results.txt", "w") as file:
                    file.write(result)
                st.success("✅ Results saved successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- HealthBot Chat ---
elif mode == "💬 HealthBot Chat":
    st.markdown("### Ask HealthBot anything about your diet, wellness, or fitness!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "welcome_shown" not in st.session_state:
        st.chat_message("assistant").write("Hi! I'm your HealthBot 🤖. Ask me anything about health, nutrition, or fitness!")
        st.session_state.welcome_shown = True

    user_message = st.chat_input("Ask me something about your health!")

    if user_message:
        st.session_state.chat_history.append(("You", user_message))
        lowered = user_message.lower()

        try:
            # --- Basic Intent Recognition ---
            if any(word in lowered for word in ["bye", "exit", "quit", "thanks"]):
                response = "👋 Goodbye! Stay healthy and eat well!"
            else:
                # Try to enrich the context before calling the model
                if "protein" in lowered:
                    prompt = f"Answer the following nutritional question about protein: {user_message}"
                elif "paneer" in lowered:
                    prompt = f"Give nutritional details specifically about paneer: {user_message}"
                elif "calorie" in lowered:
                    prompt = f"Explain the calorie information: {user_message}"
                elif "exercise" in lowered or "workout" in lowered or "fitness" in lowered:
                    prompt = f"The user wants advice related to fitness: {user_message}"
                elif "diet" in lowered or "nutrition" in lowered:
                    prompt = f"The user has a dietary query: {user_message}"
                else:
                    prompt = user_message  # Let Gemini handle unknown queries intelligently

                response = get_gemini_response(prompt)

                # Fallback if still empty
                if not response or "sorry" in response.lower():
                    response = "🤔 I’m not sure what you mean. Can you rephrase or ask in a different way?"

            st.session_state.chat_history.append(("HealthBot", response))
        except Exception as e:
            st.session_state.chat_history.append(("HealthBot", f"⚠️ An error occurred: {e}"))

    for role, message in st.session_state.chat_history:
        if role == "You":
            st.chat_message("user").write(message)
        else:
            st.chat_message("assistant").write(message)
