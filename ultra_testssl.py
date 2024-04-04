import subprocess

# Function to run the testssl.sh command on a target
def run_testssl(target):
    # Customize the testssl command based on your requirements
    command = f"./testssl.sh --sneaky --openssl-timeout 15 --phone-out --mapping rfc --color 3 -U --vulnerable --headers -p -S -P -c -h -H -I -T --BB --SI -R -C -B -O -Z -W -A -L -WS -F -J -D -4 https://{target}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode('utf-8')

# Function to iterate over domains in the targets file and run scans
def run_scan_on_targets(file_path):
    with open(file_path, 'r') as file:
        targets = [line.strip() for line in file.readlines()]

    for target in targets:
        print(f"Running testssl on {target}")
        results = run_testssl(target)
        print(results)

if __name__ == "__main__":
    targets_file = "targets.txt"
    run_scan_on_targets(targets_file)
