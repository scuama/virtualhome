#!/bin/bash
killall -9 xvfb-run || true
killall -9 linux_exec.v2.3.0.x86_64 || true
sleep 3
nohup /bin/sh /usr/bin/xvfb-run -a /mnt/disk1/decom/virtualhome/virtualhome/simulation/unity_simulator/linux_exec.v2.3.0.x86_64 -batchmode -http-port=8080 > /tmp/unity.log 2>&1 &
echo "Waiting for Unity server to initialize (15s)..."
sleep 15
echo "Running E2E tests..."
for f in G3 M1 M2 M3; do
    echo "Starting test_$f..."
    python3 run_main.py agent/configs/test_$f.json > /tmp/final_test_$f.log 2>&1
    cat /tmp/final_test_$f.log | grep -E "(SUCCESS|FAILED|Error|Starting)"
done
echo "All done."
