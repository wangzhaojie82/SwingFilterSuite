#!/bin/bash

echo "ColdFilter is running..."

./CF.sh $1 $2

echo "Loglog filter is running..."

./log.sh $1 $2

echo "SwingFilter is running..."

./BF.sh $1 $2