import io
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app

def run_checks():
    client = TestClient(app)

    # 1. Test /api/health
    res_h = client.get('/api/health')
    print('HEALTH STATUS:', res_h.status_code, res_h.json())
    assert res_h.status_code == 200
    assert res_h.json()['status'] == 'healthy'

    # 2. Test /api/health/ai
    res_ai = client.get('/api/health/ai')
    print('AI HEALTH:', res_ai.status_code, res_ai.json())
    assert res_ai.status_code == 200
    assert 'local_cv' in res_ai.json()
    assert 'gemini' in res_ai.json()

    # 3. Simulate exact screenshot upload
    img = Image.new('RGB', (800, 600), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    files = {
        'file': ('Gemini_Generated_Image_8372619472.png', buf, 'image/png')
    }
    data = {
        'credential_type': 'AUTO_DETECT',
        'notes': ''
    }

    res_s = client.post('/api/screen', files=files, data=data)
    print('SCREEN STATUS CODE:', res_s.status_code)
    print('RAW RESPONSE:', res_s.json())
    res_json = res_s.json()
    print('SUCCESS:', res_json.get('success'))
    print('STATUS:', res_json.get('status'))
    print('DOCUMENT:', res_json.get('document'))
    print('IDENTITY STATUS:', res_json.get('identity', {}).get('status'))
    print('RISK:', res_json.get('risk', {}).get('overall_score'), res_json.get('risk', {}).get('risk_level'))
    print('PIPELINE STAGES:', [p['stage'] + ':' + p['status'] for p in res_json.get('pipeline', [])])

    assert res_s.status_code == 200
    assert res_json.get('success') is True
    assert res_json.get('status') == 'COMPLETED'
    assert res_json.get('identity', {}).get('status') == 'NOT_PROVIDED'

    # Test with primary_document key
    buf.seek(0)
    files2 = {'primary_document': ('Gemini_Generated_Image_test2.png', buf, 'image/png')}
    res_s2 = client.post('/api/screen', files=files2, data=data)
    assert res_s2.status_code == 200
    assert res_s2.json().get('success') is True

    print('ALL VERIFICATIONS PASSED SUCCESSFULLY!')

if __name__ == '__main__':
    run_checks()
