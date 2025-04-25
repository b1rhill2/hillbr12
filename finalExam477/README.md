# Web Application Development: Final Exam - Group Scheduling Tool

## Overview

This web application is a group scheduling tool inspired by When2Meet. It allows users to create events, invite participants, and collaboratively indicate their availability using an interactive grid-based calendar interface. The application features real-time updates and a heatmap visualization to help identify the best meeting times for a group.

This project was developed as the final exam for a Web Application Development course, aiming to assess understanding of reactive front-end design, data-driven backend development, session management, and asynchronous communication.

## Key Features

* **Signup System:** Users can register, log in, and log out securely. Only logged-in users can access core application features. Passwords are encrypted for security.
* **Event Creation:** Logged-in users can create new events by providing an event name, start and end dates, a daily time range, and a list of invitee emails. The creator is automatically added as a participant.
* **Joining Existing Events:** Logged-in users who have been invited to events can see a list of their invitations and access the specific Event Page.
* **Interactive Availability Grid:** An interactive grid displays time slots in half-hour increments across the event's date range. Users can select their availability (Available, Maybe, Unavailable) by clicking or dragging on cells.
* **Availability Mode Selector:** A clear dropdown allows users to switch between the three availability states.
* **Persistence of Selections:** User availability selections are saved in the backend in real-time and are loaded when the user revisits the Event Page.
* **Heatmap Visualization:** A live heatmap overlay on the grid visually represents the collective availability of all participants, with color intensity increasing for time slots with more "Available" responses. "Maybe" and "Unavailable" statuses are also visually differentiated.
* **Best Time Calculation:** A dynamically updated "Best Time to Meet" section identifies and displays the single most optimal 30-minute time slot based on the highest number of "Available" responses, followed by the fewest "Unavailable" responses, and then the earliest time.
* **Live Synchronization:** Real-time updates of availability selections, the heatmap, and the best time calculation are synchronized across all clients viewing the same Event Page using WebSockets.

## Technologies Used

* **Backend:**
    * [Python](https://www.python.org/) (Version 3.8 or higher)
    * [Flask](https://flask.palletsprojects.com/)
    * [MySQL](https://www.mysql.com/)
* **Frontend:**
    * [HTML5](https://developer.mozilla.org/en-US/docs/Web/HTML)
    * [CSS3](https://developer.mozilla.org/en-US/docs/Web/CSS)
    * [JavaScript](https://www.javascript.com/)
    * [jQuery](https://jquery.com/)
* **Real-time Communication:**
    *  Flask-SocketIO 

## Installation

To run this application locally, please follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://gitlab.msu.edu/cse477-spring-2025/hillbr12.gite Repository URL
    cd finalExam477
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt  # You'll need to create this file listing your Python dependencies
    ```

4.  **Set up the MySQL database:**
    * Ensure you have MySQL installed and running.
    * Create a database for the application (e.g., `final_exam_db`).
    * Create a user with the necessary permissions to access this database.
    * Import the database schema from `schema.sql` (if you have a SQL file defining your tables).

5.  **Configure environment variables:**
    * Create a `.env` file in the project root directory and add your database credentials and a secret key for Flask:
        ```
        DATABASE_USER=your_db_user
        DATABASE_PASSWORD=your_db_password
        DATABASE_HOST=localhost
        DATABASE_NAME=final_exam_db
        SECRET_KEY=your_secret_key_here
        ```

6.  **Run the application:**
    ```bash
    flask run
    ```

7.  **Open your web browser** and navigate to `http://127.0.0.1:5000` (or the address your Flask app runs on).

## Usage

1.  **Signup:** New users can register an account using their email and password on the signup page.
2.  **Login:** Registered users can log in with their email and password on the login page.
3.  **Event Creation:** After logging in, users can click "Create a New Event" and fill out the form with the event name, start and end dates, daily time range, and a comma-separated list of invitee emails.
4.  **Joining Events:** Users who have been invited to events can click "Join an Existing Event" to see a list of their invitations and click on an event to access its Event Page.
5.  **Availability Selection:** On the Event Page, users can select their availability for each 30-minute time slot within the event's date and time range using the dropdown selector and by clicking or dragging on the grid cells.
6.  **Viewing Others' Availability:** The availability grid dynamically updates with a heatmap overlay showing the collective availability of all participants.
7.  **Best Time to Meet:** The "Best Time to Meet" section displays the calculated optimal 30-minute time slot based on the availability data.

## Deployment to Google Cloud

This application is Dockerized for deployment to Google Cloud. The necessary `Dockerfile` and `cloudbuild.yaml` (or similar configuration) are included in the repository.

To deploy:

1.  Ensure you have a Google Cloud Project set up and the Google Cloud CLI installed and configured.
2.  Build and push the Docker image to Google Container Registry (GCR).
3.  Deploy the application to Google Cloud Run or Google Kubernetes Engine (GKE) using the appropriate Google Cloud services.

**Service URL:** [Your Deployed Application URL on Google Cloud]

## Contributing

This project was developed as part of a final exam and is not intended for external contributions at this time.

## License

This project is for academic purposes as part of the Web Application Development final exam. No specific license is applied.

## Acknowledgments

This project draws inspiration from the functionality of [When2Meet](https://www.when2meet.com/).

