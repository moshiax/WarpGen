from flask import Flask, render_template, request, jsonify
import random
import httpx
import os

app = Flask(__name__)

def load_keys():
    if os.path.exists('base.txt'):
        with open('base.txt', 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_keys(new_keys):
    keys = load_keys()
    with open('base.txt', 'a') as f:
        for key in new_keys:
            f.write(f"\n{key}")

    if len(keys) + len(new_keys) > 100:
        keys.extend(new_keys)
        with open('base.txt', 'w') as f:
            for key in keys[-100:]: 
                f.write(f"\n{key}")

keys = load_keys()
gkeys = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global gkeys
    if request.method == 'POST':
        value_int = int(request.form['num_keys'])
        gkeys = []
        new_keys = []
        generate_keys(value_int, new_keys)
        save_keys(new_keys)
        return render_template('index.html', gkeys=gkeys)
    return render_template('index.html', gkeys=[])

def generate_keys(value_int, new_keys):
    global gkeys
    a = 0
    while a < value_int:
        a += 1
        try:
            headers = {
                "CF-Client-Version": "a-6.11-2223",
                "Host": "api.cloudflareclient.com",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "User-Agent": "okhttp/3.12.1",
            }

            with httpx.Client(base_url="https://api.cloudflareclient.com/v0a2223", headers=headers, timeout=30.0) as client:
                r = client.post("/reg")
                id = r.json()["id"]
                license = r.json()["account"]["license"]
                token = r.json()["token"]

                r = client.post("/reg")
                id2 = r.json()["id"]
                token2 = r.json()["token"]

                headers_get = {"Authorization": f"Bearer {token}"}
                headers_get2 = {"Authorization": f"Bearer {token2}"}
                headers_post = {"Content-Type": "application/json; charset=UTF-8", "Authorization": f"Bearer {token}"}

                json = {"referrer": f"{id2}"}
                client.patch(f"/reg/{id}", headers=headers_post, json=json)
                client.delete(f"/reg/{id2}", headers=headers_get2)

                keys = load_keys()
                key = random.choice(keys)

                json = {"license": f"{key}"}
                client.put(f"/reg/{id}/account", headers=headers_post, json=json)

                json = {"license": f"{license}"}
                client.put(f"/reg/{id}/account", headers=headers_post, json=json)

                r = client.get(f"/reg/{id}/account", headers=headers_get)
                referral_count = r.json()["referral_count"]
                license = r.json()["license"]

                client.delete(f"/reg/{id}", headers=headers_get)

                new_key_info = {
                    'referral_count': referral_count,
                    'license': license
                }
                gkeys.append(new_key_info)
                new_keys.append(license)
                print(f"Generated key {a}: {license}")
                print(f"Data Allocated: {referral_count} GB")
                print(f"License: {license}")

                yield new_key_info
        except Exception as er:
            print("Error.")
            print(er)

@app.route('/api/generate_keys', methods=['POST'])
def api_generate_keys():
    value_int = int(request.json.get('num_keys', 0))
    gkeys.clear() 
    new_keys = []
    results = []
    for key_info in generate_keys(value_int, new_keys):
        results.append(key_info)
    save_keys(new_keys)  
    return jsonify(gkeys=results)

if __name__ == '__main__':
    app.run(debug=True)
