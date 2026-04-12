from requests import get, post, delete, put

print(get('http://127.0.0.1:5000/api/products/2').json())