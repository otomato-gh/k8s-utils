import logging
import boto3
import re, os, time
from botocore.exceptions import ClientError
import argparse

def msg(message):
    print ("\033[92m INFO [{}] ---> {}\033[0m".format(time.strftime("%H:%M:%S"), message))
def warn(message):
    print ("\033[93m WARN [{}] ---> {}\033[0m".format(time.strftime("%H:%M:%S"), message))
def err(message):
    print ("\033[91m ERR  [{}] ---> {}\033[0m".format(time.strftime("%H:%M:%S"), message))
    sys.exit(1)

parser = argparse.ArgumentParser(description='Create a viewer only user for a k8s cluster.')

parser.add_argument('bucket')
parser.add_argument('clustername')
args = parser.parse_args()
print(args.bucket)
client = boto3.client('s3')
#find the key file
objects = client.list_objects(Bucket=args.bucket, Delimiter="/", Prefix=args.clustername+"/pki/private/ca/")
for object in objects["Contents"]:
    if bool(re.search(".*\.key", object['Key']))==True:
        #this is the key
        with open('ca.key', 'wb') as f:
            client.download_fileobj(args.bucket, object['Key'], f)

objects = client.list_objects(Bucket=args.bucket, Delimiter="/", Prefix=args.clustername+"/pki/issued/ca/")
for object in objects["Contents"]:
    if bool(re.search(".*\.crt", object['Key']))==True:
        #this is the key
        with open('ca.crt', 'wb') as f:
            client.download_fileobj(args.bucket, object['Key'], f)


os.system("openssl genrsa -out user.key 4096")
os.system("openssl req -new -key user.key -out user.csr -subj '/CN=viewer/O=developer'")
os.system("openssl x509 -req -in user.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out user.crt -days 365")

os.environ["KUBECONFIG"] = "./kubeconfig"
os.system("kops export kubecfg --state=s3://"+args.bucket+" --name="+args.clustername)
os.system("kubectl create clusterrolebinding viewer-cluster-view-binding --clusterrole=view --user=viewer")
os.system("kubectl config unset users")
os.system("kubectl config set-credentials  viewer --client-key=user.key --client-certificate=user.crt --embed-certs=true")
os.system("kubectl config set-context "+args.clustername+" --user=viewer --cluster "+args.clustername)

#check
msg("Checking access - this should return the namespaces list:\n...")
if os.system("kubectl get ns"):
    error("Error accessing the server")
else:
    msg("Read access verified\n...")

msg("Checking access - this should be forbidden:\n...")
timestamp = str(int(time.time()))
if os.system("kubectl create ns "+timestamp):
    msg("Failed as expected\n...")
else:
    os.system("kubectl delete ns "+timestamp)
    error("Something is wrong - don't distribute resulting user credentials!")

for file in ["user.key", "user.crt", "user.csr","ca.key", "ca.crt", "ca.srl"]:
    os.remove(file)

msg("*** SUCCESS! The kubeconfig file in current directory can be distributed to users. ****")

