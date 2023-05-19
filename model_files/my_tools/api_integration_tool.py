import requests
import argparse


def make_api_request(url, method='GET', headers=None, params=None, data=None):
    response = requests.request(method, url, headers=headers, params=params, data=data)
    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='API Integration Tool')
    parser.add_argument('-u', '--url', required=True, help='URL of the API endpoint')
    parser.add_argument('-m', '--method', default='GET', help='HTTP method (default: GET)')
    parser.add_argument('--headers', nargs='*', help='HTTP headers as key-value pairs')
    parser.add_argument('--params', nargs='*', help='HTTP query parameters as key-value pairs')
    parser.add_argument('--data', nargs='*', help='HTTP request body data as key-value pairs')

    args = parser.parse_args()

    headers = dict(pair.split('=') for pair in args.headers) if args.headers else None
    params = dict(pair.split('=') for pair in args.params) if args.params else None
    data = dict(pair.split('=') for pair in args.data) if args.data else None

    response = make_api_request(args.url, args.method, headers, params, data)
    print(response)
