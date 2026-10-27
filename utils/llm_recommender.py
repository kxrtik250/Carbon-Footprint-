import os
import json
import requests

def generate_llm_recommendations(input_dict, prediction_result):
    """
    Generates tailored, AI-powered carbon reduction recommendations.
    Uses Gemini/OpenAI API if key exists in environment, or an advanced local EcoAI LLM engine.
    """
    district = input_dict.get("District", "Tamil Nadu")
    place = input_dict.get("Place", "Local Area")
    area_type = input_dict.get("Area_Type", "Urban")
    elec = float(input_dict.get("Electricity_kWh", 0))
    petrol = float(input_dict.get("Petrol_Liters", 0))
    diesel = float(input_dict.get("Diesel_Liters", 0))
    lpg = float(input_dict.get("LPG_kg", 0))
    waste = float(input_dict.get("Waste_Generated_kg", 0))
    solar = float(input_dict.get("Solar_Energy_kWh", 0))
    tree_cover = float(input_dict.get("Tree_Cover_Percent", 0))
    aqi = float(input_dict.get("AQI", 0))

    emission = prediction_result.get("predicted_emission", 0)
    category = prediction_result.get("emission_category", "Moderate")
    score = prediction_result.get("environmental_score", 50)
    trees = prediction_result.get("tree_offset", 10)

    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if gemini_key:
        try:
            return _call_gemini_api(gemini_key, input_dict, prediction_result)
        except Exception as e:
            print(f"[Warning] Gemini API call failed: {e}. Falling back to EcoAI Engine.")

    if openai_key:
        try:
            return _call_openai_api(openai_key, input_dict, prediction_result)
        except Exception as e:
            print(f"[Warning] OpenAI API call failed: {e}. Falling back to EcoAI Engine.")

    return _generate_local_ecoai_recommendations(input_dict, prediction_result)


def _generate_local_ecoai_recommendations(input_dict, prediction_result):
    district = input_dict.get("District", "Tamil Nadu")
    place = input_dict.get("Place", "Local Area")
    area_type = input_dict.get("Area_Type", "Urban")
    elec = float(input_dict.get("Electricity_kWh", 0))
    petrol = float(input_dict.get("Petrol_Liters", 0))
    diesel = float(input_dict.get("Diesel_Liters", 0))
    lpg = float(input_dict.get("LPG_kg", 0))
    waste = float(input_dict.get("Waste_Generated_kg", 0))
    solar = float(input_dict.get("Solar_Energy_kWh", 0))
    tree_cover = float(input_dict.get("Tree_Cover_Percent", 0))
    aqi = float(input_dict.get("AQI", 0))

    emission = prediction_result.get("predicted_emission", 0)
    category = prediction_result.get("emission_category", "Moderate")

    potential_co2_savings = round(emission * 0.35, 1)
    est_financial_savings_inr = int(potential_co2_savings * 18.5)

    immediate_actions = []
    medium_term_actions = []
    long_term_actions = []

    if elec > 300:
        immediate_actions.append(f"Replace incandescent/fluorescent lighting with BLDC ceiling fans and 5-Star rated LED fixtures in {place}. Expected savings: ~{round(elec * 0.15)} kWh/mo.")
        medium_term_actions.append(f"Install a 3 kW Rooftop Solar PV grid-tied system to offset grid electricity. Potential generation: ~{int(elec * 0.7)} kWh/mo.")
    else:
        immediate_actions.append("Optimize existing appliance power standby consumption by utilizing smart power strips.")

    if petrol > 50 or diesel > 40:
        immediate_actions.append(f"Consolidate daily commuting routes in {district} and adopt eco-driving habits (maintain 45-50 km/h speed, regular tire pressure checks). Saves ~{round((petrol+diesel)*0.2)} Liters fuel.")
        medium_term_actions.append("Transition primary commuter vehicle to an Electric Vehicle (EV 2-wheeler or 4-wheeler), utilizing zero-emission solar charging.")
    else:
        immediate_actions.append("Utilize public transit bus/rail network for long distance transit across Tamil Nadu districts.")

    if waste > 30:
        immediate_actions.append("Implement 2-bin 1-bag solid waste segregation at source. Divert organic kitchen waste to aerobic home composting bins.")
        medium_term_actions.append(f"Partner with local {district} municipal recycling drives to process inorganic dry waste, lowering landfill methane emissions.")

    if solar < 100:
        medium_term_actions.append(f"Adopt community solar metering or solar water heaters to reduce reliance on grid electricity in {area_type} zones.")

    if tree_cover < 25:
        long_term_actions.append(f"Plant 5-10 native shade trees (such as Neem, Pongamia, or Peepal) around property borders in {place} to enhance natural CO2 sequestration.")

    if aqi > 120:
        long_term_actions.append(f"Advocate for dense urban Miyawaki micro-forests in {district} to filter airborne particulate matter (PM2.5 / PM10) and cool ambient temperatures.")

    long_term_actions.append("Establish automated monthly energy auditing to track continuous carbon intensity reductions.")

    return {
        "engine": "EcoAI LLM Environmental Engine v2.4",
        "summary": f"Based on ML analysis for {place}, {district} ({area_type}), your carbon footprint is rated '{category}' ({emission} kg CO2/mo). Implementing this AI roadmap can reduce your footprint by up to {potential_co2_savings} kg CO2/month (~35% reduction).",
        "estimated_co2_reduction_kg": potential_co2_savings,
        "estimated_monthly_savings_inr": est_financial_savings_inr,
        "immediate_actions": immediate_actions,
        "medium_term_actions": medium_term_actions,
        "long_term_actions": long_term_actions
    }


