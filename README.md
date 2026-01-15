# 🚀 FitLife Pro
### Your Intelligent Personal Health & Nutrition Assistant

FitLife Pro is a comprehensive, standalone **Streamlit** application designed to help you track your nutrition, hydration, fitness, and health symptoms. It goes beyond simple logging by using scientific formulas (Mifflin-St Jeor, MET Values) to provide accurate data and actionable insights.

---

## ✨ Features

### 🍎 Smart Nutrition Tracker
*   **Macro Tracking**: Automatically calculates Calories, Protein, Carbs, and Fats.
*   **Database Integration**: Built-in support for Indian Food Nutrition data.
*   **Custom Foods**: Add your own custom meals and recipes to the database.
*   **Meal Planner**: Generates simple meal plans based on your calorie budget.

### 💧 Advanced Hydration Analytics
*   **Effective Hydration**: Not all liquids are equal! FitLife Pro calculates "Effective Volume" (e.g., Coffee logs as 90% water, Alcohol as 80%).
*   **Visual Goals**: Daily progress bars and beverage breakdown charts.

### 🏃 Fitness & Activity
*   **MET-Based Burn**: Calculates calories burnt based on specific activity types and duration using Metabolic Equivalent of Task (MET) values.
*   **Workout Log**: Keep a history of your daily exercises.

### 🩺 AI Health Advisor
*   **Symptom Checker**: Select symptoms to view severity, estimated recovery time, and possible causes.
*   **Holistic Advice**: Get dietary recommendations ("Foods to Avoid", "Preferred Meals") and home remedies for common ailments.

### 📊 Interactive Dashboard
*   **Real-time Analytics**: Powered by **Plotly** for beautiful, interactive charts.
*   **Weekly Summaries**: Track your calorie trends week-over-week.
*   **Smart Insights**: "AI" logic that detects patterns (e.g., "Late Night Snacking", "Low Protein Breakfast") and alerts you.

---

## 🛠️ Installation & Setup

1.  **Clone or Download** this repository.
2.  **Install Dependencies**:
    Ensure you have Python installed. Run the following command to install required libraries:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `streamlit`, `pandas`, `numpy`, `plotly`*

3.  **Run the App**:
    Navigate to the project folder and run user interface controller:
    ```bash
    streamlit run app.py
    ```

---

## 📂 Project Structure

*   **`app.py`** (Main Controller):
    *   Handles user authentication (profile check).
    *   Manages detailed navigation (Sidebar configuration).
    *   Routing logic for different views (Dashboard, Logs, Settings).

*   **`newback.py`** (Backend Logic & UI):
    *   Contains all business logic (BMR calculations, Data logging).
    *   Manages CSV file selection and data integrity (`load_data_safe`).
    *   Renders specific UI components (Charts, Forms, Health Advisor).

*   **Data Files (Auto-Generated)**:
    *   The app uses a localized file system (`.csv` and `.json`) to store your data.
    *   *No external database setup required!*

---

## 📸 Usage Tips

*   **First Run**: You will be prompted to set up your profile (Age, Weight, Height, Goal). This is crucial for calculating your Calorie and Macro targets.
*   **Reset Data**: You can reset your logs from the `Settings` menu if you want to start fresh.
*   **Safe Mode**: The app is built to be resilient. If a log file is deleted, the app will automatically recreate it without crashing.

---

## 📜 License
This project is for educational and personal use.
