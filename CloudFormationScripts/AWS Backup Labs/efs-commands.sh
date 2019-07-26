#!/bin/bash

sudo yum install -y amazon-efs-utils

sudo mount -t efs fs-1516f7f7:/ /mnt/efs
sudo chmod 777 /mnt/efs
touch file1.txt
touch file2.txt
touch file3.txt