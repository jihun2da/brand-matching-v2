#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브랜드 매칭 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import pandas as pd
import logging
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# 로컬 모듈 import
from brand_matching_system import BrandMatchingSystem
from file_processor import BrandFileProcessor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('brand_matching.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Flask 앱 생성
app = Flask(__name__)
app.secret_key = 'brand_matching_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 제한

# 전역 인스턴스
matching_system = BrandMatchingSystem()
file_processor = BrandFileProcessor()

# 허용된 파일 확장자
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    """파일 확장자 검증"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('brand_matching_index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """파일 업로드 API"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'})
        
        files = request.files.getlist('files[]')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                try:
                    # 안전한 파일명 생성
                    original_filename = secure_filename(file.filename)
                    file_path = file_processor.save_uploaded_file(file, original_filename)
                    uploaded_files.append({
                        'filename': original_filename,
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    })
                    
                except Exception as e:
                    logger.error(f"파일 업로드 실패 ({file.filename}): {e}")
                    return jsonify({
                        'success': False, 
                        'message': f'파일 업로드 실패: {file.filename}'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': f'지원되지 않는 파일 형식: {file.filename}'
                })
        
        if uploaded_files:
            return jsonify({
                'success': True,
                'message': f'{len(uploaded_files)}개 파일 업로드 완료',
                'files': uploaded_files
            })
        else:
            return jsonify({'success': False, 'message': '업로드된 파일이 없습니다.'})
            
    except Exception as e:
        logger.error(f"파일 업로드 API 오류: {e}")
        return jsonify({'success': False, 'message': f'업로드 중 오류 발생: {str(e)}'})

@app.route('/api/process', methods=['POST'])
def process_matching():
    """브랜드 매칭 처리 API"""
    try:
        logger.info("브랜드 매칭 처리 시작")
        
        # 업로드된 파일 목록 가져오기
        uploaded_files = file_processor.get_uploaded_files()
        
        if not uploaded_files:
            return jsonify({'success': False, 'message': '처리할 파일이 없습니다.'})
        
        # 파일들을 하나로 합치기 (Sheet1 형식)
        file_paths = [f['path'] for f in uploaded_files]
        combined_df = file_processor.combine_excel_files(file_paths)
        
        if combined_df.empty:
            return jsonify({'success': False, 'message': '읽을 수 있는 데이터가 없습니다.'})
        
        logger.info(f"통합된 데이터: {len(combined_df)}행")
        
        # Sheet1 -> Sheet2 변환
        sheet2_df = matching_system.convert_sheet1_to_sheet2(combined_df)
        
        # 브랜드 매칭 수행
        matched_df = matching_system.process_matching(sheet2_df)
        
        # 결과 파일 저장
        result_file = file_processor.save_result_file(matched_df)
        
        # 매칭 통계 계산
        total_rows = len(matched_df)
        matched_rows = len(matched_df[matched_df['N열(중도매명)'] != ''])
        success_rate = (matched_rows / total_rows * 100) if total_rows > 0 else 0
        
        logger.info(f"브랜드 매칭 완료: {matched_rows}/{total_rows} ({success_rate:.1f}%)")
        
        return jsonify({
            'success': True,
            'message': '브랜드 매칭 처리 완료',
            'stats': {
                'total_rows': total_rows,
                'matched_rows': matched_rows,
                'success_rate': round(success_rate, 1),
                'result_file': os.path.basename(result_file)
            }
        })
        
    except Exception as e:
        logger.error(f"브랜드 매칭 처리 오류: {e}")
        return jsonify({'success': False, 'message': f'처리 중 오류 발생: {str(e)}'})

@app.route('/api/files', methods=['GET'])
def get_files():
    """업로드된 파일 목록 API"""
    try:
        files = file_processor.get_uploaded_files()
        stats = file_processor.get_file_stats()
        
        return jsonify({
            'success': True,
            'files': files,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"파일 목록 조회 오류: {e}")
        return jsonify({'success': False, 'message': f'파일 목록 조회 실패: {str(e)}'})

@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    """파일 삭제 API"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': '파일명이 지정되지 않았습니다.'})
        
        success = file_processor.delete_uploaded_file(filename)
        
        if success:
            return jsonify({'success': True, 'message': f'파일 삭제 완료: {filename}'})
        else:
            return jsonify({'success': False, 'message': f'파일 삭제 실패: {filename}'})
            
    except Exception as e:
        logger.error(f"파일 삭제 오류: {e}")
        return jsonify({'success': False, 'message': f'파일 삭제 중 오류 발생: {str(e)}'})

@app.route('/api/clear-files', methods=['POST'])
def clear_files():
    """모든 파일 삭제 API"""
    try:
        success = file_processor.clear_uploaded_files()
        
        if success:
            return jsonify({'success': True, 'message': '모든 파일 삭제 완료'})
        else:
            return jsonify({'success': False, 'message': '파일 삭제 실패'})
            
    except Exception as e:
        logger.error(f"파일 전체 삭제 오류: {e}")
        return jsonify({'success': False, 'message': f'파일 삭제 중 오류 발생: {str(e)}'})

@app.route('/api/download/<filename>')
def download_file(filename):
    """파일 다운로드 API"""
    try:
        file_path = os.path.join(file_processor.results_dir, filename)
        
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({'success': False, 'message': '파일을 찾을 수 없습니다.'})
            
    except Exception as e:
        logger.error(f"파일 다운로드 오류: {e}")
        return jsonify({'success': False, 'message': f'다운로드 중 오류 발생: {str(e)}'})

@app.route('/api/reload-brand-data', methods=['POST'])
def reload_brand_data():
    """브랜드 데이터 새로고침 API"""
    try:
        matching_system.load_brand_data()
        
        brand_count = len(matching_system.brand_data) if matching_system.brand_data is not None else 0
        
        return jsonify({
            'success': True,
            'message': f'브랜드 데이터 새로고침 완료 ({brand_count}개 상품)'
        })
        
    except Exception as e:
        logger.error(f"브랜드 데이터 새로고침 오류: {e}")
        return jsonify({'success': False, 'message': f'새로고침 중 오류 발생: {str(e)}'})

@app.errorhandler(413)
def too_large(e):
    """파일 크기 초과 오류 처리"""
    return jsonify({'success': False, 'message': '파일 크기가 너무 큽니다. (최대 100MB)'}), 413

@app.errorhandler(Exception)
def handle_exception(e):
    """전역 예외 처리"""
    logger.error(f"예상치 못한 오류: {e}")
    return jsonify({'success': False, 'message': '서버 내부 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    logger.info("브랜드 매칭 웹 애플리케이션 시작")
    app.run(host='0.0.0.0', port=5002, debug=True) 