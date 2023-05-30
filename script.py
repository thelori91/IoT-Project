import paramiko
import subprocess
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

    # Run the SSH command
    run_ssh_command(hostname, username, password, ssh_command)

    # Run the local Python command
    run_local_python_command(local_python_command)
finally:
        print("** ENDING **")
