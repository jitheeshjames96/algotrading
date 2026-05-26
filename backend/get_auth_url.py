from fyers_apiv3 import fyersModel

# Replace with your actual credentials
client_id = "CRCZAQEUZS-100"
secret_key = "JIFIPR160Z"
redirect_uri = "http://127.0.0.1:5000/"

# Initialize Session
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type="code",
    grant_type="authorization_code"
)

# Generate and print the URL to open in your browser
print("Open this URL in your browser:", session.generate_authcode())
