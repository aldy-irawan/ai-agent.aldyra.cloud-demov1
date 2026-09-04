#!/bin/bash

# ============================================================
# AI Infrastructure Assistant - EC2 Action Script
# ============================================================

ACTION="$1"
INSTANCE_NAME="$2"

REGION="ap-southeast-1"
ACTION_ROLE="arn:aws:iam::YOUR_ACCOUNT_ID:role/AI-Infrastructure-Action-Role"
SESSION_NAME="ai-assistant-action"

# ------------------------------------------------------------
# Validasi parameter
# ------------------------------------------------------------

if [[ -z "$ACTION" || -z "$INSTANCE_NAME" ]]; then
    echo "Usage:"
    echo "  $0 check <instance-name>"
    echo "  $0 stop  <instance-name>"
    exit 1
fi

# ------------------------------------------------------------
# Hanya izinkan action yang kita definisikan
# ------------------------------------------------------------

case "$ACTION" in
    check|stop)
        ;;
    *)
        echo "ERROR: Unsupported action: $ACTION"
        exit 1
        ;;
esac

# ------------------------------------------------------------
# Cari Instance ID berdasarkan Name tag
# ------------------------------------------------------------

INSTANCE_ID=$(aws ec2 describe-instances \
    --region "$REGION" \
    --filters \
        "Name=tag:Name,Values=$INSTANCE_NAME" \
        "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text)

if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
    echo "ERROR: EC2 instance '$INSTANCE_NAME' tidak ditemukan di $REGION."
    exit 1
fi

# ------------------------------------------------------------
# Pastikan hanya satu instance yang ditemukan
# ------------------------------------------------------------

INSTANCE_COUNT=$(echo "$INSTANCE_ID" | wc -w)

if [[ "$INSTANCE_COUNT" -ne 1 ]]; then
    echo "ERROR: Ditemukan $INSTANCE_COUNT instance dengan Name '$INSTANCE_NAME'."
    echo "Action dibatalkan untuk mencegah salah server."
    exit 1
fi

# ------------------------------------------------------------
# Ambil informasi instance
# ------------------------------------------------------------

INSTANCE_INFO=$(aws ec2 describe-instances \
    --region "$REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,InstanceType,PrivateIpAddress,Tags[?Key==`Name`].Value|[0]]' \
    --output text)

read -r ID STATE TYPE PRIVATE_IP NAME <<< "$INSTANCE_INFO"

echo "=========================================="
echo "AI Infrastructure Assistant"
echo "=========================================="
echo "Instance Name : $NAME"
echo "Instance ID   : $ID"
echo "Region        : $REGION"
echo "State         : $STATE"
echo "Instance Type : $TYPE"
echo "Private IP    : $PRIVATE_IP"
echo "=========================================="

# ------------------------------------------------------------
# CHECK MODE
# ------------------------------------------------------------

if [[ "$ACTION" == "check" ]]; then

    echo "ACTION        : CHECK"
    echo "STATUS        : OK"

    exit 0
fi

# ------------------------------------------------------------
# STOP MODE
# ------------------------------------------------------------

if [[ "$ACTION" == "stop" ]]; then

    if [[ "$STATE" != "running" ]]; then
        echo "ERROR: Instance '$NAME' tidak dalam status RUNNING."
        echo "Current state: $STATE"
        echo "STOP dibatalkan."
        exit 1
    fi

    echo ""
    echo "WARNING: Instance akan dihentikan."
    echo "Target: $NAME ($ID)"
    echo ""

    # --------------------------------------------------------
    # Assume Action Role
    # --------------------------------------------------------

    CREDS=$(aws sts assume-role \
        --role-arn "$ACTION_ROLE" \
        --role-session-name "$SESSION_NAME")

    if [[ $? -ne 0 ]]; then
        echo "ERROR: Gagal melakukan AssumeRole."
        exit 1
    fi

    export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r '.Credentials.AccessKeyId')
    export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r '.Credentials.SecretAccessKey')
    export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r '.Credentials.SessionToken')

    # --------------------------------------------------------
    # Verify assumed role
    # --------------------------------------------------------

    CURRENT_ROLE=$(aws sts get-caller-identity \
        --query 'Arn' \
        --output text)

    echo "Action Role   : $CURRENT_ROLE"

    if [[ "$CURRENT_ROLE" != *"assumed-role/AI-Infrastructure-Action-Role"* ]]; then
        echo "ERROR: Active AWS identity bukan Action Role."
        echo "STOP dibatalkan."
        exit 1
    fi

    # --------------------------------------------------------
    # Execute StopInstances
    # --------------------------------------------------------

    echo "Executing STOP..."

    RESULT=$(aws ec2 stop-instances \
        --region "$REGION" \
        --instance-ids "$INSTANCE_ID" \
        --output json)

    if [[ $? -ne 0 ]]; then
        echo "ERROR: Gagal melakukan STOP."
        echo "$RESULT"
        exit 1
    fi

    echo ""
    echo "=========================================="
    echo "SUCCESS"
    echo "=========================================="
    echo "Instance : $NAME"
    echo "ID       : $INSTANCE_ID"
    echo "Action   : STOP"
    echo "Region   : $REGION"
    echo "=========================================="

    exit 0
fi
