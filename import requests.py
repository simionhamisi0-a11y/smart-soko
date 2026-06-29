import requests

url = "https://api.smart-soko.tz/v1/update"
payload = {
    "id": "001",
    "agent_name": "KUZENZA", 
    "soko_location": "Ilala",
    "zao_name": "Mahindi", 
    "bei_ya_jumla": 150000,
    "kipimo": "100kg",
    "hali_ya_soko": "inapanda",
    "tarehe_iliyoingizwa": "13/06/2026" 
    
}
headers = {"Authorization": "Bearer YOUR_TOKEN"}

try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Safiii! Data imefika kwenye table.")
    else:
        print(f"Server imekataa kwa code: {response.status_code}")
        print(f"Sababu: {response.text}")
except Exception as e:
    print(f"Duh! Kuna hitilafu: {e}")