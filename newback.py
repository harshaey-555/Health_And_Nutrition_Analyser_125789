
import pandas as pd
import json
import os
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
FILES = {
    "profile": "user_profile.json",
    "food_log": "food_log.csv",
    "exercise_log": "exercise_log.csv",
    "water_log": "water_log_detailed.csv",
    "weight_log": "weight_log.csv",
    "custom_food": "custom_foods.csv",
    "food_db": "Enhanced_Indian_Food_Nutrition.csv",
    "exercise_db": "Compendium_of_Physical_Activities_2024.csv",
    "symptom_db": "symptom_database.csv",
}
# Hydration Constants
HYDRATION_FACTORS = {
    "Water": 1.0, "Milk": 0.99, "Tea": 0.98, "Coffee": 0.90,
    "Juice": 0.95, "Soda": 0.90, "Alcohol": 0.80, "Sports Drink": 1.0
}


def initialize_databases():
    """Creates necessary files if they don't exist."""

    # 1. Logs
    if not os.path.exists(FILES["water_log"]):
        pd.DataFrame(columns=["Date", "Time", "Beverage", "Volume_ml", "Effective_Hydration_ml"]).to_csv(
            FILES["water_log"], index=False)

    if not os.path.exists(FILES["weight_log"]):
        pd.DataFrame(columns=["Date", "Weight"]).to_csv(FILES["weight_log"], index=False)

    if not os.path.exists(FILES["food_log"]):
        pd.DataFrame(
            columns=["Date", "Time", "Dish", "Meal Type", "Quantity", "Calories", "Protein", "Carbs", "Fats"]).to_csv(
            FILES["food_log"], index=False)

    if not os.path.exists(FILES["exercise_log"]):
        pd.DataFrame(columns=["Date", "Time", "Activity", "Duration", "Calories Burnt"]).to_csv(FILES["exercise_log"],index=False)



def load_data_safe(filepath):
    """Safely loads CSVs handling empty files."""
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            if df.empty: return None
            return df
        except pd.errors.EmptyDataError:
            return None
    return None

def save_profile(name, age, gender, height, weight, activity, goal, water_goal):
    # BMR Calculation (Mifflin-St Jeor)
    if gender == "Male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    act_map = {"Sedentary": 1.2, "Lightly": 1.375, "Moderately": 1.55, "Very": 1.725, "Super": 1.9}
    tdee = bmr * act_map.get(activity.split()[0], 1.2)

    # Goal Adjustment
    if goal == "Weight Loss":
        target, macros = tdee - 500, (40, 40, 20)
    elif goal == "Weight Gain":
        target, macros = tdee + 500, (50, 25, 25)
    elif goal == "Muscle Gain":
        target, macros = tdee + 250, (45, 35, 20)
    else:
        target, macros = tdee, (50, 20, 30)

    rec_prot = int((target * (macros[1] / 100)) / 4)

    profile = {
        "Name": name, "Age": age, "Gender": gender, "Height": height,
        "Start_Weight": weight, "Current_Weight": weight,
        "Activity": activity, "Goal": goal,
        "Targets": {"Calories": int(target), "Protein": rec_prot, "Water": water_goal, "Macros_Split": macros}
    }

    with open(FILES["profile"], "w") as f:
        json.dump(profile, f)

    # Initialize Weight Log
    if not os.path.exists(FILES["weight_log"]) or os.stat(FILES["weight_log"]).st_size == 0:
        pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Weight": weight}]).to_csv(FILES["weight_log"],
                                                                                               index=False)
    return profile


def load_profile():
    if os.path.exists(FILES["profile"]):
        with open(FILES["profile"], "r") as f:
            profile = json.load(f)
        
        if "Start_Weight" not in profile:
            profile["Start_Weight"] = profile.get("Weight", 70)
            profile["Current_Weight"] = profile.get("Weight", 70)
            with open(FILES["profile"], "w") as f: json.dump(profile, f)
        return profile
    return None

def log_data(file, data_dict):
    df_new = pd.DataFrame([data_dict])
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df_new.to_csv(file, index=False)
    else:
        df_new.to_csv(file, mode='a', header=False, index=False)

