# EagleNotes
Repository for web-based note-taking app developed for school project
Local Setup Walkthrough (for a personal machine)

# all code blocks below in bash

1. Clone the repository
git clone https://github.com/lieu-EtOH/EagleNotes.git
cd EagleNotes

2. Create a virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# or
source venv/bin/activate   # macOS/Linux

3. Install dependencies
pip install -r requirements.txt

4. Set up environment variables
# Create a .env file in the project root. Example:
DB_HOST=localhost
DB_NAME=eaglenotes
DB_USER=postgres
DB_PASSWORD=yourpassword
SECRET_KEY=your-secret-key

5. Initialize the database
# Open PostgreSQL and run:
CREATE DATABASE eaglenotes;
# Then execute your schema SQL (the User table and others).

6. Run the Flask app
python app.py
# Visit:
http://127.0.0.1:5000/

7. Verify functionality
# Register → confirm hashed password in DB

# Login → confirm session works

# Access protected pages → confirm redirect if unauthenticated

# Logout → confirm session clears 