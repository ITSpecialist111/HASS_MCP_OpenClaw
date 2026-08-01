#!/usr/bin/env bash
# Test harness for deploy-voicebox-lxc.sh --check
# Mocks the Proxmox CLI so the RAM-budget logic can be exercised without a node.

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/deploy-voicebox-lxc.sh"
MOCK="$HERE/.mockbin"
PASS=0; FAIL=0

setup_mocks() {
    local total_mb="$1" used_mb="$2" vmspec="$3" ctspec="$4"
    rm -rf "$MOCK"; mkdir -p "$MOCK"

    cat > "$MOCK/free" <<EOF
#!/usr/bin/env bash
echo "              total        used        free      shared  buff/cache   available"
echo "Mem:          $total_mb        $used_mb         100           0        1000        1000"
EOF

    # vmspec / ctspec format: "id:state:mem,id:state:mem"
    cat > "$MOCK/qm" <<EOF
#!/usr/bin/env bash
spec="$vmspec"
if [ "\$1" = "list" ]; then
  echo "      VMID NAME                 STATUS     MEM(MB)    BOOTDISK(GB) PID"
  IFS=, read -ra items <<< "\$spec"
  for it in "\${items[@]}"; do
    [ -z "\$it" ] && continue
    IFS=: read -r id st mem <<< "\$it"
    printf '%10s %-20s %-10s %-10s %-12s %s\n' "\$id" "guest\$id" "\$st" "\$mem" "32" "1234"
  done
elif [ "\$1" = "config" ]; then
  IFS=, read -ra items <<< "\$spec"
  for it in "\${items[@]}"; do
    IFS=: read -r id st mem <<< "\$it"
    [ "\$id" = "\$2" ] && echo "memory: \$mem"
  done
fi
EOF

    cat > "$MOCK/pct" <<EOF
#!/usr/bin/env bash
spec="$ctspec"
if [ "\$1" = "list" ]; then
  echo "VMID       Status     Lock         Name"
  IFS=, read -ra items <<< "\$spec"
  for it in "\${items[@]}"; do
    [ -z "\$it" ] && continue
    IFS=: read -r id st mem <<< "\$it"
    printf '%-10s %-10s %-12s %s\n' "\$id" "\$st" "" "ct\$id"
  done
elif [ "\$1" = "config" ]; then
  IFS=, read -ra items <<< "\$spec"
  for it in "\${items[@]}"; do
    IFS=: read -r id st mem <<< "\$it"
    [ "\$id" = "\$2" ] && echo "memory: \$mem"
  done
fi
EOF

    printf '#!/usr/bin/env bash\necho 200\n'                        > "$MOCK/pvesh"
    printf '#!/usr/bin/env bash\necho "pve-manager/9.0.3/abc"\n'    > "$MOCK/pveversion"
    cat > "$MOCK/pvesm" <<'EOF'
#!/usr/bin/env bash
echo "Name             Type     Status           Total            Used       Available        %"
echo "local            dir      active       100000000        20000000        80000000    20.00%"
EOF
    chmod +x "$MOCK"/*
}

run_check() {
    PATH="$MOCK:$PATH" bash "$SCRIPT" --check 2>&1
}

assert() {
    local name="$1" expect="$2" out="$3"
    if grep -qi -- "$expect" <<< "$out"; then
        echo "  PASS  $name"; PASS=$((PASS+1))
    else
        echo "  FAIL  $name  (expected to find: '$expect')"
        echo "$out" | sed 's/^/        | /'
        FAIL=$((FAIL+1))
    fi
}

echo "================================================================"
echo " Scenario 1: 64 GB node, 20 GB committed -> should allocate 12 GB"
echo "================================================================"
setup_mocks 64000 30000 "100:running:8192,101:running:4096" "200:running:8192"
out=$(run_check)
echo "$out"
assert "budget computed"        "AVAILABLE FOR VOICEBOX"          "$out"
assert "allocates full 12288"   "LXC will get 12288 MB"           "$out"
assert "container capped 10240" "capped at 10240 MB"              "$out"
assert "no changes made"        "check mode: nothing was changed"  "$out"
echo

echo "================================================================"
echo " Scenario 2: 16 GB node, 12 GB committed -> MUST REFUSE"
echo "================================================================"
setup_mocks 16000 14000 "100:running:8192" "200:running:4096"
out=$(run_check); rc=$?
echo "$out"
assert "refuses to deploy"      "needs at least"                  "$out"
if [[ $rc -ne 0 ]]; then echo "  PASS  non-zero exit ($rc)"; PASS=$((PASS+1));
else echo "  FAIL  should have exited non-zero"; FAIL=$((FAIL+1)); fi
echo

echo "================================================================"
echo " Scenario 3: 32 GB node, 18 GB committed -> trims to fit budget"
echo "================================================================"
setup_mocks 32000 20000 "100:running:16384" "200:running:2048"
out=$(run_check)
echo "$out"
assert "trims allocation"       "trimming LXC RAM"                "$out"
echo

echo "================================================================"
echo " Scenario 4: empty node, no guests -> full allocation, no crash"
echo "================================================================"
setup_mocks 32000 2000 "" ""
out=$(run_check)
echo "$out"
assert "handles zero guests"    "(none)"                          "$out"
assert "allocates 12288"        "LXC will get 12288 MB"           "$out"
echo

echo "================================================================"
echo " Scenario 5 (regression): a guest whose config cannot be read"
echo "   Previously this aborted the whole script silently via set -e."
echo "   Expect: that guest counts as 0 and the run continues."
echo "================================================================"
setup_mocks 64000 30000 "100:running:8192,101:running:4096" "200:running:8192"
# make `qm config` always fail, as if the guest vanished mid-run
cat > "$MOCK/qm" <<'EOF'
#!/usr/bin/env bash
if [ "$1" = "list" ]; then
  echo "      VMID NAME                 STATUS     MEM(MB)    BOOTDISK(GB) PID"
  echo "       100 guest100             running    8192       32           1234"
  echo "       101 guest101             running    4096       32           1235"
elif [ "$1" = "config" ]; then
  exit 1
fi
EOF
chmod +x "$MOCK/qm"
out=$(run_check); rc=$?
echo "$out"
assert "survives unreadable config" "AVAILABLE FOR VOICEBOX"      "$out"
assert "still reaches check output" "check mode: nothing was changed" "$out"
if [[ $rc -eq 0 ]]; then echo "  PASS  exited cleanly"; PASS=$((PASS+1));
else echo "  FAIL  aborted (rc=$rc) - the set -e bug is back"; FAIL=$((FAIL+1)); fi
echo

rm -rf "$MOCK"
echo "================================================================"
echo " RESULT: $PASS passed, $FAIL failed"
echo "================================================================"
[[ $FAIL -eq 0 ]]
