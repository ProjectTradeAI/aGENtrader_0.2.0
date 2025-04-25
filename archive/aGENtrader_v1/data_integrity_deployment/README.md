# Data Integrity Deployment for EC2

This package contains scripts and modules to implement data integrity measures in the trading system.
These measures ensure that analyst agents explicitly state when they don't have access to real data
rather than providing simulated responses.

## EC2 Deployment Instructions

1. Upload this package to your EC2 instance:
   ```
   scp -i your-ec2-key.pem data_integrity_deployment.tar.gz ec2-user@your-ec2-ip:~/
   ```

2. SSH into your EC2 instance:
   ```
   ssh -i your-ec2-key.pem ec2-user@your-ec2-ip
   ```

3. Extract the package in your project directory:
   ```
   cd ~/aGENtrader
   mkdir -p data_integrity
   tar -xzf ~/data_integrity_deployment.tar.gz -C data_integrity
   cd data_integrity
   ```

4. Apply the data integrity implementation:
   ```
   chmod +x apply-data-integrity.sh
   ./apply-data-integrity.sh
   ```

5. Restart your trading system to apply the changes.

## Verification

After installation, when analyst agents don't have access to real data, they will:

1. Clearly state they cannot provide analysis due to lack of data access
2. Explicitly recommend their input should NOT be counted in trading decisions
3. Never provide simulated data that could lead to poor trading decisions
