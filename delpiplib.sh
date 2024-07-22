#!/bin/bash
while read p; do
    pip uninstall -y $p
done < <(pip freeze)
