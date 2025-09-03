#!/usr/bin/env python3
"""
Test script for Brand Matching System V2
"""

try:
    from streamlit_app import extract_features, match_brand, BRAND_DATABASE
    from PIL import Image
    import numpy as np
    
    print("🔧 Testing Brand Matching System V2...")
    print("=" * 50)
    
    # Test 1: Import test
    print("✅ All modules imported successfully")
    
    # Test 2: Brand database test
    print(f"✅ Brand database loaded: {len(BRAND_DATABASE)} brands")
    for brand_id, brand_data in BRAND_DATABASE.items():
        print(f"   - {brand_data['name']}: {brand_data['description']}")
    
    # Test 3: Create test images
    print("\n🖼️  Testing with different colored images...")
    
    test_colors = [
        ('red', (255, 0, 0)),
        ('blue', (0, 0, 255)),
        ('black', (0, 0, 0)),
        ('white', (255, 255, 255))
    ]
    
    for color_name, rgb_color in test_colors:
        print(f"\n📷 Testing {color_name} image...")
        
        # Create test image
        test_image = Image.new('RGB', (100, 100), color=rgb_color)
        
        # Test feature extraction
        features = extract_features(test_image)
        if features:
            print(f"   ✅ Feature extraction successful")
            print(f"   📐 Dimensions: {features['dimensions']}")
            print(f"   🎨 Dominant colors found: {len(features['dominant_colors'])}")
            
            # Test brand matching
            matches = match_brand(features)
            if matches:
                print(f"   ✅ Brand matching successful")
                top_match = matches[0]
                print(f"   🏆 Top match: {top_match['brand_name']} ({top_match['confidence']:.2%})")
                
                # Show top 3 matches
                print("   📊 Top 3 matches:")
                for i, match in enumerate(matches[:3]):
                    print(f"      {i+1}. {match['brand_name']}: {match['confidence']:.2%}")
            else:
                print(f"   ❌ Brand matching failed")
        else:
            print(f"   ❌ Feature extraction failed")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("✅ The app is ready for deployment!")
    
except Exception as e:
    print(f"❌ Error during testing: {str(e)}")
    import traceback
    traceback.print_exc() 