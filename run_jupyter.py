import subprocess
import time
import argparse
# debug = 'any value'


params_vect = []
params_vect.append({'server':'comp',         'port':1445, 'user':'nir',     'image': 'image_comp', 'mount': '/home/nir/share'})


parser = argparse.ArgumentParser()
help_str = f'Please choose from:{", ".join([p["server"] for p in params_vect])}'
parser.add_argument('server', help=help_str)
args = parser.parse_args(['comp'] if 'debug' in locals() else None)


params_filt_vect = [p for p in params_vect if p['server'].startswith(args.server)]
assert len(params_filt_vect)>0, f'Server {args.server} not found. {help_str}'
assert len(params_filt_vect)<2, f'More than one option: {params_filt_vect}'
params = params_filt_vect[0]
print(f'{params["server"]}')
print('-'*50)
_=[print (f'{str(p)+" -":10}{params[p]}') for p in params]
print('-'*50)


def run_ssh(command, ssh_header=f'ssh {params["user"]}@{params["server"]}', wait=True, verbose=True):
    full_command = command
    if ssh_header:
        full_command = f'{ssh_header} "{command}"'
    if verbose:
        print(f'run_ssh: {full_command}')
        print('-' * 50)

    p = subprocess.Popen(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if not wait:
        # print ('No wait')
        return None

    retval = p.wait()
    output = [l.decode("utf-8").strip() for l in p.stdout.readlines()]
    if verbose:
        print(output)
        print('-' * 50)
    return output


def run_local(command, wait=True, verbose=False):
    return run_ssh(command, ssh_header=None, wait=wait, verbose=verbose)


def find_running_jupyters():
    try:
        out_list = run_ssh('docker ps')
        assert out_list, "Error: docker ps retuned None"
        line_list = [o for o in out_list if params["image"] in o]
        process_id_list = [o.split()[0] for o in line_list]
        assert len(process_id_list) > 0, f'Image "{params["image"]}" not found'
        assert len(process_id_list) == 1, f'More than one image "{params["image"]}" option {line_list}'
        process_id = process_id_list[0]
        return process_id, line_list[0]
    except Exception as e:
        print(f'=== Failure: {e}')
        return None, None


def verbose_sleep(secs):
    for i in range(secs, 0, -1):
        print(f'{i}     \r', end='')
        time.sleep(1)


print('Looking for running notebooks...')
process_id, line = find_running_jupyters()
if process_id:
    assert line.split(':::')[1].startswith(f'{params["port"]}->{params["port"]}'), 'Wrong port: {line}, expected port {port}'
    # print(f'Found: {line}')
else:
    stat_jupyter_command = f'docker run -p {params["port"]}:{params["port"]} --gpus all -v /home/{params["user"]}/jupyters:/home/{params["user"]}/jupyters -v {params["mount"]}:{params["mount"]} -t {params["image"]} /home/{params["user"]}/.local/bin/jupyter notebook --port {params["port"]} --notebook-dir=/home/{params["user"]} --ip 0.0.0.0 --no-browser --allow-root'
    print('Starting jupyter')
    out_list = run_ssh(stat_jupyter_command, wait=False)
    print('------- waiting...')
    verbose_sleep(5)
    print('Verifing running notebooks...')
    process_id, line = find_running_jupyters()
    assert process_id
    # print(f'Found: {line}')
print()
print('====> Jupyter Running, OK')
print()



command = f'docker exec -t  {process_id} /home/{params["user"]}/.local/bin/jupyter server list'
# print(command)
out = run_ssh(command)
#print (out)
assert out[0] == 'Currently running servers:'
token = out[1].split(f'?token=')[1].split(' :: ')[0]
jupyter_cmd = f'http://localhost:{params["port"]}/?token={token}'
tunnel_cmd = f'ssh -NfL localhost:{params["port"]}:localhost:{params["port"]} {params["user"]}@{params["server"]}'
# print(tunnel_cmd)
run_local(tunnel_cmd, wait = False, verbose = True)

print()
print(jupyter_cmd)
print()

explorer_path = '"/mnt/c/Program Files/Mozilla Firefox/firefox.exe"'
run_local(f'{explorer_path} {jupyter_cmd}')

print ('====> Done')

# _=run_ssh(f'docker stop {process_id}')
# _=run_ssh('docker ps')


