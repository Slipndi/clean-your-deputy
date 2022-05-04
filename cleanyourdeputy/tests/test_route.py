from tests.conftest import client


def test_should_get_status_code_ok_on_index(client) : 
    response = client.get('/')
    assert response.status_code == 200
    
def test_should_get_status_code_ok_on_deputy_select(client) : 
    response = client.get('/deputy?select_field=cedric-roussel')
    assert response.status_code == 200
    
def test_should_get_status_code_ok_on_party_select(client) : 
    response = client.get('/party?select_field=EDS')
    assert response.status_code == 200
    

