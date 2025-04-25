import os


def get_db_config():
    """Get database configuration based on environment"""
    # Check if running in Cloud Run
    in_cloud_run = os.environ.get('K_SERVICE', '') != ''

    if in_cloud_run:
        # Cloud SQL connection
        return {
            'database': os.getenv('DB_NAME', 'final'),
            'user': os.getenv('DB_USER', 'master'),
            'password': os.getenv('DB_PASS', 'master'),
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'port': 3306
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