# Enterprise Verification System Guide

The Verification System (Module 7) is an advanced suite designed to protect your Discord server from raids, alt-accounts, and automated spam. It dynamically routes users through various verification layers depending on their "Risk Score."

## Overview

The system includes:
- **Button Verification**: Simple one-click access for low-risk users.
- **Math & Word Captcha**: Adaptive challenge for medium-risk users.
- **Image Captcha**: High-security alphanumeric image challenges for high-risk users.
- **Manual Review**: Push the highest risk users (or specific thresholds) into a manual approval queue.

## Setting Up

1. **Enable the Module**: Navigate to the Dashboard, select your server, and toggle Verification `ON`.
2. **Assign Roles**:
   - **Quarantine Role**: Assigned instantly upon joining. Prevents the user from seeing any channels except the verification channel.
   - **Verified Role**: The role granted after successfully solving the Captcha.
3. **Configure the Channel**: Set the Verification Channel ID where the bot will post the verification prompt.
4. **Deploy the Panel**: Run the `/verify_setup` slash command in your verification channel. The bot will deploy a localized embed with a "Verify" button.

## Risk Engine

The Risk Engine calculates a dynamic score based on:
- **Account Age**: Accounts under 24 hours receive maximum penalty. Accounts under 7 days receive a moderate penalty.
- **Avatar**: Missing avatars increase the risk score.
- **Username Pattern**: Automated bot names (e.g., `User12345`) are flagged.

If the score exceeds your configured `Risk Threshold` (default: 70), the user is escalated to an Image Captcha or Manual Review automatically.

## Web Dashboard Real-Time Logging

The system emits WebSocket events directly to the Dashboard. You can monitor Verification Success, Failures, and Pending Manual Reviews in real-time.

## Architecture

Developers can easily add new Captcha providers by extending `CaptchaProvider` in `bot/services/verification/providers/base.py` and registering it in `VerificationService`.