def log_beverage_advanced(date_obj, time_obj, beverage, volume):
    factor = HYDRATION_FACTORS.get(beverage, 1.0)
    eff_vol = volume * factor
    log_data(FILES["water_log"], {
        "Date": date_obj.strftime("%Y-%m-%d"),
        "Time": time_obj.strftime("%H:%M:%S"),
        "Beverage": beverage, "Volume_ml": volume, "Effective_Hydration_ml": eff_vol
    })
    st.success("Logged!")



def load_all_databases():
    df_food = load_data_safe(FILES["food_db"])
    df_custom = load_data_safe(FILES["custom_food"])

    if df_food is not None and df_custom is not None:
        df_food = pd.concat([df_custom, df_food], ignore_index=True)
    elif df_custom is not None:
        df_food = df_custom

    df_ex = load_data_safe(FILES["exercise_db"])
    df_sym = load_data_safe(FILES["symptom_db"])

    
    if df_food is not None and "Diet" not in df_food.columns:
        df_food["Diet"] = df_food["Dish Name"].apply(
            lambda x: "Non-Veg" if any(k in str(x).lower() for k in ["chicken", "egg", "fish", "mutton"]) else "Veg")

    return df_food, df_ex, df_sym
def get_daily_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    stats = {"eaten": 0, "protein": 0, "burnt": 0}

    df_food = load_data_safe(FILES["food_log"])
    if df_food is not None:
        day = df_food[df_food["Date"] == today]
        stats["eaten"] = day["Calories"].sum()
        stats["protein"] = day["Protein"].sum()

    df_ex = load_data_safe(FILES["exercise_log"])
    if df_ex is not None:
        day = df_ex[df_ex["Date"] == today]
        stats["burnt"] = day["Calories Burnt"].sum()
    return stats


def show_food_log(df_food):
    st.title("🍎 Nutrition Logger")
    tab1, tab2 = st.tabs(["Log Meal", "Add Custom Food"])

    with tab1:
        c_d, c_t, c_m = st.columns(3)
        with c_d: log_date = st.date_input("Date", datetime.now())
        with c_t: log_time = st.time_input("Time", datetime.now())
        with c_m: meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
        st.divider()

        search = st.text_input("Search Database", placeholder="Type 'Paneer', 'Rice', 'Chicken'...")
        if search and df_food is not None:
            matches = df_food[df_food["Dish Name"].str.lower().str.contains(search.lower())]
            if not matches.empty:
                dish = st.selectbox("Select Dish", matches["Dish Name"].unique())
                sel = df_food[df_food["Dish Name"] == dish].iloc[0]
                qty = st.number_input("Quantity (Servings)", 0.5, 10.0, 1.0)
                cals = sel.get("Calories per Serving", 0) * qty
                st.info(f"Total: {cals:.0f} kcal | Diet: {sel.get('Diet', 'Veg')}")

                if st.button("Add to Log"):
                    log_data(FILES["food_log"], {
                        "Date": log_date.strftime("%Y-%m-%d"),
                        "Time": log_time.strftime("%H:%M:%S"),
                        "Dish": dish, "Meal Type": meal_type, "Quantity": qty,
                        "Calories": cals, "Protein": sel.get("Protein per Serving (g)", 0) * qty,
                        "Carbs": sel.get("Carbohydrates (g)", 0) * qty, "Fats": sel.get("Fats (g)", 0) * qty
                    })
                    st.success("Logged Successfully!")

    with tab2:
        with st.form("new_food"):
            nm = st.text_input("Name")
            diet = st.radio("Type", ["Veg", "Non-Veg"])
            c1, c2 = st.columns(2)
            cal = c1.number_input("Calories", 0)
            prot = c2.number_input("Protein", 0.0)
            c3, c4 = st.columns(2)
            carb = c3.number_input("Carbs", 0.0)
            fat = c4.number_input("Fats", 0.0)
            if st.form_submit_button("Save Food"):
                df = pd.DataFrame([{"Dish Name": nm, "Calories per Serving": cal, "Protein per Serving (g)": prot,
                                    "Carbohydrates (g)": carb, "Fats (g)": fat, "Diet": diet}])
                mode = 'a' if os.path.exists(FILES["custom_food"]) else 'w'
                header = not os.path.exists(FILES["custom_food"])
                df.to_csv(FILES["custom_food"], mode=mode, header=header, index=False)
                st.success("Saved!")
                st.cache_data.clear()

