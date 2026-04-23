"""Run once: python -m src.tools.init_db [--admin-user admin --admin-pass changeme]"""
import argparse
import bcrypt
import yaml
from src.config import AUTH_YAML_PATH
from src.tools.job_store import init_schema, get_or_create_user


def run(admin_user: str = "admin", admin_pass: str = "changeme"):
    init_schema()

    hashed = bcrypt.hashpw(admin_pass.encode(), bcrypt.gensalt()).decode()
    auth_config = {
        "credentials": {
            "usernames": {
                admin_user: {
                    "email": f"{admin_user}@example.com",
                    "name": admin_user.title(),
                    "password": hashed,
                }
            }
        },
        "cookie": {
            "expiry_days": 30,
            "key": "p04_meeting_intelligence_secret_key",
            "name": "p04_auth_cookie",
        },
        "preauthorized": {"emails": []},
    }
    AUTH_YAML_PATH.write_text(yaml.dump(auth_config, default_flow_style=False))
    get_or_create_user(admin_user)

    print(f"DB initialised at {AUTH_YAML_PATH.parent / 'data' / 'jobs.db'}")
    print(f"auth.yaml written to {AUTH_YAML_PATH}")
    print("IMPORTANT: change the admin password before sharing this instance.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-pass", default="changeme")
    args = parser.parse_args()
    run(args.admin_user, args.admin_pass)
