gitimport streamlit as st
import os

from newback import FILES,initialize_databases,load_profile, save_profile, get_daily_stats, load_all_databases,show_ad_dashboard, show_food_log, show_hydration, show_fitness,show_meal_planner, show_health_advisor_ad, show_analytics_ad, show_settings

st.set_page_config(
    page_title="FitLife Pro",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)


initialize_databases()

if "user" not in st.session_state:
    st.session_state["user"] = load_profile()
user = st.session_state["user"]


if user is None:
    st.title("🚀 Welcome to FitLife Pro")
    st.markdown("### Let's build your personalized health plan.")

    with st.form("setup_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("First Name")
        gender = c1.radio("Gender", ["Male", "Female"], horizontal=True)
        age = c1.number_input("Age", 10, 100, 25)
        weight = c2.number_input("Weight (kg)", 30, 200, 70)
        height = c2.number_input("Height (cm)", 100, 250, 170)
        st.markdown("---")
        act = st.selectbox("Activity Level",
                           ["Sedentary (Office)", "Lightly Active", "Moderately Active", "Very Active", "Super Active"])
        goal = st.selectbox("Your Goal", ["Weight Loss", "Weight Gain", "Muscle Gain", "Maintain"])
        w_goal = st.number_input("Daily Water Goal (ml)", 1000, 5000, 2500)

        if st.form_submit_button("Start My Journey"):
            if name:
                save_profile(name, age, gender, height, weight, act, goal, w_goal)
            else:
                st.error("Please enter your name.")


else:
   

    df_food, df_ex, df_sym = load_all_databases()

    
    with st.sidebar:
        st.title(f"👤 {user['Name']}")
        st.caption(f"Goal: {user['Goal']}")

        page = st.radio(
            "Navigate",
            ["🏠 Dashboard", "🍎 Food Log", "💧 Hydration", "🏃 Fitness", "🔮 Meal Planner", "🩺 Health Advisor",
             "📈 Analytics", "⚙️ Settings"],
        )

        st.markdown("---")
        stats = get_daily_stats()
        net = stats['eaten'] - stats['burnt']
        target = user['Targets']['Calories']

        st.metric("Net Calories", f"{net:.0f}", delta=f"{target - net:.0f} left")
        st.progress(min(max(net / target, 0.0), 1.0))

    
    if page == "🏠 Dashboard":
        show_ad_dashboard(user)
    elif page == "🍎 Food Log":
        show_food_log(df_food)
    elif page == "💧 Hydration":
        show_hydration(user)
    elif page == "🏃 Fitness":
        show_fitness(user, df_ex)
    elif page == "🔮 Meal Planner":
        show_meal_planner(user, df_food)
    elif page == "🩺 Health Advisor":
        show_health_advisor_ad(user,df_sym)
    elif page == "📈 Analytics":
        show_analytics_ad()
    elif page == "⚙️ Settings":
        show_settings(user)