def show_hydration(user):
    st.title("💧 Hydration Tracker")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Log Drink")
        h_date = st.date_input("Date", datetime.now())
        h_time = st.time_input("Time", datetime.now())
        h_bev = st.selectbox("Beverage", list(HYDRATION_FACTORS.keys()))
        h_vol = st.number_input("Volume (ml)", 50, 2000, 250, step=50)
        if st.button("Log Drink"): log_beverage_advanced(h_date, h_time, h_bev, h_vol)

        st.markdown("#### Quick Add")
        if st.button("💧 250ml Water"): log_beverage_advanced(datetime.now(), datetime.now(), "Water", 250)

    with c2:
        st.subheader("History")
        df_w = load_data_safe(FILES["water_log"])
        if df_w is not None:
            d_str = h_date.strftime("%Y-%m-%d")
            df_w["Date"] = df_w["Date"].astype(str)
            day_data = df_w[df_w["Date"] == d_str]
            if not day_data.empty:
                tot = day_data["Effective_Hydration_ml"].sum()
                st.metric("Effective Hydration", f"{tot:.0f} ml", f"Goal: {user['Targets']['Water']} ml")
                st.progress(min(tot / user['Targets']['Water'], 1.0))
                st.plotly_chart(px.pie(day_data, values="Volume_ml", names="Beverage", hole=0.4),
                                use_container_width=True)
            else:
                st.info("No data for this date.")
def show_health_advisor(df_sym):
    st.title("🩺 Advanced Symptom Checker")
    if df_sym is not None:
        sym = st.selectbox("I am feeling...", ["Select..."] + sorted(df_sym["Symptom"].unique().tolist()))
        if sym != "Select...":
            res = df_sym[df_sym["Symptom"] == sym].iloc[0]
            st.info(
                f"**Severity:** {res.get('Severity Level', 'N/A')} | **Recovery:** {res.get('Time to Relief', 'N/A')}")
            c1, c2 = st.columns(2)
            with c1:
                st.warning(f"**Causes:** {res['Possible Causes']}")
                st.info(f"**Remedies:** {res['Remedies']}")
            with c2:
                st.error(f"**Avoid:** {res['Foods to Avoid']}")
                st.success(f"**Diet:** {res['Preferred Indian Meal']}")
            with st.expander("💡 Lifestyle & Home Remedies"):
                st.write(f"**Home Remedy:** {res.get('Home Remedy Option', 'N/A')}")
                st.write(f"**Tip:** {res['Tips / General Medicine']}")
                st.write(f"**Screen Time:** {res.get('Screen Time Link', 'N/A')}")

def show_fitness(user, df_ex):
    st.title("🏃 Fitness Tracker")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Log Workout")
        ex_date = st.date_input("Date", datetime.now())
        ex_time = st.time_input("Time", datetime.now())
        search_ex = st.text_input("Search Activity")
        if search_ex and df_ex is not None:
            matches = df_ex[df_ex["Description"].str.lower().str.contains(search_ex.lower())]
            if not matches.empty:
                act = st.selectbox("Activity", matches["Description"].unique())
                met = matches[matches["Description"] == act].iloc[0]["MET Value"]
                mins = st.number_input("Duration (Mins)", 10, 180, 30)
                burn = met * user["Current_Weight"] * (mins / 60)
                st.success(f"Estimated Burn: {burn:.0f} kcal")
                if st.button("Log Workout"):
                    log_data(FILES["exercise_log"],
                             {"Date": ex_date.strftime("%Y-%m-%d"), "Time": ex_time.strftime("%H:%M:%S"),
                              "Activity": act, "Duration": mins, "Calories Burnt": burn})
                    st.success("Logged!")
    with c2:
        st.subheader("History")
        df_ex_log = load_data_safe(FILES["exercise_log"])
        if df_ex_log is not None:
            st.dataframe(df_ex_log.sort_index(ascending=False), use_container_width=True)



