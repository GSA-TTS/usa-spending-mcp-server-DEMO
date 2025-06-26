import httpx


async def _make_request(method: str, url: str, **kwargs):
    """
    Make an asynchronous HTTP request using httpx.

    :param method: HTTP method (e.g., 'GET', 'POST').
    :param url: The URL to which the request is sent.
    :param kwargs: Additional keyword arguments to pass to the request.
    :return: The response object from the request.
    :raises httpx.HTTPStatusError: If the request returns an error status code.
    """
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url=url, **kwargs)
        response.raise_for_status()
        return response


async def async_http_get(url, **kwargs):
    """
    Make an asynchronous HTTP GET request.

    :param url: The URL to which the request is sent.
    :param kwargs: Additional keyword arguments to pass to the request.
    :return: The response object from the request.
    """
    return await _make_request("GET", url, **kwargs)


async def async_http_post(url, **kwargs):
    """
    Make an asynchronous HTTP POST request.

    :param url: The URL to which the request is sent.
    :param kwargs: Additional keyword arguments to pass to the request.
    :return: The response object from the request.
    """
    return await _make_request("POST", url, **kwargs)
