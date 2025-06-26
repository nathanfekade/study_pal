# Study Pal

-----

Study Pal is a web application built with **Django Rest Framework**, designed to help students manage their study materials, track their progress, and organize their notes efficiently. This project provides a robust backend API.
## Prerequisites

-----

Before setting up the project, ensure you have the following installed on your system:

  * **Python 3.10** or higher

## Setup

-----

### Backend

-----

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/nathanfekade/study_pal.git
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd study_pal
    ```

3.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

4.  **Activate the virtual environment:**

      * On Unix-based systems:
        ```bash
        source venv/bin/activate
        ```
      * On Windows:
        ```bash
        venv\Scripts\activate
        ```

5.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

6.  **Run database migrations:**

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

7.  **Start the development server:**

    ```bash
    python manage.py runserver
    ```
