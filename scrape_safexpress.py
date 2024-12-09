from playwright.sync_api import sync_playwright, TimeoutError
import csv
from datetime import datetime
import sys

def scrape_tracking_info(waybill_number: str):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            print(f"\n🌐 Navigating to Safexpress website...")
            page.goto('https://www.safexpress.com/', wait_until='networkidle')
            
            # Handle cookie popup - using the correct class from the landing page
            print("🍪 Handling cookie popup...")
            try:
                deny_button = page.locator('.cc-btn.cc-deny').first
                if deny_button:
                    deny_button.click()
                    page.wait_for_timeout(1000)  # Wait for popup to disappear
            except Exception:
                print("ℹ️ No cookie popup detected")
            
            # Handle notification popup
            print("🔄 Handling notification popup...")
            try:
                close_button = page.wait_for_selector('.btn-close', timeout=5000)
                if close_button:
                    close_button.click()
                    page.wait_for_timeout(1000)
            except TimeoutError:
                print("ℹ️ No notification popup detected")
            
            print(f"📦 Processing waybill number: {waybill_number}")
            input_selector = 'input[placeholder="Enter Waybill Number 8/9/12 digits"]'
            page.wait_for_selector(input_selector)
            page.fill(input_selector, waybill_number)
            
            # Click the track button - with retry mechanism
            print("🔘 Attempting to click track button...")
            max_attempts = 3
            attempt = 0
            tracking_found = False

            while attempt < max_attempts and not tracking_found:
                attempt += 1
                print(f"Attempt {attempt}/{max_attempts}...")
                
                try:
                    # Try different button selectors
                    selectors = [
                        'button[type="submit"].btn.track-button',
                        'button.btn.col-md-2.track-button',
                        'button[type="submit"]:has-text("Track")'
                    ]
                    
                    for selector in selectors:
                        track_button = page.locator(selector).first
                        if track_button and track_button.is_visible():
                            track_button.click(timeout=5000)
                            page.wait_for_timeout(2000)  # Wait after clicking
                            
                            # Check if tracking info appeared
                            try:
                                tracking_info = page.wait_for_selector('.container.trackResult.for-desktop.ng-star-inserted', timeout=5000)
                                if tracking_info:
                                    tracking_found = True
                                    print("✅ Tracking information found!")
                                    break
                            except TimeoutError:
                                print(f"⏳ Waiting for tracking info after click {attempt}...")
                                continue
                    
                    if not tracking_found:
                        page.wait_for_timeout(3000)  # Wait longer between attempts
                        
                except Exception as e:
                    print(f"⚠️ Attempt {attempt} failed: {str(e)}")
                    page.wait_for_timeout(2000)

            if not tracking_found:
                raise Exception("Failed to get tracking information after multiple attempts")
            
            print("🔍 Fetching tracking details...")
            
            # Basic shipment details
            tracking_data = {
                'waybill_number': page.locator('.col-4.text-start span[style*="font-weight: 550"]').first.inner_text().strip(),
                'origin': page.locator('.col-4.text-center span[style*="font-weight: 550"]').first.inner_text().strip(),
                'destination': page.locator('.col-4.text-end span[style*="font-weight: 550"]').first.inner_text().strip()
            }
            
            # Get all tracking stages from the flex container
            stages_container = page.locator('div[style*="display: flex"][style*="align-items: center"]')
            stages = stages_container.locator('div[style*="border: 1px solid #006431"]').all()
            tracking_stages = []
            
            for stage in stages:
                try:
                    status = stage.locator('span[style*="color: #006431"]').inner_text().strip()
                    date = stage.locator('span[style*="font-weight: 550"]:not([style*="color"])').inner_text().strip()
                    tracking_stages.append({'status': status, 'date': date})
                    
                    # Map to specific fields
                    if "SHIPPING DATE" in status:
                        tracking_data['shipping_date'] = date
                    elif "IN TRANSIT" in status:
                        tracking_data['in_transit_date'] = date
                    elif "ARRIVED AT DESTINATION" in status:
                        tracking_data['arrival_date'] = date
                    elif "OUT FOR DELIVERY" in status:
                        tracking_data['out_for_delivery_date'] = date
                    elif "DELIVERED" in status:
                        tracking_data['delivery_date'] = date
                        tracking_data['current_status'] = status.strip()
                except Exception as e:
                    print(f"⚠️ Error processing stage: {str(e)}")
                    continue
            
            # Add stages to tracking data
            tracking_data['tracking_stages'] = tracking_stages
            
            print("\n📊 Tracking Information:")
            for key, value in tracking_data.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
            
            filename = f"tracking_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=tracking_data.keys())
                writer.writeheader()
                writer.writerow(tracking_data)
            
            print(f"\n💾 Data saved to {filename}")
            browser.close()
            return tracking_data
            
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    test_waybill = "600704867288"
    print(f"\n🚀 Starting Safexpress Tracking Scraper")
    print(f"=====================================")
    result = scrape_tracking_info(test_waybill)
    if not result:
        sys.exit(1) 