import pytest
from unittest.mock import patch
from easy_eula_webapp.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_get(client):
    """Test the GET request for the index page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Easy EULA' in response.data
    assert b'Analyze Policy' in response.data

@patch('easy_eula_webapp.app.analyze_eulas')
def test_index_post_success(mock_analyze, client):
    """Test successful POST request."""
    # Mock the response from the LLM orchestrator
    mock_analyze.return_value = {
        'success': True,
        'summary': 'Test Summary',
        'impact': 'Test Impact',
        'tinfoil': 'Test Tinfoil'
    }
    
    response = client.post('/', data={'url': 'https://example.com/terms'})
    
    assert response.status_code == 200
    assert b'Test Summary' in response.data
    assert b'Test Impact' in response.data
    assert b'Test Tinfoil' in response.data
    mock_analyze.assert_called_once_with(['https://example.com/terms'])

@patch('easy_eula_webapp.app.analyze_eulas')
def test_index_post_failure(mock_analyze, client):
    """Test failed POST request."""
    mock_analyze.return_value = {
        'success': False,
        'error': 'Failed to fetch url'
    }
    
    response = client.post('/', data={'url': 'https://example.com/invalid'})
    
    assert response.status_code == 200
    # Flask flashed error messages should appear
    assert b'Failed to fetch url' in response.data

@patch('easy_eula_webapp.app.analyze_email')
def test_index_post_email_success(mock_analyze, client):
    """Test successful POST request using email text."""
    mock_analyze.return_value = {
        'success': True,
        'summary': 'Email Test Summary',
        'impact': 'Email Test Impact',
        'tinfoil': 'Email Test Tinfoil',
        'extracted_urls': ['https://example.com/new-terms']
    }
    
    response = client.post('/', data={'email_text': 'We updated our terms: https://example.com/new-terms'})
    
    assert response.status_code == 200
    assert b'Email Test Summary' in response.data
    assert b'Email Test Impact' in response.data
    assert b'Email Test Tinfoil' in response.data
    mock_analyze.assert_called_once_with('We updated our terms: https://example.com/new-terms')

def test_index_post_no_url(client):
    """Test POST request without URL or email."""
    response = client.post('/', data={})
    
    assert response.status_code == 200
    assert b'Please enter a URL or paste an email.' in response.data
