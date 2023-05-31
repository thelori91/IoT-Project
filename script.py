import paramiko
import subprocess
import time
import sys

try:
    def run_ssh_command(hostname, username, password, command):
        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Connect to the remote host
            ssh.connect(hostname, username=username, password=password)

            # Execute the command
            stdin, stdout, stderr = ssh.exec_command(command)
        finally:
            # Close the SSH connection
            ssh.close()

    def run_local_python_command(command):
        # Run the Python command locally
        output = subprocess.check_output(command, shell=True).decode('utf-8')

        # Print the output
        print("Local Python command output:")
        print(output)

    # SSH connection details
    hostname = 'raspberrypi.local'
    username = 'lorenzocassinelli'
    password = 'E'
    ssh_command = 'python3 server.py'  
    local_python_command = 'python3 client.py' 

    print("** STARTING **")

    print("** RUNNING SSH - SERVER **")
    run_ssh_command(hostname, username, password, ssh_command)

    print("** WAITING **")
    time.sleep(2)

    print("** RUNNING LOCAL - CLIENT **")
    # Run the local Python command
    run_local_python_command(local_python_command)
finally:
        sys.tracebacklimit=0
        print("** ENDING **")
