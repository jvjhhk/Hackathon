# AgriShield AI – Project Specification Sheet

**Project Name:** AgriShield AI  
**Tagline:** Predict. Protect. Produce.  
**Project Type:** AI-powered Smart Farming & Climate Risk Protection System  
**Purpose:** Help farmers make better farming decisions using AI, weather data and IoT sensors.

## 1. Project Objective

Develop a smart farming web application that helps farmers monitor weather conditions, understand climate risks, manage irrigation and receive AI-powered farming recommendations.

The application must have a simple, modern interface that is easy for farmers to understand and use.

## 2. Main Features

### Module 1: Farmer Dashboard
- Display current weather information.
- Display temperature, humidity and rainfall.
- Show selected crop and location.
- Display soil moisture level.
- Show important farming alerts.
- Provide an overview of farm conditions.

### Module 2: AI Crop Advisor
- Allow farmers to enter soil type, location and available soil information.
- Recommend suitable crops.
- Provide basic crop care recommendations.
- Display fertilizer and watering suggestions.
- Explain why a crop is recommended.

### Module 3: Climate Risk Predictor
- Retrieve weather information using a weather API.
- Analyse upcoming rainfall and temperature conditions.
- Identify potential drought, heavy rainfall and heat risks.
- Display risk levels: Low, Medium and High.
- Generate alerts and recommended precautions.

### Module 4: Smart Irrigation
- Read soil moisture data from an ESP32 and soil moisture sensor.
- Display moisture percentage on the dashboard.
- Identify whether the soil is dry, normal or wet.
- Recommend whether irrigation is needed.
- Provide a simulated sensor mode if physical hardware is unavailable.

### Module 5: Market Price Intelligence
- Display crop market prices.
- Allow farmers to select a crop.
- Display available market price information.
- Compare prices across available markets.
- Show price trends when historical data is available.

### Module 6: Malayalam AI Farming Assistant
- Provide a chat interface for farmers.
- Allow questions in Malayalam and English.
- Generate simple farming recommendations.
- Answer questions about crops, irrigation, weather and farming practices.
- Display responses in the farmer's selected language.
- Support voice input and text-to-speech where available.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js |
| Styling | Tailwind CSS |
| Backend | Python FastAPI |
| AI/ML | Python, Scikit-learn |
| Database | PostgreSQL |
| IoT | ESP32, Soil Moisture Sensor |
| Weather | Weather API |
| Charts | Recharts |
| Communication | REST API |

## 4. Application Pages

1. **Login / Registration** – Farmer authentication.
2. **Dashboard** – Overall farm condition and alerts.
3. **Crop Advisor** – Crop recommendations.
4. **Climate Risk** – Weather analysis and risk predictions.
5. **Smart Irrigation** – Soil moisture monitoring.
6. **Market Prices** – Crop price information.
7. **AI Assistant** – Malayalam and English farming chatbot.
8. **Settings** – Farmer profile, location and language preferences.

## 5. UI / Design Requirements

- Modern and professional agricultural dashboard.
- Green, white and light-earth colour theme.
- Simple navigation sidebar.
- Responsive design for desktop and mobile.
- Easy-to-read cards, charts and status indicators.
- Use agricultural icons and visual elements.
- Malayalam language support.
- Avoid complicated technical information on farmer-facing pages.

## 6. System Workflow

1. Farmer logs into the application.
2. Farmer enters farm location and selects a crop.
3. System collects weather and soil information.
4. AI analyses the available data.
5. System generates farming recommendations.
6. Farmer receives climate and irrigation alerts.
7. Farmer can ask additional questions using the AI assistant.

## 7. Development Requirements

- Build a functional frontend and backend.
- Connect frontend and backend using REST APIs.
- Store farmer profiles and farm information in PostgreSQL.
- Use real weather API data when an API key is available.
- Support real ESP32 sensor data and simulated sensor data.
- Implement working crop recommendation logic.
- Clearly distinguish actual predictions from simulated demonstrations.
- Display meaningful error messages when APIs or sensors are unavailable.
- Keep the code modular and easy to maintain.

## 8. Hackathon MVP (Minimum Viable Product)

Prioritise these four features for the hackathon demonstration:

1. Farmer Dashboard.
2. Weather-based Climate Risk Predictor.
3. Smart Irrigation with soil moisture monitoring.
4. Malayalam AI Farming Assistant.

Other modules should be implemented as additional features if development time permits.

## 9. Expected Final Output

A working web application named **AgriShield AI** that demonstrates how AI, weather information and IoT technology can help farmers make smarter farming decisions.

**Important:** Build a complete, functional application rather than a static UI prototype. Use realistic sample data only where live integrations are unavailable, and clearly label simulated data.