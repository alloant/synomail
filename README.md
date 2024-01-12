# Synology Document Database Management with User-Specific Access Control

This Flask project integrates Synology Drive, SQLAlchemy, and user authentication to create a robust and secure document management system.

## Key Features:

* Synology Drive Integration: Leverages the synology-drive-api library to interact with your Synology Drive.
* SQLAlchemy ORM: Streamlines database interactions for a smooth development experience:
    * Handles database operations effortlessly
    * Ensures data consistency and integrity
* User Authentication and Access Control: Enforces granular control over user access to documents, ensuring:
    * Secure document management
    * Restriction of sensitive information to authorized users
    * Workflow Support.

## Getting Started:


. Clone the repository: `git clone https://github.com/alloant/synomail`

. Install dependencies: `pip install -r requirements.txt` or `poetry install`

. Configure credentials SECRET_KEY (to encrypt the user passwords) and DATABASE_URI (to connect to the databse, otherwise it will default to SQlite)

. Run the application: `python flask_app/app.py` or `waitress-serve -call 'app:create_app'`

### With docker

. Clone the repository: `git clone https://github.com/alloant/synomail`

. Build image: `docker build -t synomail .`

. Run docker: `docker run --env SECRET_KEY="secret" DATABASE_URI="mariadb+pymysql://user:password@host/database?charset=utf8mb4"`

