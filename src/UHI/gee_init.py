import ee

def gee_auth():

    try:
        ee.Initialize()
        print("GEE initialized successfully")
    except:
        print("Run 'earthengine authenticate' in terminal first")
        ee.Authenticate()
        ee.Initialize()

