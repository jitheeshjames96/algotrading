import os
from fyers_apiv3 import fyersModel

# ==========================================
# 1. PASTE YOUR NEW CREDENTIALS HERE
# ==========================================
# Make sure your client_id ends with -100
client_id = "CRCZAQEUZS-100" 
secret_key = "JIFIPR160Z"

# ==========================================
# 2. PASTE THE AUTH CODE FROM YOUR BROWSER
# ==========================================
auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiJDUkNaQVFFVVpTIiwidXVpZCI6IjRlNTVlNTY2OGI5NTQ4NWM4N2NlNWE2ZTMxNTZlOTBmIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IkZBSjc3MTkzIiwib21zIjoiSzEiLCJoc21fa2V5IjoiYWI5NGNhNjhlOTUyNDg1NmZjZTAxMTExN2QyMDEwNjQxMjAxMjk5OGY3Y2UzMTIyZWFjODljZDQiLCJpc0RkcGlFbmFibGVkIjoiTiIsImlzTXRmRW5hYmxlZCI6Ik4iLCJhdWQiOiJbXCJkOjFcIixcImQ6MlwiLFwieDowXCIsXCJ4OjFcIixcIng6MlwiXSIsImV4cCI6MTc3OTgwNTA2OCwiaWF0IjoxNzc5Nzc1MDY4LCJpc3MiOiJhcGkubG9naW4uZnllcnMuaW4iLCJuYmYiOjE3Nzk3NzUwNjgsInN1YiI6ImF1dGhfY29kZSJ9.W-hXm1jjCHARbHrdLLAIWsFSBIl70jdv81freVkRAPE"

redirect_uri = "http://127.0.0.1:5000/"

def get_token():
    print("🔄 Contacting Fyers Auth Server...")
    
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )

    session.set_token(auth_code)

    try:
        response = session.generate_token()
        
        if response.get("s") == "ok":
            access_token = response["access_token"]
            print("\n✅ SUCCESS! Here is your brand new Access Token:\n")
            print("================================================================================")
            print(f"{access_token}")
            print("================================================================================\n")
            print("👉 Copy the massive token above.")
            print("👉 Open your .env file.")
            print("👉 Paste it as: FYERS_ACCESS_TOKEN=\"your_massive_token_here\"")
        else:
            print("\n❌ FAILED TO GENERATE TOKEN. Error from Fyers:")
            print(response)
            
    except Exception as e:
        print(f"\n❌ SCRIPT CRASHED: {str(e)}")

if __name__ == "__main__":
    if client_id == "YOUR_NEW_APP_ID-100" or auth_code == "PASTE_THE_LONG_AUTH_CODE_HERE":
        print("⚠️ WAIT: You need to open generate_token.py and paste your actual keys and auth_code first!")
    else:
        get_token()
