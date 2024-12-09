from scrape_safexpress import scrape_tracking_info
import csv
import time
from datetime import datetime
import os

def load_awb_numbers(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def update_output_csv(tracking_data, output_file):
    fieldnames = [
        'waybill_number', 'origin', 'destination', 'shipping_date',
        'in_transit_date', 'arrival_date', 'out_for_delivery_date',
        'delivery_date', 'current_status', 'tracking_stages',
        'last_updated'
    ]
    
    # Read existing data
    existing_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            existing_data = {row['waybill_number']: row for row in reader}
    
    # Update with new data
    tracking_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    existing_data[tracking_data['waybill_number']] = tracking_data
    
    # Write back to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_data.values())

def main():
    # Test run with single AWB
    print("🧪 Running initial test...")
    test_result = scrape_tracking_info("600704867288")
    if not test_result:
        print("❌ Initial test failed. Exiting...")
        return
    
    print("✅ Initial test successful! Starting batch processing...")
    
    # Load AWB numbers
    awb_numbers = load_awb_numbers('awb_numbers.csv')
    output_file = 'tracking_results.csv'
    
    print(f"📋 Loaded {len(awb_numbers)} AWB numbers")
    
    while True:
        for awb in awb_numbers:
            try:
                print(f"\n🔄 Processing AWB: {awb}")
                result = scrape_tracking_info(awb)
                
                if result:
                    update_output_csv(result, output_file)
                    print(f"✅ Updated tracking data for {awb}")
                else:
                    print(f"⚠️ No data found for {awb}")
                
                # Wait between requests to avoid overwhelming the server
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error processing {awb}: {str(e)}")
                continue
        
        print("\n📊 Completed one cycle. Waiting before next cycle...")
        time.sleep(300)  # 5 minutes between cycles

if __name__ == "__main__":
    main() 