def generate_meal_plan(df_food, target_cals, goal, diet_pref, days=3):
    plan = {}
    budgets = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}

    if diet_pref == "Vegetarian":
        df_food = df_food[df_food["Diet"] == "Veg"]

    if goal == "Muscle Gain":
        df_food = df_food.sort_values(by="Protein per Serving (g)", ascending=False)
    elif goal == "Weight Loss":
        df_food = df_food.sort_values(by="Calories per Serving", ascending=True)

    for day in range(1, days + 1):
        day_meals = []
        total_day = 0
        for meal, ratio in budgets.items():
            budget = target_cals * ratio
            candidates = df_food[
                (df_food["Calories per Serving"] >= budget - 150) & (df_food["Calories per Serving"] <= budget + 150)]
            if candidates.empty: candidates = df_food  

            selected = candidates.sample(1).iloc[0]
            qty = max(0.5, min(round(budget / selected["Calories per Serving"], 1), 3.0))
            cals = int(selected["Calories per Serving"] * qty)

            day_meals.append({
                "Type": meal, "Dish": selected["Dish Name"], "Qty": qty,
                "Unit": selected.get("Serving Unit", "svg"), "Cals": cals, "Diet": selected.get("Diet", "Veg")
            })
            total_day += cals
        plan[f"Day {day}"] = {"Meals": day_meals, "Total": total_day}
    return plan

def generate_nutrition_plan():
    with open(FILES["profile"] ,"r") as f:
        data = json.load(f)

        bmi = data["Current_Weight"] / ((data['Height'] / 100) ** 2)
        act =data["Activity"]

        calories = data["Targets"]["Calories"]
        protein = data["Targets"]["Protein"]
        macros_split = data["Targets"]["Macros_Split"]
        carb_per,prot_per,fats_per=macros_split

        protein_g = (calories * prot_per / 100) / 4  
        carbs_g = (calories * carb_per / 100) / 4
        fats_g = (calories * fats_per / 100) / 9  

        tips = []
        if bmi < 18.5:
            tips.append("Increase calorie intake with nutrient-dense foods.")
        elif bmi > 25:
            tips.append("Include more vegetables and lean protein for fat loss.")
        else:
            tips.append("Maintain balanced meals & steady exercise.")

        return {"Calories": round(calories), "Protein (g)": round(protein_g),
                "Carbs (g)": round(carbs_g), "Fats (g)": round(fats_g), "Tips": tips}


