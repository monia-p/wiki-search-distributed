import paramiko
import sys

# Assuming the search term is passed as a command line argument
if len(sys.argv) < 2:
    print("Please provide a search term")
    sys.exit(1)

searchTerm = sys.argv[1]  # Retrieve the search term passed from the Flask app

instance_ip = "XXXXXXX"
securityKeyFile = "XXXXX.pem"

cmd = f"python3 /home/ubuntu/wiki.py {searchTerm}"

try:
    # Connect to the instance using SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(securityKeyFile)
    client.connect(hostname=instance_ip, username="ubuntu", pkey=key)

    # Execute the command after SSH connection
    stdin, stdout, stderr = client.exec_command(cmd)
    stdin.close()

    # Capture and print errors
    outerr = stderr.readlines()
    if outerr:
        print("ERRORS: ", outerr)

    # Capture and print output
    output = stdout.readlines()
    print("output:", output)
    for items in output:
        print(items, end="")

    # Close the client connection
    client.close()
except Exception as e:
    print(e)
