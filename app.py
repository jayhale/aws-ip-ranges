from datetime import datetime

import requests
from werkzeug.wrappers import Request, Response

IP_RANGES_URL = 'https://ip-ranges.amazonaws.com/ip-ranges.json'

ERROR_RESPONSE = '''
<html>
    <head>
        <title>AWS IP Ranges | An error occured</title>
    </head>
    <body>
        <h1>A remote error occured</h1>
        <p>{error}</p>
    </body>
</html>
'''

SUCCESS_RESPONSE = '''
<html>
    <head>

    </head>
    <body>
        <h1>AWS IP Ranges as of {create_date}</h1>
        <h2>Metadata</h2>
        <p>
            <strong>Sync token:</strong> {sync_token}
        </p>
        <h2>IPv4 Prefixes</h2>
        <table>
            <thead>
                <tr>
                    <th>CIDR</th>
                    <th>Region</th>
                    <th>Service</th>
                </tr>
            </thead>
            <tbody>
                {ipv4_range_rows}
            </tbody>
        </table>
        <h2>IPv6 Prefixes</h2>
        <table>
            <thead>
                <tr>
                    <th>CIDR</th>
                    <th>Region</th>
                    <th>Service</th>
                </tr>
            </thead>
            <tbody>
                {ipv6_range_rows}
            </tbody>
        </table>
    </body>
</html>
'''


@Request.application
def application(request):

    # Get the current AWS IP ranges JSON file
    aws_res = requests.get(IP_RANGES_URL)
    if not aws_res.status_code == 200:
        return Response(
            ERROR_RESPONSE.format(error=(f'AWS returned {aws_res.status_code} '
                                         'when attempting to fetch '
                                         'ip-ranges.json')),
            content_type='text/html'
        )
    data = aws_res.json()
    sync_token = data['syncToken']
    create_date = datetime.utcfromtimestamp(int(sync_token))
    ipv4_ranges = data['prefixes']
    ipv6_ranges = data['ipv6_prefixes']

    # Check if the user wants to filter to a specific region
    region = request.path.replace('/', '')
    if region:
        ipv4_ranges = [r for r in ipv4_ranges if r['region'] == region]
        ipv6_ranges = [r for r in ipv6_ranges if r['region'] == region]

    ipv4_range_rows = ''
    for r in ipv4_ranges:
        ipv4_range_rows += f'''
            <tr>
                <td>{r['ip_prefix']}</td>
                <td><a href="/{r['region']}">{r['region']}</a></td>
                <td>{r['service']}</td>
            </tr>
        '''

    ipv6_range_rows = ''
    for r in ipv6_ranges:
        ipv6_range_rows += f'''
            <tr>
                <td>{r['ipv6_prefix']}</td>
                <td><a href="/{r['region']}">{r['region']}</a></td>
                <td>{r['service']}</td>
            </tr>
        '''

    return Response(
        SUCCESS_RESPONSE.format(create_date=create_date, sync_token=sync_token,
            ipv4_range_rows=ipv4_range_rows, ipv6_range_rows=ipv6_range_rows),
        content_type='text/html'
    )


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("localhost", 5000, application)
