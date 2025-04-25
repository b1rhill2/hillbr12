import os


def get_db_config():
    """Get database configuration based on environment"""
    # Check if running in Cloud Run
    in_cloud_run = os.environ.get('K_SERVICE', '') != ''

    if in_cloud_run:
        # Cloud SQL connection
        db_socket_dir = os.environ.get("DB_SOCKET_DIR", "/cloudsql")
        instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME",
                                                  "pure-league-447922-q4:us-central1:cse477-spring-2025")

        return {
            'database': os.getenv('DB_NAME', 'final'),
            'user': os.getenv('DB_USER', 'master'),
            'password': os.getenv('DB_PASS', 'master'),
            'unix_socket': f'{db_socket_dir}/{instance_connection_name}'
        }
    else:
        # Local development
        return {
            'database': 'final',
            'user': 'master',
            'password': 'master',
            'host': 'host.docker.internal',  # or localhost/127.0.0.1 if not using Docker
            'port': 3306
        }