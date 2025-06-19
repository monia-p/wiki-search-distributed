import wikipedia
import paramiko
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
import time
import hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key"

# EC2 connection settings
EC2_CONFIG = {
    "hostname": "XXXXXXX",
    "username": "ubuntu",
    "key_file": "CT5050.pem"
}

# Database connection settings for caching
DB_CONFIG = {
    "host": "192.168.56.101",
    "port": 7888,
    "user": "root",
    "password": "password",
    "database": "cache_db"
}

def searchWikipedia(term):
    # Checking cache
    cached_result = check_cache(term)
    if cached_result:
        print(f"Returning cached result for '{term}'")
        return f"<div class='cached-result'><p><strong>⚡ Cached Result:</strong></p>{cached_result}</div>"

    # If not in cache, search via EC2
    try:
        print(f"Performing new search for '{term}'")
        content = search_wikipedia_via_ec2(term)

        # Save result to cache
        if "Error" not in content and "No results found" not in content:
            save_to_cache(term, content)

        return f"<div class='fresh-result'>{content}</div>"
    except Exception as e:
        print(f"EC2 search failed: {e}")
        error_message = f"Error connecting to EC2 search service: {str(e)}"
        return f"<div class='error'>{error_message}</div>"


#connecting with database
def get_db_connection():
    try:
        print("Attempting database connection...")
        connection = mysql.connector.connect(**DB_CONFIG)
        print("Database connection successful")
        return connection
    except mysql.connector.Error as e:
        if e.errno == mysql.connector.errorcode.CR_CONN_HOST_ERROR:
            print(f"Database connection error: Cannot connect to host {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        elif e.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print(f"Database connection error: Access denied for user {DB_CONFIG['user']}")
        elif e.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print(f"Database connection error: Database '{DB_CONFIG['database']}' does not exist")
        else:
            print(f"Database connection error: {e}")
        return None
# Searching via EC2 with SSH connection
def search_wikipedia_via_ec2(term):
    try:


        # SSH connection
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Loading the key file
            key = paramiko.RSAKey.from_private_key_file(EC2_CONFIG["key_file"])
        except FileNotFoundError:
            print(f"Key file not found: {EC2_CONFIG['key_file']}")
            return f"Error: SSH key file not found. Please check that {EC2_CONFIG['key_file']} exists."
        except Exception as key_error:
            print(f"Key file error: {key_error}")
            return f"Error: Problem with SSH key file: {str(key_error)}"
        try:
            # Connecting to EC2

            client.connect(
                hostname=EC2_CONFIG["hostname"],
                username=EC2_CONFIG["username"],
                pkey=key,
                timeout=10  # Set a timeout
            )
        except paramiko.SSHException as ssh_error:
            print(f"SSH connection error: {ssh_error}")
            return f"Error connecting to search server: {str(ssh_error)}"
        except Exception as conn_error:
            print(f"Connection error: {conn_error}")
            return f"Error connecting to search server: {str(conn_error)}"

        # Activate virtual environment and execute the wiki.py on EC2
        cmd = f"source myenv/bin/activate && python3 /home/ubuntu/wiki.py \"{term}\""
        stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
        stdin.close()

        # Check for errors
        error_output = stderr.read().decode('utf-8')
        if error_output:
            print(f"EC2 search error: {error_output}")
            if "No such file or directory" in error_output:
                return "Error: Required files not found on EC2 server. Check that wiki.py exists and virtual environment is set up."

        # Get the output
        output = stdout.read().decode('utf-8')

        # Close the connection
        client.close()

        # Process the output
        if output:
            formatted_output = output.replace("\n", "<br>")
            return formatted_output
        else:
            return "No results found for this search term."

    except Exception as e:
        print(f"EC2 connection error: {e}")
        return f"Error connecting to search service: {str(e)}"


#Checking if term is present in cache
def check_cache(term):

    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor()

        # Check cache
        cursor.execute("SELECT content FROM wiki_cache WHERE term = %s", (term,))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if result:
            content = result[0]
            print(f"Cache hit! Found '{term}' in database cache")
            return content
        else:
            print(f"Cache miss! '{term}' not found in database")
            return None

    except mysql.connector.Error as e:
        print(f"Cache check error: {e}")
        connection.close()
        return None

#Saving new search result to cache
def save_to_cache(term, content):
    if not content or "Error" in content or "No results found" in content:
        print("Not caching error results or empty content")
        return False

    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()

        # Insert or update cache entry
        cursor.execute(
            "INSERT INTO wiki_cache (term, content) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE content = VALUES(content)",
            (term, content)
        )

        connection.commit()
        cursor.close()
        connection.close()

        print(f"Successfully cached results for '{term}'")
        return True

    except mysql.connector.Error as e:
        print(f"Cache storage error: {e}")
        connection.close()
        return False

#route for the home page
@app.route("/", methods=["GET", "POST"])
def home_page():
    if request.method == "POST":
        search_term = request.form.get("search_term")
        if not search_term:
            flash("Please enter a search term.")
            return redirect(url_for("home_page"))

        result = searchWikipedia(search_term)
        return render_template("index.html", result=result)

    return render_template("index.html", result=None)

#Initializing database
def init_db():
    #Connecting to database
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()

        # Create the wiki_cache table
        cursor.execute('''
               CREATE TABLE IF NOT EXISTS wiki_cache (
                   id INT AUTO_INCREMENT PRIMARY KEY,
                   term VARCHAR(255) NOT NULL UNIQUE,
                   content LONGTEXT NOT NULL
               )
               ''')

        connection.commit()
        cursor.close()
        connection.close()
        print("Database initialized successfully")
        return True
    else:
        print("Warning: Could not initialize database. Caching will be disabled.")
        return False

#Entry point
if __name__ == "__main__":
    # Initialize database at the start
    db_initialized = init_db()
    if not db_initialized:
        print("Warning: Running without caching capability!")

    # Make the app accessible from all IPs
    app.run(debug=True, host='0.0.0.0', port=5000)