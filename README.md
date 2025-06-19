Read me first – instructions on how to run the Wiki Search app
1. Use Linux VM to run Flask app
 Configure network settings. Use a NAT (or Bridged) adapter to ensure internet
access and a host-only adapter to connect with other VMs.
 Install necessary updates and Python.
 Create a directory for the project and make sure to create and activate a virtual
environment.
2. Use EC2 to search Wikipedia
 Connect with your instance from the host terminal using SSH.
 Install available updates and Python.
 Create and activate a virtual environment.
 Install the Wikipedia package
 Transfer a copy of the wiki.py file to your EC2 instance
3. Use another Linux VM to set up a database
 Make sure the host-only adapter is enabled in the VM’s network settings.
 Set static IP 192.168.56.101.
 Ensure Docker is installed.
4. Update the code with your parameters
 Go to EC2 connection settings (EC2_CONFIG) in main.py and update them with
details of your EC2 instance.
 Find Database connection settings in my.py and add details of your MySQL
connection.
 Update the secret key in main.py
 Add the IP of your EC2 instance and the path of your key file.
5. Run main.py in VM. Navigate to http://IP_of_your_Linux_VM:5000 in your browser
