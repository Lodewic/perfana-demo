import httpx


def get_grafana_api_token(username, password, key_name: str = "kedro-grafana-token") -> str:
    """Create and replace the Grafana HTTP API token by name."""
    password = password.replace("@", "%40")
    username = username.replace("@", "%40")

    url = f"http://{username}:{password}@grafana:3000/api/auth/keys"
    with httpx.Client(headers={"Content-Type": "application/json"}) as client:
        response_existing_keys = client.get(url)
        if response_existing_keys.status_code != 200:
            raise ValueError(
                f"Existing keys response status was {response_existing_keys.status_code}: {response_existing_keys.text}"
            )

        existing_tokens = [x for x in response_existing_keys.json() if x["name"] == key_name]
        if len(existing_tokens) > 0:
            for existing_token in existing_tokens:
                response_delete_key = client.delete(f"{url}/{existing_token['id']}")
                if response_delete_key.status_code != 200:
                    raise ValueError(
                        f"Deleting key (id={existing_token['id']}), response status was {response_delete_key.status_code}: {response_delete_key.text}"
                    )

        response = client.post(url=url, json={"name": "kedro-grafana-token", "role": "Viewer"})

        if response.status_code != 200:
            raise ValueError(f"Response status was {response.status_code}: {response.text}")
        key = response.json()["key"]

        return key
