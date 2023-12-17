#!/bin/bash
if [ $# -eq  0 ]
   then
     pkexec ec4Linux.py
else
    pkexec ec4Linux.py $1
fi
