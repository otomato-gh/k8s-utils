# viewerconfig.py : create read-only user configuration for a Kops-managed cluster

usage: viewerconfig.py [-h] bucket clustername

positional arguments:
  
    bucket - s3 bucket name of the Kops state store (without the s3:// prefix)
  
    clustername - name of the cluster defined in the bucket

**Note**: this uses the current shell AWS access keys

output: 

    the `kubeconfig` file in script execution directory

What the script does:

- Pulls the following files from the s3 bucket:
  - s3://$BUCKET/$CLUSTER/pki/private/ca/$KEY
  - s3://$BUCKET/$CLUSTER/pki/issued/ca/$CERT

- Generates certificate and key for a user named 'viewer'

- Creates a ClusterRoleBinding between user 'viewer' and ClusterRole 'view'

- Generates a kubeconfig file for sending to the users.