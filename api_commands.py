import requests


def send_api_request(url, method='GET', headers=None, params=None, data=None):
    print(
        f'COMMANDS: send_api_request - url={url}, method={method}, headers={headers}, params={params}, data={data}')
    response = requests.request(
        method, url, headers=headers, params=params, data=data)
    return response.json()