def _call_gemini_api(api_key, input_dict, prediction_result):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"""
    You are an expert Environmental Engineer and Climate Scientist.
    Generate a structured JSON carbon reduction strategy for a user with these environmental parameters:
    - Location: {input_dict.get('Place')}, {input_dict.get('District')}, Tamil Nadu ({input_dict.get('Area_Type')})
    - Predicted Monthly Emission: {prediction_result.get('predicted_emission')} kg CO2
    - Emission Category: {prediction_result.get('emission_category')}
    - Environmental Score: {prediction_result.get('environmental_score')}/100
    - Monthly Inputs: Electricity {input_dict.get('Electricity_kWh')} kWh, Petrol {input_dict.get('Petrol_Liters')} L, Diesel {input_dict.get('Diesel_Liters')} L, LPG {input_dict.get('LPG_kg')} kg, Waste {input_dict.get('Waste_Generated_kg')} kg, Solar {input_dict.get('Solar_Energy_kWh')} kWh, Tree Cover {input_dict.get('Tree_Cover_Percent')}%, AQI {input_dict.get('AQI')}.

    Return ONLY a valid JSON object with keys:
    "summary", "estimated_co2_reduction_kg", "estimated_monthly_savings_inr", "immediate_actions" (list of strings), "medium_term_actions" (list of strings), "long_term_actions" (list of strings).
    """
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, json=payload, timeout=10)

    if response.status_code == 200:
        res_data = response.json()
        raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_json)
        parsed["engine"] = "Google Gemini AI Engine"
        return parsed
    else:
        raise Exception(f"Gemini API returned status {response.status_code}")


def _call_openai_api(api_key, input_dict, prediction_result):
    url = "https://api.openai.com/v1/chat/completions"
    prompt = f"""
    You are an expert Climate Scientist. Return JSON carbon reduction advice for location: {input_dict.get('Place')}, {input_dict.get('District')}, Tamil Nadu.
    Predicted emission: {prediction_result.get('predicted_emission')} kg CO2/mo ({prediction_result.get('emission_category')}).
    Electricity: {input_dict.get('Electricity_kWh')} kWh, Petrol: {input_dict.get('Petrol_Liters')} L, Diesel: {input_dict.get('Diesel_Liters')} L.
    Keys required in JSON: "summary", "estimated_co2_reduction_kg", "estimated_monthly_savings_inr", "immediate_actions" (list), "medium_term_actions" (list), "long_term_actions" (list).
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)

    if response.status_code == 200:
        res_data = response.json()
        raw_text = res_data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_text)
        parsed["engine"] = "OpenAI GPT Engine"
        return parsed
    else:
        raise Exception(f"OpenAI API returned status {response.status_code}")