def show_analytics_ad():
    st.header("📊 Nutrition Analytics")

   
    df_log = load_data_safe(FILES["food_log"])

    if df_log is None or df_log.empty:
        st.info("No data available. Go to 'Input Meal Logs' to add data.")
        return

    df_log["Date"] = pd.to_datetime(df_log["Date"])

    
    st.subheader("📅 Daily Calorie Intake")
    
    daily_stats = df_log.groupby("Date")["Calories"].sum().reset_index()

    fig_daily = px.bar(daily_stats, x="Date", y="Calories",
                       title="Total Calories per Day",
                       color="Calories", color_continuous_scale="Blues")
    st.plotly_chart(fig_daily, use_container_width=True)

    st.divider()
    macro_colors = {
        "Protein": "#FF9999",  
        "Carbs": "#99CCFF",    
        "Fats": "#FFCC99"      
    }

    # --- Actual Intake Pie ---
    selected_date=st.date_input("Select Date",datetime.now())
    c1,c2=st.columns(2)
    with c1:
        st.markdown("#### **Actual Intake**")
        filter=df_log["Date"]==pd.to_datetime(selected_date)
        day_data=df_log[filter]
        if day_data is not None and not day_data.empty:
            day_prot=day_data["Protein"].sum()
            day_carbs=day_data["Carbs"].sum()
            day_fat=day_data["Fats"].sum()
            total_p=day_prot
            total_c=day_carbs
            total_f=day_fat
        fig_pie = px.pie(
            names=["Protein", "Carbs", "Fats"],
            values=[total_p, total_c, total_f],
            title=f"Actual: {selected_date.strftime('%Y-%m-%d')}",
            hole=0.4
        )
        fig_pie.update_traces(marker=dict(colors=[macro_colors[n] for n in ["Protein","Carbs","Fats"]]),
                            showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            st.markdown("#### **Target Goal**")
            target=generate_nutrition_plan()
            prot=target["Protein (g)"]
            carbs=target["Carbs (g)"]
            fats=target["Fats (g)"]
            # --- Target Goal Pie ---
            fig_pie1 = px.pie(
                names=["Protein", "Carbs", "Fats"],
                values=[prot, carbs, fats],
                title="Recommended Goal",
                hole=0.4
            )
            fig_pie1.update_traces(marker=dict(colors=[macro_colors[n] for n in ["Protein","Carbs","Fats"]]),
                                showlegend=True)
            st.plotly_chart(fig_pie1, use_container_width=True)



    # --- CHART 3: Weekly Summaries (Bar Chart) ---
    st.subheader("wk Weekly Summaries")

    
    weekly_stats = df_log.set_index("Date").resample('W')["Calories"].sum().reset_index()

    weekly_stats["Week"] = weekly_stats["Date"].dt.strftime("Week of %Y-%m-%d")

    fig_weekly = px.bar(weekly_stats, x="Week", y="Calories",
                        title="Total Calories per Week",
                        text_auto=True,  
                        color="Calories", color_continuous_scale="Greens")

    st.plotly_chart(fig_weekly, use_container_width=True)



def show_settings(user):
    st.title("⚙️ Settings")
    with st.expander("✏️ Edit Profile"):
        new_w = st.number_input("Update Weight (kg)", value=float(user['Current_Weight']))
        new_h = st.number_input("Update Height (cm)", value=float(user['Height']))
        new_age = st.number_input("Update Age", value=int(user['Age']))
        new_act = st.selectbox("Update Activity",
                               ["Sedentary (Office)", "Lightly Active", "Moderately Active", "Very Active",
                                "Super Active"], index=0)
        new_goal = st.selectbox("Update Goal", ["Weight Loss", "Weight Gain", "Muscle Gain", "Maintain"], index=0)

        if st.button("Save Profile Changes"):
            new_profile = save_profile(user['Name'], new_age, user['Gender'], new_h, new_w, new_act, new_goal,
                         user['Targets']['Water'])
            st.session_state["user"] = new_profile
            st.success("Profile Updated!")
            st.rerun()

    st.divider()
    st.subheader("⬇️ Export Data")
    c1, c2, c3 = st.columns(3)
    if os.path.exists(FILES["food_log"]):
        with open(FILES["food_log"], "rb") as f: c1.download_button("Download Food Log", f, "food_log.csv")
    if os.path.exists(FILES["exercise_log"]):
        with open(FILES["exercise_log"], "rb") as f: c2.download_button("Download Exercise Log", f,
                                                                        "exercise_log.csv")
    if os.path.exists(FILES["weight_log"]):
        with open(FILES["weight_log"], "rb") as f: c3.download_button("Download Weight Log", f, "weight_log.csv")

    st.divider()
    if st.button("🗑️ Reset All Data (Irreversible)", type="primary"):
        for f in FILES.values():
            
            if "db" not in f and os.path.exists(f): os.remove(f)
        del st.session_state["user"]
        st.rerun()


def get_simple_streak(df_food):
    
    log_dates = set(pd.to_datetime(df['Date']).dt.date)

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

   
    if today not in log_dates and yesterday not in log_dates:
        return 0

    
    current_date = today if today in log_dates else yesterday

   
    streak = 0
    while current_date in log_dates:
        streak += 1
        current_date -= timedelta(days=1)

    return streak
def calculate_streak(df_food):
    """Calculates consecutive days logged, handling NaT errors."""
    if df_food is None or df_food.empty: return 0

   
    df_food["DateObj"] = pd.to_datetime(df_food["Date"], errors='coerce')
    valid_dates = df_food["DateObj"].dropna().dt.date.unique()

    if len(valid_dates) == 0:
        return 0

    valid_dates.sort()

    streak = 0
    check_date = datetime.now().date()

   
    if check_date not in valid_dates:
        check_date -= timedelta(days=1)
        if check_date not in valid_dates: return 0

    while check_date in valid_dates:
        streak += 1
        check_date -= timedelta(days=1)
    return streak
def show_dashboard(user):
    st.title("🏠 Your Daily Snapshot")
    stats = get_daily_stats()
    target = user['Targets']['Calories']
    net = stats['eaten'] - stats['burnt']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Calories Eaten", f"{stats['eaten']:.0f}", f"Target: {target}")
    with col2:
        st.metric("Calories Burnt", f"{stats['burnt']:.0f}", "Active")
    with col3:
        st.metric("Protein", f"{stats['protein']:.0f}g", f"Goal: {user['Targets']['Protein']}g")

    df_w = load_data_safe(FILES["water_log"])
    w_today = 0
    if df_w is not None:
        df_w["Date"] = pd.to_datetime(df_w["Date"], errors='coerce')
        today = datetime.now().strftime("%Y-%m-%d")
        w_today = df_w[df_w["Date"] == today]["Effective_Hydration_ml"].sum()
    with col4:
        st.metric("Hydration", f"{w_today:.0f} ml", f"Goal: {user['Targets']['Water']} ml")

    st.divider()

    c_ring, c_streak = st.columns([2, 1])
    with c_ring:
        st.subheader("🎯 Today's Progress")
        fig = go.Figure(go.Pie(
            labels=['Eaten', 'Remaining'],
            values=[net, max(0, target - net)],
            hole=.7, marker_colors=['#FF4B4B', '#F0F2F6'], sort=False
        ))
        fig.update_layout(
            annotations=[dict(text=f"{int(net)}<br>kcal", x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=False, height=220, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c_streak:
        df_f = load_data_safe(FILES["food_log"])
        streak = calculate_streak(df_f)
        st.subheader("🔥 Streak")
        st.metric("Consecutive Days", f"{streak} 🔥")

        st.subheader("⚖️ Weight")
        cw = user.get("Current_Weight", user["Start_Weight"])
        st.metric("Current", f"{cw} kg", delta=f"{cw - user['Start_Weight']:.1f} kg")


def generate_smart_insights():
    """Analyzes logs to generate actionable text advice."""
    insights = []

    # 1. Load Data
    user = load_profile()
    df_food = load_data_safe(FILES["food_log"])
    df_ex = load_data_safe(FILES["exercise_log"])
    df_water = load_data_safe(FILES["water_log"])

    if user is None: return ["Please create your profile first."]

   
    if df_food is not None:
        df_food["Date"] = pd.to_datetime(df_food["Date"])
        recent_days = df_food[df_food["Date"] >= (datetime.now() - timedelta(days=3))]

        if not recent_days.empty:
            avg_cal = recent_days.groupby("Date")["Calories"].sum().mean()
            target_cal = user["Targets"]["Calories"]
            diff = avg_cal - target_cal

            if diff > 500:
                insights.append(
                    f"⚠️ **High Calorie Alert:** You are averaging {avg_cal:.0f} kcal (Target: {target_cal}). Try reducing portion sizes at Dinner.")
            elif diff < -500:
                insights.append(
                    f"⚠️ **Under-eating:** You are averaging {avg_cal:.0f} kcal. You might lose muscle. Add a healthy snack like nuts or yogurt.")
            else:
                insights.append(f"✅ **Calorie Control:** You are within range of your calorie goals. Keep it up!")

   
    if df_food is not None:
       
        breakfasts = df_food[df_food["Meal Type"] == "Breakfast"]
        if not breakfasts.empty:
            avg_prot_bf = breakfasts["Protein"].mean()
            if avg_prot_bf < 15:
                insights.append(
                    f"🥩 **Protein Boost Needed:** Your breakfasts average only {avg_prot_bf:.0f}g protein. Try adding eggs, paneer, or a protein shake to start your day better.")

   
    if df_water is not None:
        df_water["Date"] = pd.to_datetime(df_water["Date"])
        today_vol = df_water[df_water["Date"].dt.date == datetime.now().date()]["Effective_Hydration_ml"].sum()
        goal_water = user["Targets"]["Water"]

        
        if datetime.now().hour > 18 and today_vol < (goal_water * 0.5):
            insights.append(
                f"💧 **Dehydration Risk:** It's late and you've only drunk {today_vol:.0f}ml. Go drink 2 glasses of water now!")

   
    if df_ex is not None:
        df_ex["Date"] = pd.to_datetime(df_ex["Date"])
        last_workout = df_ex["Date"].max()
        days_since = (datetime.now() - last_workout).days

        if days_since > 3:
            insights.append(
                f"🏃 **Get Moving:** You haven't logged a workout in {days_since} days. Even a 15-minute walk today counts!")

    
    if df_food is not None:
       
        late_night = df_food[df_food["Time"] > "22:00:00"]
        if not late_night.empty:
            insights.append(
                f"🌙 **Late Snacking:** We noticed food logs after 10 PM. Late eating can disrupt sleep and digestion. Try herbal tea instead.")

    if not insights:
        insights.append("🌟 **Great Job:** Your logs look balanced. Stick to your plan!")

    return insights



def show_ad_dashboard(user):
    
    user_name = user.get("Name", "Friend")
    st.title(f"Welcome back, {user_name}! 👋")


    st.subheader("📢 AI Action Plan for Today")

    daily_insights = generate_smart_insights()

    if not daily_insights:
        st.info("🌟 No specific alerts today. You are doing great!")
    else:
        for insight in daily_insights:
            
            if "⚠️" in insight or "Dehydration" in insight or "Risk" in insight:
                st.error(insight, icon="🚨")
            elif "✅" in insight or "Great" in insight:
                st.success(insight, icon="🏆")
            elif "Run" in insight or "Walk" in insight or "Exercise" in insight:
                st.warning(insight, icon="👟")
            else:
                st.info(insight, icon="💡")

    st.divider()

   
    st.subheader("📊 Your Progress Charts")
    show_dashboard(user) 

    
def show_health_advisor_ad(user, df_sym):
    st.title("🩺 Advanced Symptom Checker")
    
    if df_sym is None:
        st.error("Symptom database is missing or could not be loaded.")
        return

   
    name = user.get("Name", "Friend")
    st.subheader(f"How can we help you today, {name}?")

   
    symptoms_list = sorted(df_sym["Symptom"].dropna().astype(str).unique().tolist())
    
    
    sym = st.selectbox("I am currently experiencing...", ["Select a symptom..."] + symptoms_list)

    if sym != "Select a symptom...":
        
        res = df_sym[df_sym["Symptom"] == sym].iloc[0]

        
        st.divider()
        
        
        severity = res.get('Severity Level', 'Unknown')
        color_map = {"High": "red", "Moderate": "orange", "Low": "green", "Mild": "green"}
        sev_color = color_map.get(severity.split()[0], "blue") 

        
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"**Severity Level:**")
            st.markdown(f":{sev_color}[**{severity}**]") 
        with m2:
            st.markdown(f"**Est. Recovery Time:**")
            st.markdown(f"⏱️ **{res.get('Time to Relief', 'Varies')}**")

        st.divider()

        
        c1, c2 = st.columns(2, gap="medium")

        with c1:
            st.markdown("### 🧬 Medical Insights")
            
            
            with st.container(border=True):
                st.markdown("#### ❓ Possible Causes")
                st.warning(res.get('Possible Causes', 'Consult a doctor for diagnosis.'))
            
          
            with st.container(border=True):
                st.markdown("#### 💊 Suggested Remedies")
                st.info(res.get('Remedies', 'Rest and hydration are usually recommended.'))

        with c2:
            st.markdown("### 🥗 Dietary & Lifestyle")
            
            
            with st.container(border=True):
                st.markdown("#### 🚫 Foods to Avoid")
                st.error(res.get('Foods to Avoid', 'Processed and spicy foods.'))
            
            
            with st.container(border=True):
                st.markdown("#### ✅ Recommended Indian Meal")
                st.success(res.get('Preferred Indian Meal', 'Light, home-cooked meals.'))

        
        st.markdown("---")
        with st.expander("💡 Natural Home Remedies & Doctor's Tips", expanded=True):
            
            ec1, ec2 = st.columns(2)
            
            with ec1:
                st.markdown("**🏡 Home Remedy:**")
                st.write(f"_{res.get('Home Remedy Option', 'Not available')}_")
                
                st.markdown("**📱 Screen Time Advice:**")
                st.write(res.get('Screen Time Link', 'Limit screen time if necessary.'))
                
            with ec2:
                st.markdown("**🩺 General Medical Tip:**")
                st.write(f"_{res.get('Tips / General Medicine', 'Consult a specialist if symptoms persist.')}_")    

   
def show_meal_planner(user, df_food):
    st.title("🔮 AI Meal Planner")
    c1, c2 = st.columns([1, 3])
    with c1:
        days = st.slider("Days", 1, 7, 3)
        pref = st.radio("Diet", ["Vegetarian", "Non-Vegetarian"])
        if st.button("Generate Plan"):
            st.session_state["plan"] = generate_meal_plan(df_food, user['Targets']['Calories'], user['Goal'], pref,
                                                          days)
    with c2:
        if "plan" in st.session_state:
            
            if not st.session_state["plan"]:
                st.info("Meal plan logic under construction.")
            else:
                for day, det in st.session_state["plan"].items():
                    with st.expander(f"📅 {day} - {det['Total']} kcal"):
                        for m in det["Meals"]:
                            st.write(f"**{m['Type']}**: {m['Qty']} x {m['Dish']} ({m['Diet']})")
                            st.caption(f"{m['Cals']} kcal")

 
