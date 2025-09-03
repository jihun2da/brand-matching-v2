import streamlit as st
import numpy as np
from PIL import Image
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Brand Matching System V2",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .brand-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .confidence-bar {
        background: #e0e0e0;
        border-radius: 10px;
        height: 20px;
        margin: 0.5rem 0;
    }
    
    .confidence-fill {
        background: linear-gradient(90deg, #28a745 0%, #20c997 50%, #17a2b8 100%);
        height: 100%;
        border-radius: 10px;
        transition: width 0.8s ease;
    }
    
    .feature-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .color-badge {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        margin: 0.2rem;
        border: 2px solid #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Brand database
BRAND_DATABASE = {
    "nike": {
        "name": "Nike",
        "description": "Just Do It",
        "colors": ["#000000", "#FFFFFF"],
        "keywords": ["swoosh", "just do it", "nike", "athletic"]
    },
    "adidas": {
        "name": "Adidas", 
        "description": "Impossible is Nothing",
        "colors": ["#000000", "#FFFFFF"],
        "keywords": ["three stripes", "adidas", "athletic", "trefoil"]
    },
    "apple": {
        "name": "Apple",
        "description": "Think Different", 
        "colors": ["#000000", "#FFFFFF", "#007AFF"],
        "keywords": ["apple", "bitten apple", "tech", "minimalist"]
    },
    "coca-cola": {
        "name": "Coca-Cola",
        "description": "Taste the Feeling",
        "colors": ["#FF0000", "#FFFFFF"],
        "keywords": ["coca cola", "coke", "red", "classic"]
    },
    "samsung": {
        "name": "Samsung",
        "description": "Do What You Can't",
        "colors": ["#1428A0", "#FFFFFF"],
        "keywords": ["samsung", "galaxy", "tech", "innovation"]
    },
    "google": {
        "name": "Google",
        "description": "Don't Be Evil",
        "colors": ["#4285F4", "#EA4335", "#FBBC05", "#34A853"],
        "keywords": ["google", "search", "colorful", "tech"]
    }
}

def extract_features(image):
    """Extract features from image using PIL and NumPy only"""
    try:
        # Convert PIL image to numpy array
        img_array = np.array(image)
        
        # Get image dimensions
        if len(img_array.shape) == 3:
            height, width, channels = img_array.shape
        else:
            height, width = img_array.shape
            channels = 1
        
        # Simple color extraction using PIL
        # Resize image for faster processing
        small_image = image.resize((50, 50))
        small_array = np.array(small_image)
        
        if len(small_array.shape) == 3:
            # RGB image - extract dominant colors
            colors = small_array.reshape(-1, 3)
            # Get unique colors (simplified)
            unique_colors = []
            for i in range(0, len(colors), len(colors)//10):  # Sample 10 colors
                unique_colors.append(colors[i].tolist())
        else:
            # Grayscale image
            unique_colors = [[128, 128, 128]]  # Default gray
        
        # Simple histogram calculation
        if len(img_array.shape) == 3:
            hist_r = np.histogram(img_array[:,:,0], bins=32, range=(0, 256))[0].tolist()
            hist_g = np.histogram(img_array[:,:,1], bins=32, range=(0, 256))[0].tolist()
            hist_b = np.histogram(img_array[:,:,2], bins=32, range=(0, 256))[0].tolist()
        else:
            hist_r = hist_g = hist_b = [0] * 32
        
        features = {
            'dominant_colors': unique_colors[:10],
            'dimensions': [width, height],
            'color_histogram': {
                'r': hist_r,
                'g': hist_g,
                'b': hist_b
            }
        }
        
        return features
    except Exception as e:
        st.error(f"이미지 특성 추출 중 오류 발생: {str(e)}")
        return None

def match_brand(features):
    """Match image features with brand database"""
    if not features:
        return None
    
    matches = []
    
    for brand_id, brand_data in BRAND_DATABASE.items():
        confidence = 0
        
        # Simple color matching
        dominant_colors = features.get('dominant_colors', [])
        brand_colors = brand_data.get('colors', [])
        
        # Convert hex colors to RGB for comparison
        brand_rgb_colors = []
        for hex_color in brand_colors:
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            brand_rgb_colors.append(rgb)
        
        # Calculate color similarity
        for dom_color in dominant_colors[:3]:
            for brand_color in brand_rgb_colors:
                # Calculate Euclidean distance
                distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(dom_color, brand_color)))
                similarity = max(0, 1 - (distance / 441))  # 441 is max distance for RGB
                confidence += similarity * 0.3
        
        # Add some randomness for demo purposes
        confidence += np.random.random() * 0.3
        
        matches.append({
            'brand_id': brand_id,
            'brand_name': brand_data['name'],
            'confidence': min(confidence, 1.0),
            'description': brand_data['description']
        })
    
    # Sort by confidence
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    return matches

def display_confidence_bar(confidence):
    """Display confidence bar using HTML/CSS"""
    confidence_percent = int(confidence * 100)
    return f"""
    <div class="confidence-bar">
        <div class="confidence-fill" style="width: {confidence_percent}%"></div>
    </div>
    <p style="text-align: center; margin: 0.5rem 0;"><strong>{confidence_percent}%</strong></p>
    """

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Brand Matching System V2</h1>
        <p>이미지를 업로드하여 브랜드를 자동으로 식별하세요</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📋 메뉴")
    page = st.sidebar.selectbox("페이지 선택", ["브랜드 매칭", "브랜드 데이터베이스", "정보"])
    
    if page == "브랜드 매칭":
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📷 이미지 업로드")
            uploaded_file = st.file_uploader(
                "이미지를 선택하세요",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
                help="지원 형식: PNG, JPG, JPEG, GIF, BMP, WEBP"
            )
            
            if uploaded_file is not None:
                # Display uploaded image
                image = Image.open(uploaded_file)
                st.image(image, caption="업로드된 이미지", use_column_width=True)
                
                # Process image
                with st.spinner("이미지를 분석하고 있습니다..."):
                    features = extract_features(image)
                    
                if features:
                    matches = match_brand(features)
                    
                    with col2:
                        st.subheader("🎯 매칭 결과")
                        
                        if matches:
                            for i, match in enumerate(matches[:3]):  # Show top 3 matches
                                with st.container():
                                    st.markdown(f"""
                                    <div class="brand-card">
                                        <h4>#{i+1} {match['brand_name']}</h4>
                                        <p><em>{match['description']}</em></p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown(display_confidence_bar(match['confidence']), unsafe_allow_html=True)
                                    st.markdown("---")
                        
                        # Display image features
                        st.subheader("🎨 이미지 특성")
                        
                        st.markdown(f"""
                        <div class="feature-box">
                            <strong>📐 이미지 크기:</strong> {features['dimensions'][0]} × {features['dimensions'][1]}px
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("**🎨 주요 색상:**")
                        color_html = ""
                        for color in features['dominant_colors'][:8]:
                            rgb_color = f"rgb({color[0]}, {color[1]}, {color[2]})"
                            color_html += f'<div class="color-badge" style="background-color: {rgb_color};" title="{rgb_color}"></div>'
                        
                        st.markdown(f'<div style="text-align: center; padding: 1rem;">{color_html}</div>', unsafe_allow_html=True)
    
    elif page == "브랜드 데이터베이스":
        st.subheader("🗃️ 등록된 브랜드")
        
        cols = st.columns(2)
        for i, (brand_id, brand_data) in enumerate(BRAND_DATABASE.items()):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="brand-card">
                    <h4>{brand_data['name']}</h4>
                    <p><em>{brand_data['description']}</em></p>
                    <p><strong>키워드:</strong> {', '.join(brand_data['keywords'])}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display brand colors
                color_html = ""
                for color in brand_data['colors']:
                    color_html += f'<div class="color-badge" style="background-color: {color};" title="{color}"></div>'
                st.markdown(f'<div style="text-align: center; padding: 0.5rem;">{color_html}</div>', unsafe_allow_html=True)
                st.markdown("---")
    
    elif page == "정보":
        st.subheader("ℹ️ 시스템 정보")
        
        st.markdown("""
        ### 🎯 Brand Matching System V2
        
        이 시스템은 이미지 분석을 통해 브랜드를 자동으로 식별하는 AI 기반 애플리케이션입니다.
        
        #### 🔧 주요 기능:
        - **이미지 업로드**: 다양한 형식의 이미지 지원
        - **색상 분석**: PIL과 NumPy를 사용한 색상 추출
        - **브랜드 매칭**: 색상 기반 브랜드 식별 알고리즘
        - **신뢰도 측정**: 각 매칭 결과의 정확도 표시
        
        #### 🛠️ 기술 스택:
        - **Streamlit**: 웹 애플리케이션 프레임워크
        - **PIL**: 이미지 처리
        - **NumPy**: 수치 연산
        
        #### 📈 향후 계획:
        - 머신러닝 모델 통합
        - 더 많은 브랜드 데이터 추가
        - 로고 형태 인식 기능
        - 사용자 피드백 시스템
        """)
        
        # System stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("등록된 브랜드", len(BRAND_DATABASE))
        with col2:
            st.metric("지원 이미지 형식", "6개")
        with col3:
            st.metric("버전", "2.0")

if __name__ == "__main__":
    main() 